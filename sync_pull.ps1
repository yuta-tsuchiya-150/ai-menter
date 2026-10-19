Write-Host "[SYNC] Pulling latest changes from GitHub (git pull origin main)..." -ForegroundColor Cyan
git pull origin main
Write-Host "`n==========================================" -ForegroundColor Green
Write-Host " [SUCCESS] Pull completed successfully!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Start-Sleep -Seconds 2
