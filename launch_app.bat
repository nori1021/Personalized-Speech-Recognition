@echo off
cd /d "%~dp0"
echo === 音声認識アプリケーション起動プロセス ===

REM 環境チェックの実行
echo.
echo 1. 環境チェックを実行中...
python test_environment.py
if errorlevel 1 (
    echo 環境チェックに失敗しました。
    echo 詳細はログを確認してください。
    pause
    exit /b 1
)

REM Whisper初期設定の実行
echo.
echo 2. Whisper初期設定を実行中...
python prepare_whisper.py
if errorlevel 1 (
    echo Whisper初期設定に失敗しました。
    echo 詳細はログを確認してください。
    pause
    exit /b 1
)

REM アプリケーションの起動
echo.
echo 3. アプリケーションを起動中...
python sr_app.py
if errorlevel 1 (
    echo アプリケーションの実行中にエラーが発生しました。
    echo 詳細はエラーメッセージを確認してください。
    pause
    exit /b 1
)

echo.
echo アプリケーションが正常に終了しました。
timeout /t 3
