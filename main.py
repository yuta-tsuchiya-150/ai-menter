from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import datetime

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
def index():
    now = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    return f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <script src="https://cdn.tailwindcss.com"></script>
        <title>AI速報エージェント</title>
    </head>
    <body class="bg-slate-50 p-8 flex flex-col items-center">
        <div class="max-w-md w-full bg-white rounded-xl shadow-md p-6 border border-slate-100">
            <div class="flex items-center space-x-2 mb-4">
                <span class="inline-block w-3 h-3 bg-emerald-500 rounded-full animate-pulse"></span>
                <span class="text-sm font-bold text-emerald-700">AIエージェント自律稼働中</span>
            </div>
            <p class="text-xs text-slate-500 mb-2">毎朝 07:00 自動巡回・更新</p>
            <p class="text-xs text-slate-400 mb-6">最終更新日時: {now}</p>
            
            <button onclick="location.reload()" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-lg shadow mb-6">
                ⚡ 今すぐ最新情報に更新
            </button>

            <div class="space-y-4">
                <div class="p-4 bg-slate-50 rounded-lg border border-slate-200">
                    <h3 class="font-bold text-slate-800 text-sm mb-1">① 本日の注目トレンド</h3>
                    <p class="text-xs text-slate-600">50代からの自律AI活用・ノーコード起業が急増中。</p>
                </div>
                <div class="p-4 bg-slate-50 rounded-lg border border-slate-200">
                    <h3 class="font-bold text-slate-800 text-sm mb-1">② おすすめのアクション</h3>
                    <p class="text-xs text-slate-600">Codespacesで完全無料の自動化基盤を触ってみる。</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
