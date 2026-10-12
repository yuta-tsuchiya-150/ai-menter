#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初心者マニュアル 自動巡回・整合性監査システム (audit_manual_integrity.py)

機能:
1. マニュアル内の外部リンク（YouTube動画、各社サービスURL）の死活・削除・非公開チェック
2. 外部サービス（Render, Google AI Studio, GitHub等）の最新公式情報とマニュアルのセマンティック比較（Gemini AI活用）
3. ズレやリンク切れを検知した場合、修正案付きで管理者宛て (t1738315@gmail.com) にメール通知
"""

import os
import sys
import re
import json
import smtplib
import ssl
import argparse
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from html.parser import HTMLParser
import requests

# ==========================================
# .env 自動読み込みヘルパー
# ==========================================
def load_dotenv_custom():
    """カレントまたは親ディレクトリの .env ファイルを読み込む"""
    candidates = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"),
        "/root/ojuken_project/Data_search_engine/.env",
        "/root/fx_support_app/.env"
    ]
    for env_path in candidates:
        if os.path.exists(env_path):
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            k, v = k.strip(), v.strip().strip('"').strip("'")
                            if k not in os.environ:
                                os.environ[k] = v
                break
            except Exception:
                pass

load_dotenv_custom()

# ==========================================
# 設定情報
# ==========================================
CONFIG = {
    # Gemini API
    "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY", ""),
    "GEMINI_MODELS": ["gemini-flash-lite-latest", "gemini-3.8-flash", "gemini-flash-latest"],
    
    # SMTP メール設定 (ConoHa WING)
    "SMTP_HOST": os.getenv("SMTP_HOST", "mail1061.conoha.ne.jp"),
    "SMTP_PORT": int(os.getenv("SMTP_PORT", 465)),
    "SMTP_USER": os.getenv("SMTP_USER", ""),
    "SMTP_PASSWORD": os.getenv("SMTP_PASSWORD", ""),
    "ADMIN_EMAIL": os.getenv("ADMIN_EMAIL", "t1738315@gmail.com"),
    "FROM_NAME": "AI教材品質監査システム",
    
    # 公式サービス巡回URL
    "OFFICIAL_SOURCES": {
        "Render": {
            "name": "Render (ホスティング)",
            "urls": [
                "https://render.com/docs/blueprint-spec",
                "https://render.com/pricing"
            ],
            "related_manuals": ["prep-render.php", "step3-render.php"]
        },
        "Google AI Studio": {
            "name": "Google AI Studio / Gemini API",
            "urls": [
                "https://ai.google.dev/gemini-api/docs/api-key",
                "https://ai.google.dev/pricing"
            ],
            "related_manuals": ["prep-gemini.php"]
        },
        "GitHub": {
            "name": "GitHub",
            "urls": [
                "https://docs.github.com/en/get-started/onboarding/getting-started-with-your-github-account"
            ],
            "related_manuals": ["prep-github.php", "step2-github.php"]
        }
    }
}


# ==========================================
# HTML / テキスト解析ユーティリティ
# ==========================================
class SimpleHTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text_parts = []
        self.links = []
        self.in_script_or_style = False

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            self.in_script_or_style = True
        if tag == 'a':
            for name, value in attrs:
                if name == 'href' and value.startswith('http'):
                    self.links.append(value)

    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self.in_script_or_style = False

    def handle_data(self, data):
        if not self.in_script_or_style:
            stripped = data.strip()
            if stripped:
                self.text_parts.append(stripped)

    def get_text(self):
        return "\n".join(self.text_parts)


def parse_html_file(file_path):
    """HTML/PHPファイルからテキストとリンクを抽出"""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        parser = SimpleHTMLTextExtractor()
        parser.feed(content)
        return parser.get_text(), list(set(parser.links))
    except Exception as e:
        print(f"Error parsing file {file_path}: {e}")
        return "", []


def fetch_url_text(url, timeout=10):
    """外部URLのテキストを取得"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        r = requests.get(url, headers=headers, timeout=timeout)
        if r.status_code == 200:
            parser = SimpleHTMLTextExtractor()
            parser.feed(r.text)
            text = parser.get_text()
            # 5000文字以内に丸める
            return text[:5000]
        else:
            return f"HTTP {r.status_code} Error"
    except Exception as e:
        return f"Fetch error: {e}"


