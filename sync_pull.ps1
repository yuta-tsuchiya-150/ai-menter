Write-Host "GitHubから最新データを取得しています (git pull)..." -ForegroundColor Cyan
git pull origin main
Write-Host "`n==========================================" -ForegroundColor Green
Write-Host "  最新データの取得が完了しました！" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Start-Sleep -Seconds 2
