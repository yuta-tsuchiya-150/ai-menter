$status = git status --porcelain
if ($status) {
    Write-Host "[SYNC] Changes detected. Committing and pushing to GitHub..." -ForegroundColor Cyan
    git add .
    $now = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    git commit -m "sync: PC switch ($now)"
    git push origin main
    Write-Host "`n==========================================" -ForegroundColor Green
    Write-Host " [SUCCESS] Push completed successfully!" -ForegroundColor Green
    Write-Host "==========================================" -ForegroundColor Green
} else {
    Write-Host "`n[INFO] No local changes to commit. Checking remote status..." -ForegroundColor Yellow
    git push origin main
    Write-Host "[SUCCESS] Up to date." -ForegroundColor Green
}
Start-Sleep -Seconds 2
