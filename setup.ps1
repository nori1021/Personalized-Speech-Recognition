# 管理者権限の確認
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "このスクリプトは管理者権限で実行する必要があります。"
    Write-Host "スクリプトを管理者として再実行します..."
    Start-Process powershell -Verb RunAs -ArgumentList "-File `"$PSCommandPath`""
    Exit
}

Write-Host "=== WhisperSR セットアップ ==="
Write-Host ""

# Pythonのバージョン確認
try {
    $pythonVersion = python --version
    Write-Host "Python version: $pythonVersion"
} catch {
    Write-Host "Pythonがインストールされていません。"
    Write-Host "https://www.python.org/downloads/ からPythonをインストールしてください。"
    Exit 1
}

# pipのアップグレード
Write-Host "`npipをアップグレード中..."
python -m pip install --upgrade pip

# 必要なパッケージのインストール
Write-Host "`n必要なパッケージをインストール中..."
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$requirementsPath = Join-Path $scriptPath "requirements.txt"

if (Test-Path $requirementsPath) {
    python -m pip install -r $requirementsPath
} else {
    Write-Host "requirements.txtが見つかりません: $requirementsPath"
    Exit 1
}

# アプリケーションディレクトリの作成
Write-Host "`nアプリケーションディレクトリを作成中..."
$appDir = Join-Path $env:LOCALAPPDATA "WhisperSR"
$dirs = @(
    "models",
    "assets",
    "temp",
    "transcripts",
    "dataset",
    "annotations",
    "finetuned_models"
)

foreach ($dir in $dirs) {
    $path = Join-Path $appDir $dir
    if (-not (Test-Path $path)) {
        New-Item -ItemType Directory -Path $path -Force | Out-Null
        Write-Host "作成: $path"
    } else {
        Write-Host "確認: $path"
    }
}

# 環境チェックの実行
Write-Host "`n環境チェックを実行中..."
python test_environment.py

# Whisper初期設定の実行
Write-Host "`nWhisper初期設定を実行中..."
python prepare_whisper.py

# デスクトップショートカットの作成
Write-Host "`nデスクトップショートカットを作成中..."
try {
    & "$PSScriptRoot\create_shortcut.ps1"
    Write-Host "✓ ショートカットの作成が完了しました"
} catch {
    Write-Host "✗ ショートカットの作成に失敗しました: $($_.Exception.Message)"
}

Write-Host "`nセットアップが完了しました！"
Write-Host "デスクトップのショートカットからアプリケーションを起動できます。"
Write-Host ""
Pause
