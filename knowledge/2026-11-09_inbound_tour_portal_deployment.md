# インバウンド向けツアー資料ダウンロードポータル 構築・ConoHa WINGデプロイ実績レポート

**完了日時**: 2026-11-09  
**対象リポジトリ**: `ai-menter`  
**本番公開URL**:
- **ツアー一覧ポータル（基本サイト）**: [http://2026091711175w334chu.conohawing.com/tours/](http://2026091711175w334chu.conohawing.com/tours/)
- **渋谷基本ツアー 2Day（個別DLページ）**: [http://2026091711175w334chu.conohawing.com/tours/tours/shibuya-2day-ja.html](http://2026091711175w334chu.conohawing.com/tours/tours/shibuya-2day-ja.html)
- **PDF実体直接URL**: [http://2026091711175w334chu.conohawing.com/tours/assets/pdf/shibuya_basic_2day_ja.pdf](http://2026091711175w334chu.conohawing.com/tours/assets/pdf/shibuya_basic_2day_ja.pdf)

---

## 1. 接続環境情報
- **ConoHa WING ホスト**: `www1211.conoha.ne.jp`
- **SSHポート**: `8022`
- **ユーザー名**: `c6891274`
- **秘密鍵**: `~/.ssh/conoha_wing.pem`（バックアップ済み）
- **公開ディレクトリ**: `~/public_html/2026091711175w334chu.conohawing.com/tours/`

---

## 2. 実施内容・稼働確認
1. **ポータルサイト構築**:
   - `tours-portal/index.html`（一覧ポータル）
   - `tours-portal/tours/shibuya-2day-ja.html`（個別ダウンロードページ）
   - `tours-portal/assets/pdf/shibuya_basic_2day_ja.pdf`（実体PDF 9.5MB）
2. **ConoHa WINGへのSSH/SCP直接デプロイ**:
   - 新しい鍵 `key-2026-11-09-16-10.pem` のWindows権限を `icacls` で最適化
   - SCPによりサーバーの `~/public_html/2026091711175w334chu.conohawing.com/tours/` へ全ファイル転送
   - ディレクトリパーミッションを `755` に設定
3. **本番死活監視・動作検証**:
   - `http://127.0.0.1/tours/` -> HTTP 200 OK (nginx)
   - `http://127.0.0.1/tours/tours/shibuya-2day-ja.html` -> HTTP 200 OK (nginx)
   - `http://127.0.0.1/tours/assets/pdf/shibuya_basic_2day_ja.pdf` -> HTTP 200 OK (Content-Type: application/pdf)
   - すべて正常稼働を確認完了。

---

## 3. 次回以降のワンクリックデプロイ
`deploy_conoha.bat` をダブルクリックするだけで、AntigravityまたはターミナルからいつでもConoHa WINGへ最新状態が反映されます。