# ==========================================
# 監査チェック 1: リンク・YouTube死活確認
# ==========================================
def check_links(manuals_dir):
    """マニュアル内のすべての外部リンクの死活・動画公開状況を検証"""
    results = []
    
    manual_files = [f for f in os.listdir(manuals_dir) if f.endswith(('.php', '.html')) and ('prep-' in f or 'step' in f)]
    all_links = {}

    for mf in manual_files:
        full_path = os.path.join(manuals_dir, mf)
        _, links = parse_html_file(full_path)
        for link in links:
            if link not in all_links:
                all_links[link] = []
            all_links[link].append(mf)

    print(f"[*] 検出された外部リンク総数: {len(all_links)}件")

    for url, file_list in all_links.items():
        # YouTubeリンクの場合: oEmbed API で削除・非公開チェック
        if "youtube.com/watch" in url or "youtu.be/" in url:
            oembed_url = f"https://www.youtube.com/oembed?url={url}&format=json"
            try:
                r = requests.get(oembed_url, timeout=8)
                if r.status_code == 200:
                    data = r.json()
                    title = data.get("title", "")
                    print(f"  [YouTube OK] {title} ({url})")
                elif r.status_code in (404, 401, 403):
                    results.append({
                        "type": "YouTube動画アクセス不能",
                        "target_files": file_list,
                        "url": url,
                        "status": f"HTTP {r.status_code} (削除または非公開の可能性)",
                        "suggestion": f"該当のYouTube動画（{url}）が非公開または削除されています。別の解説動画または最新URLへの差し替えが必要です。"
                    })
                    print(f"  [YouTube ERROR] {r.status_code} on {url}")
            except Exception as e:
                print(f"  [YouTube Warn] {e} on {url}")

        # 一般URLの死活確認
        else:
            try:
                headers = {"User-Agent": "Mozilla/5.0"}
                r = requests.get(url, headers=headers, timeout=8, allow_redirects=True)
                if r.status_code >= 400 and r.status_code not in (403, 401):  # 403/401はBot対策の場合があるため除外
                    results.append({
                        "type": "リンク切れエラー",
                        "target_files": file_list,
                        "url": url,
                        "status": f"HTTP {r.status_code}",
                        "suggestion": f"リンク先（{url}）がエラーを返しています。リンク先URLの最新化または確認を行ってください。"
                    })
                    print(f"  [Link ERROR] HTTP {r.status_code}: {url}")
                else:
                    print(f"  [Link OK] HTTP {r.status_code}: {url}")
            except Exception as e:
                print(f"  [Link Check Warn] {url}: {e}")

    return results


# ==========================================
# 監査チェック 2: AIによるマニュアルと公式情報の整合性比較
# ==========================================
def call_gemini(prompt):
    """Gemini API を呼び出して分析結果を取得"""
    api_key = CONFIG["GEMINI_API_KEY"]
    if not api_key:
        print("  [Warn] GEMINI_API_KEY が未設定です。")
        return None

    for model in CONFIG["GEMINI_MODELS"]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2}
        }
        try:
            r = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=30)
            if r.status_code == 200:
                data = r.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return text
            elif r.status_code == 429:
                print(f"  [Gemini Rate Limit] {model} -> trying next model...")
                continue
            else:
                print(f"  [Gemini API Error] {model} status {r.status_code}: {r.text[:100]}")
        except Exception as e:
            print(f"  [Gemini API Exception] {model}: {e}")
    return None


