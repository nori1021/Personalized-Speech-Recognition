# UTF-8 with BOM
$OutputEncoding = [System.Text.Encoding]::UTF8

# アプリケーションのキャッシュディレクトリのパスを設定
$appDataDir = [System.IO.Path]::Combine($env:LOCALAPPDATA, 'WhisperSR')
$directories = @(
    [System.IO.Path]::Combine($appDataDir),
    [System.IO.Path]::Combine($appDataDir, 'models'),
    [System.IO.Path]::Combine($appDataDir, 'assets'),
    [System.IO.Path]::Combine($appDataDir, 'temp')
)

# 各ディレクトリの権限を確認
foreach ($dir in $directories) {
    Write-Host "`nChecking permissions for: $dir" -ForegroundColor Cyan
    
    if (Test-Path $dir) {
        $acl = Get-Acl $dir
        $currentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
        
        Write-Host "Owner: $($acl.Owner)" -ForegroundColor Yellow
        Write-Host "Access Rules:" -ForegroundColor Yellow
        $acl.Access | ForEach-Object {
            Write-Host "  $($_.IdentityReference) : $($_.FileSystemRights)"
        }
        
        # 現在のユーザーの権限を確認
        $userRights = $acl.Access | Where-Object { $_.IdentityReference.Value -eq $currentUser }
        if ($userRights) {
            Write-Host "`nCurrent user ($currentUser) permissions:" -ForegroundColor Green
            Write-Host "  $($userRights.FileSystemRights)"
        } else {
            Write-Host "`nWarning: No explicit permissions for current user" -ForegroundColor Red
        }
    } else {
        Write-Host "Warning: Directory does not exist" -ForegroundColor Red
    }
    Write-Host "-----------------------------------------"
}

Write-Host "`nPress Enter to exit..." -NoNewline
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
