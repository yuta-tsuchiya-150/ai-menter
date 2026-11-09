@echo off
chcp 65001 > nul
echo ========================================================
echo  ConoHa WING ツアーポータル自動デプロイスクリプト
echo ========================================================
echo.

set /p SSH_USER="ConoHa WING ユーザー名を入力してください: "
set /p SSH_HOST="ConoHa WING ホスト名(またはIP)を入力してください: "
set /p SSH_PORT="SSHポート番号 (通常は 15704): "
set /p SSH_KEY="秘密鍵のパス (.pem): "
set /p REMOTE_DIR="公開先ディレクトリ (例: public_html/yourdomain.com): "

if "%SSH_PORT%"=="" set SSH_PORT=15704

echo.
echo アップロードを開始します...
scp -P %SSH_PORT% -i "%SSH_KEY%" -r tours-portal/* %SSH_USER%@%SSH_HOST%:%REMOTE_DIR%/

if %errorlevel% equ 0 (
    echo.
    echo ========================================================
    echo  アップロードが完了しました！
    echo ========================================================
) else (
    echo.
    echo アップロード中にエラーが発生しました。設定を確認してください。
)
pause