def check_semantic_differences(manuals_dir):
    """マニュアルと外部公式ドキュメントをGeminiで比較"""
    differences = []

    for service_key, s_info in CONFIG["OFFICIAL_SOURCES"].items():
        print(f"[*] 公式サイト照合中: {s_info['name']}")
        
        # 1. 公式ドキュメントのテキスト取得
        official_text_corpus = ""
        for u in s_info["urls"]:
            txt = fetch_url_text(u)
            official_text_corpus += f"\n--- Source: {u} ---\n{txt}\n"

        if len(official_text_corpus.strip()) < 50:
            print(f"  [Skip] 公式情報の取得に失敗または情報量が僅少です: {s_info['name']}")
            continue

        # 2. 該当マニュアルのテキスト取得
        manual_corpus = ""
        for mf in s_info["related_manuals"]:
            fpath = os.path.join(manuals_dir, mf)
            if os.path.exists(fpath):
                txt, _ = parse_html_file(fpath)
                manual_corpus += f"\n=== マニュアルファイル: {mf} ===\n{txt[:4000]}\n"

        if not manual_corpus.strip():
            continue

        # 3. Geminiによる突き合わせ分析
        prompt = f"""
あなたは初心者向けIT教材・学習マニュアルの品質管理者です。
受講者（50代・非エンジニア）が迷わず手順を完了できるよう、マニュアルの記載内容と最新の外部公式サイトの情報を照合してください。

【対象サービス】: {s_info['name']}

【初心者マニュアルの内容】:
{manual_corpus[:6000]}

【公式サイトの最新テキスト・ドキュメント】:
{official_text_corpus[:6000]}

【判定ルール】:
1. 些細な言い回しやデザインの微差は無視してください。
2. 初心者が操作不能になる、あるいは誤解するような重大な「ズレ・乖離」を検出してください。
   例:
   - ボタン名やメニュー名、URLの廃止・変更
   - 無料プランの廃止・大幅な制限変更（有料化、クレジット制など）
   - 新規登録フローや認証方式の前提条件変更
3. ズレを発見した場合は、必ず以下のJSON配列形式のみで出力してください。
4. 重大なズレが見当たらない場合は、空の配列 `[]` のみを出力してください。

```json
[
  {{
    "target": "対象箇所やファイル名（例: step3-render.php）",
    "manual_text": "マニュアルでの現状の記述",
    "official_status": "最新の公式状況・変更点",
    "suggestion": "マニュアルの具体的な修正案・追記案"
  }}
]
```
"""

        response_text = call_gemini(prompt)
        if not response_text:
            continue

        # JSON部分の抽出
        json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
        if json_match:
            try:
                parsed = json.loads(json_match.group(0))
                for item in parsed:
                    item["service"] = s_info["name"]
                    differences.append(item)
                    print(f"  [AI検知] {item.get('target', '')}: {item.get('official_status', '')[:60]}...")
            except json.JSONDecodeError:
                print(f"  [JSON Parse Error] AI出力をJSONとして解釈できませんでした")
        else:
            print(f"  [AI判定] 重大な乖離なし (正常)")

    return differences


