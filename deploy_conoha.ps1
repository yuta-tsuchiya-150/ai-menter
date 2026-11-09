$Key = "$HOME\.ssh\conoha_wing.pem"
if (-not (Test-Path $Key)) {
    $Key = "C:\Users\yusuke_tsuchiya\Downloads\key-2026-11-09-16-10.pem"
}

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  ConoHa WING ツアーポータル自動デプロイ開始" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

Write-Host "`n[1/3] サーバー側にディレクトリを作成中..." -ForegroundColor Yellow
ssh -i $Key -p 8022 -o StrictHostKeyChecking=no c6891274@www1211.conoha.ne.jp "mkdir -p ~/public_html/2026091711175w334chu.conohawing.com/tours"

Write-Host "[2/3] ファイルを ConoHa WING へアップロード中..." -ForegroundColor Yellow
scp -P 8022 -i $Key -o StrictHostKeyChecking=no -r tours-portal/* c6891274@www1211.conoha.ne.jp:~/public_html/2026091711175w334chu.conohawing.com/tours/

Write-Host "[3/3] 権限を最適化中..." -ForegroundColor Yellow
ssh -i $Key -p 8022 -o StrictHostKeyChecking=no c6891274@www1211.conoha.ne.jp "chmod -R 755 ~/public_html/2026091711175w334chu.conohawing.com/tours"

Write-Host "`n========================================================" -ForegroundColor Green
Write-Host "  [成功] ConoHa WING への本番デプロイが完了しました！" -ForegroundColor Green
Write-Host "  本番ポータルURL: http://2026091711175w334chu.conohawing.com/tours/" -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Green
Start-Sleep -Seconds 3
