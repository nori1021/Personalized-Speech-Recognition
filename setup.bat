@echo off
cd /d "%~dp0"
echo === WhisperSR セットアップ ===

REM PowerShellの実行ポリシーを確認
powershell -Command "Get-ExecutionPolicy" > temp.txt
set /p POLICY=<temp.txt
del temp.txt

REM 実行ポリシーがRestrictedの場合は一時的に変更
if "%POLICY%"=="Restricted" (
    echo PowerShellの実行ポリシーを一時的に変更します...
    powershell -Command "Set-ExecutionPolicy RemoteSigned -Scope Process"
)

REM セットアップスクリプトを実行
echo.
echo セットアップを開始します...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup.ps1"

if errorlevel 1 (
    echo セットアップに失敗しました。
    echo エラーの詳細については上記のメッセージを確認してください。
    pause
    exit /b 1
)

echo.
echo セットアップが完了しました。
timeout /t 3