# ==========================================
# メール送信機能
# ==========================================
def send_notification_email(link_errors, semantic_diffs, is_test=False):
    """管理者宛てに監査結果メールを送信"""
    total_issues = len(link_errors) + len(semantic_diffs)
    now_str = datetime.now().strftime("%Y年%m月%d日 %H:%M")

    if is_test:
        subject = f"【動作確認】初心者マニュアル巡回・ズレ検知システムのテスト通知 ({now_str})"
    else:
        subject = f"【要確認】初心者マニュアルと公式サイトにズレを検知しました ({total_issues}件) - {now_str}"

    # 本文（テキスト版）
    text_lines = [
        f"自律型AI教材品質監査システムからの定期レポートです。",
        f"実行日時: {now_str}",
        f"検知されたズレ・問題: {total_issues} 件",
        "=" * 60,
    ]

    # HTML版
    html_parts = [
        f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #333; max-width: 700px; margin: 0 auto; padding: 20px;">
  <div style="background-color: #2563eb; color: white; padding: 16px 20px; border-radius: 8px 8px 0 0;">
    <h2 style="margin: 0; font-size: 1.25rem;">初心者マニュアル 自動巡回・整合性監査レポート</h2>
    <p style="margin: 4px 0 0; font-size: 0.9rem; opacity: 0.9;">実行日時: {now_str}</p>
  </div>
  <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-top: none; padding: 20px; border-radius: 0 0 8px 8px;">
"""
    ]

    if total_issues == 0 and is_test:
        text_lines.append("\n現在、マニュアルと外部サイトに重大なズレやリンク切れは検出されていません。正常に巡回監視中です。\n")
        html_parts.append("""
    <div style="background-color: #ecfdf5; border-left: 4px solid #10b981; padding: 12px 16px; margin-bottom: 20px; border-radius: 4px;">
      <strong style="color: #065f46;">✔ 監査結果：すべて正常です</strong>
      <p style="margin: 4px 0 0; font-size: 0.9rem; color: #047857;">外部リンクの死活・動画公開状況、および主要サービスの公式ドキュメントとの整合性を確認しました。重大なズレは検知されていません。</p>
    </div>
""")

    # 1. リンク切れ・動画非公開
    if link_errors:
        text_lines.append(f"\n■ リンク切れ・動画アクセス不能 ({len(link_errors)}件)")
        html_parts.append(f"""
    <h3 style="color: #dc2626; border-bottom: 2px solid #fee2e2; padding-bottom: 6px; margin-top: 20px;">
      🚨 リンク切れ・動画アクセス不能 ({len(link_errors)}件)
    </h3>
""")
        for item in link_errors:
            files_str = ", ".join(item.get("target_files", []))
            text_lines.extend([
                f"- 種別: {item.get('type')}",
                f"  対象ファイル: {files_str}",
                f"  URL: {item.get('url')}",
                f"  状態: {item.get('status')}",
                f"  修正案: {item.get('suggestion')}",
                ""
            ])
            html_parts.append(f"""
    <div style="background-color: white; border: 1px solid #fed7d7; border-radius: 6px; padding: 14px; margin-bottom: 12px;">
      <div style="font-weight: bold; color: #991b1b; font-size: 0.95rem;">【{item.get('type')}】</div>
      <div style="font-size: 0.85rem; color: #64748b; margin-top: 4px;">対象マニュアル: <code>{files_str}</code></div>
      <div style="font-size: 0.85rem; color: #2563eb; word-break: break-all; margin-top: 2px;">URL: {item.get('url')}</div>
      <div style="font-size: 0.85rem; color: #b91c1c; margin-top: 2px;">ステータス: {item.get('status')}</div>
      <div style="background-color: #fef2f2; padding: 10px; border-radius: 4px; margin-top: 8px; font-size: 0.9rem;">
        <strong>💡 修正案:</strong> {item.get('suggestion')}
      </div>
    </div>
""")

    # 2. AIによるセマンティック差異・手順のズレ
    if semantic_diffs:
        text_lines.append(f"\n■ 公式サイトとマニュアルの手順・仕様のズレ ({len(semantic_diffs)}件)")
        html_parts.append(f"""
    <h3 style="color: #d97706; border-bottom: 2px solid #fef3c7; padding-bottom: 6px; margin-top: 24px;">
      ⚠️ 公式サイトとマニュアルの乖離・仕様変更 ({len(semantic_diffs)}件)
    </h3>
""")
        for item in semantic_diffs:
            text_lines.extend([
                f"- サービス: {item.get('service', '外部サービス')}",
                f"  対象: {item.get('target', '')}",
                f"  マニュアル現行記述: {item.get('manual_text', '')}",
                f"  最新の公式状況: {item.get('official_status', '')}",
                f"  修正案: {item.get('suggestion', '')}",
                ""
            ])
            html_parts.append(f"""
    <div style="background-color: white; border: 1px solid #fde68a; border-radius: 6px; padding: 14px; margin-bottom: 14px;">
      <div style="font-weight: bold; color: #b45309; font-size: 1rem;">
        【{item.get('service', '')}】 {item.get('target', '')}
      </div>
      <table style="width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 0.88rem;">
        <tr style="background-color: #f8fafc;">
          <th style="padding: 6px 10px; text-align: left; border: 1px solid #e2e8f0; width: 25%;">現行マニュアル</th>
          <td style="padding: 6px 10px; border: 1px solid #e2e8f0; color: #475569;">{item.get('manual_text', '')}</td>
        </tr>
        <tr style="background-color: #fffbeb;">
          <th style="padding: 6px 10px; text-align: left; border: 1px solid #e2e8f0;">最新の公式状況</th>
          <td style="padding: 6px 10px; border: 1px solid #e2e8f0; color: #92400e; font-weight: bold;">{item.get('official_status', '')}</td>
        </tr>
      </table>
      <div style="background-color: #eff6ff; border-left: 4px solid #3b82f6; padding: 10px 14px; border-radius: 4px; margin-top: 10px; font-size: 0.9rem;">
        <strong style="color: #1e40af;">💡 変更・追記案:</strong><br>
        <span style="color: #1e3a8a;">{item.get('suggestion', '')}</span>
      </div>
    </div>
""")

    text_lines.extend([
        "=" * 60,
        "※ 本メールは巡回システムによる検知通知です。マニュアルファイルの自動書き換えは行っていません。",
        "確認のうえ、必要に応じてマニュアルの修正を実施してください。"
    ])

    html_parts.append(f"""
    <div style="margin-top: 24px; padding-top: 16px; border-top: 1px solid #cbd5e1; font-size: 0.8rem; color: #64748b; text-align: center;">
      ※ 本通知は ConoHa VPS 自動巡回システムより自動送信されています。<br>
      自動書き換えは行っていませんので、ご確認のうえ手動での更新をご検討ください。
    </div>
  </div>
</body>
</html>
""")

    plain_content = "\n".join(text_lines)
    html_content = "".join(html_parts)

    # 送信処理
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = Header(subject, "utf-8")
        msg["From"] = f"{Header(CONFIG['FROM_NAME'], 'utf-8')} <{CONFIG['SMTP_USER']}>"
        msg["To"] = CONFIG["ADMIN_EMAIL"]

        msg.attach(MIMEText(plain_content, "plain", "utf-8"))
        msg.attach(MIMEText(html_content, "html", "utf-8"))

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(CONFIG["SMTP_HOST"], CONFIG["SMTP_PORT"], context=context, timeout=15) as server:
            server.login(CONFIG["SMTP_USER"], CONFIG["SMTP_PASSWORD"])
            server.sendmail(CONFIG["SMTP_USER"], [CONFIG["ADMIN_EMAIL"]], msg.as_string())

        print(f"[✔] メール送信成功 -> {CONFIG['ADMIN_EMAIL']}")
        return True
    except Exception as e:
        print(f"[✖] メール送信失敗: {e}")
        return False


# ==========================================
# メイン実行処理
# ==========================================
def run_audit(manuals_dir=None, is_test=False, force_report=False):
    print("=" * 60)
    print(f"初心者マニュアル 整合性監査巡回開始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    if not manuals_dir:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        manuals_dir = os.path.join(base_dir, "..", "manual")

    if not os.path.exists(manuals_dir):
        print(f"[Error] マニュアルディレクトリが見つかりません: {manuals_dir}")
        return

    # 1. リンク・YouTube死活確認
    print("\n--- [ステップ 1] 外部リンクおよび解説動画の死活チェック ---")
    link_errors = check_links(manuals_dir)

    # 2. AIによるセマンティック差異確認
    print("\n--- [ステップ 2] 公式ドキュメントとの整合性AIチェック ---")
    semantic_diffs = check_semantic_differences(manuals_dir)

    total_issues = len(link_errors) + len(semantic_diffs)
    print(f"\n--- 監査完了: 検出された問題・ズレ {total_issues} 件 ---")

    # 3. メール送信判定
    if total_issues > 0 or is_test or force_report:
        print("\n--- 管理者宛てに通知メールを送信中 ---")
        send_notification_email(link_errors, semantic_diffs, is_test=is_test)
    else:
        print("\n[OK] ズレやリンク切れは検出されませんでした。メール通知はスキップします。")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="初心者マニュアル整合性監査スクリプト")
    parser.add_argument("--manuals-dir", help="マニュアルファイルのディレクトリパス")
    parser.add_argument("--test", action="store_true", help="動作テスト用メールを送信")
    parser.add_argument("--force-report", action="store_true", help="ズレの有無にかかわらず日報メールを送信")
    args = parser.parse_args()

    run_audit(manuals_dir=args.manuals_dir, is_test=args.test, force_report=args.force_report)
