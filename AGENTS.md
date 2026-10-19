# Agent Instructions & Workflow Rules

## 1. Automatic GitHub Synchronization (必須)
プログラムやファイルの改修・追加・更新を行った際は、必ず該当するGitHubリポジトリに対してコミットおよびプッシュ（git add, git commit, git push）を実施し、常にリモートを最新状態に同期すること。

### 主な管理リポジトリ一覧
- **ai-starter-pack**: https://github.com/yuta-tsuchiya-150/ai-starter-pack.git
- **Data_search_engine**: https://github.com/yuta-tsuchiya-150/Data_search_engine.git
- **corporate_site**: https://github.com/yuta-tsuchiya-150/corporate_site.git
- **fx_support_app**: https://github.com/yuta-tsuchiya-150/fx_support_app.git
- **ai-menter**: https://github.com/yuta-tsuchiya-150/ai-menter.git

## 2. ConoHa WING / VPS デプロイ
- Webサイトやアプリの更新時は、SSHまたはデプロイスクリプト経由でConoHa WINGやConoHa VPS本番環境へ同期する。

## 3. 分析・ナレッジのMarkdown永続化 (knowledge/ フォルダ) (必須)
- 複数PC間でのシームレスな開発・情報共有のため、コード分析や調査結果、設計メモ、トラブルシューティング記録等は画面上に提示するだけでなく、必ず `knowledge/` フォルダ配下にMarkdownファイルとして保存・更新する。
- 保存したMarkdownファイルもルール1に従い、必ずGitHubリポジトリへコミット＆プッシュして同期を保つこと。
