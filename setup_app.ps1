# スクリプトのディレクトリに移動
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

Write-Host "=== 音声認識アプリケーションセットアップ ===" -ForegroundColor Green

# 依存パッケージのインストール
Write-Host "`n1. 依存パッケージをインストール中..." -ForegroundColor Cyan
python -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "パッケージのインストールに失敗しました" -ForegroundColor Red
    Read-Host "Enterキーを押して終了"
    exit 1
}

# 環境チェック
Write-Host "`n2. 環境チェックを実行中..." -ForegroundColor Cyan
python test_environment.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "環境チェックに失敗しました" -ForegroundColor Red
    Read-Host "Enterキーを押して終了"
    exit 1
}

# Whisper初期設定
Write-Host "`n3. Whisper初期設定を実行中..." -ForegroundColor Cyan
python prepare_whisper.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "Whisper初期設定に失敗しました" -ForegroundColor Red
    Read-Host "Enterキーを押して終了"
    exit 1
}

# デスクトップショートカットの作成
Write-Host "`n4. デスクトップショートカットを作成中..." -ForegroundColor Cyan
python create_shortcut.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "ショートカットの作成に失敗しました" -ForegroundColor Red
    Read-Host "Enterキーを押して終了"
    exit 1
}

Write-Host "`nセットアップが完了しました！" -ForegroundColor Green
Write-Host "デスクトップの「音声認識アプリ」アイコンをダブルクリックして起動してください。" -ForegroundColor Yellow

Read-Host "`nEnterキーを押して終了"
