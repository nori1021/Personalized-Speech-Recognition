@echo off
chcp 65001 > nul
cd /d "%~dp0"
echo === 音声認識アプリケーション ===

echo 初期化中...
echo キャッシュディレクトリを作成中...

:: 環境変数の設定
set "PYTHONPATH=%~dp0;%PYTHONPATH%"
set "LOCALAPPDATA=%LOCALAPPDATA%"
set "WHISPER_HOME=%LOCALAPPDATA%\WhisperSR"
set "XDG_CACHE_HOME=%LOCALAPPDATA%\WhisperSR"
set "TEMP=%LOCALAPPDATA%\WhisperSR\temp"
set "TMP=%LOCALAPPDATA%\WhisperSR\temp"

:: 必要なディレクトリを作成
mkdir "%WHISPER_HOME%\models" 2>nul
mkdir "%WHISPER_HOME%\assets" 2>nul
mkdir "%WHISPER_HOME%\temp" 2>nul
mkdir "%WHISPER_HOME%\transcripts" 2>nul
mkdir "%WHISPER_HOME%\dataset" 2>nul

echo アプリケーションを起動中...

:: Pythonスクリプトを実行
python sr_app.py

if errorlevel 1 (
    echo エラーが発生しました。
    echo メッセージを確認してください。
    pause
    exit /b 1
)

pause
