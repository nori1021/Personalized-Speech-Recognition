# ショートカット作成スクリプト
$WshShell = New-Object -ComObject WScript.Shell

# アイコンの作成
$iconPath = Join-Path $PSScriptRoot "app.ico"
if (-not (Test-Path $iconPath)) {
    # create_icon.ps1から$iconBase64を取得
    $iconContent = Get-Content (Join-Path $PSScriptRoot "create_icon.ps1") | Select-String -Pattern '\$iconBase64\s*=\s*@(.+)@' | ForEach-Object { $_.Matches.Groups[1].Value }
    if ($iconContent) {
        [System.Convert]::FromBase64String($iconContent) | Set-Content -Path $iconPath -Encoding Byte
    }
}

# アプリケーションのパス
$AppPath = Join-Path $PSScriptRoot "launch_app.bat"
$DesktopPath = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $DesktopPath "WhisperSR.lnk"

# ショートカットの作成
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $AppPath
$Shortcut.WorkingDirectory = $PSScriptRoot
$Shortcut.Description = "WhisperSR - パーソナライズド音声認識システム"
if (Test-Path $iconPath) {
    $Shortcut.IconLocation = $iconPath
}

# ショートカットの保存
$Shortcut.Save()

Write-Host "デスクトップにショートカットを作成しました: $ShortcutPath"
