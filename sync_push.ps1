$status = git status --porcelain
if ($status) {
    Write-Host "変更を検出しました。コミットしてGitHubへプッシュします..." -ForegroundColor Cyan
    git add .
    $now = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    git commit -m "sync: PC切り替え同期 ($now)"
    git push origin main
    Write-Host "`n==========================================" -ForegroundColor Green
    Write-Host "  保存とプッシュが正常に完了しました！" -ForegroundColor Green
    Write-Host "==========================================" -ForegroundColor Green
} else {
    Write-Host "`n保存が必要な新しい変更はありませんでした。" -ForegroundColor Yellow
    Write-Host "リモートへプッシュ済みか確認します..."
    git push origin main
}
Start-Sleep -Seconds 2
