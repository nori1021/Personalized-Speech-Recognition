# Ensure running as administrator
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Warning "Please run this script as Administrator"
    exit
}

# Application cache directory paths
$appDataDir = [System.IO.Path]::Combine($env:LOCALAPPDATA, 'WhisperSR')
$directories = @(
    $appDataDir,
    [System.IO.Path]::Combine($appDataDir, 'models'),
    [System.IO.Path]::Combine($appDataDir, 'assets'),
    [System.IO.Path]::Combine($appDataDir, 'temp')
)

# Create directories and set permissions
foreach ($dir in $directories) {
    Write-Host "Processing directory: $dir" -ForegroundColor Cyan
    
    # Create directory if it doesn't exist
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force
        Write-Host "Created directory: $dir" -ForegroundColor Green
    }
    
    try {
        # Get current user
        $currentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
        
        # Get current ACL
        $acl = Get-Acl $dir
        
        # Create new rule for current user
        $accessRule = New-Object System.Security.AccessControl.FileSystemAccessRule(
            $currentUser,
            "FullControl",
            "ContainerInherit,ObjectInherit",
            "None",
            "Allow"
        )
        
        # Remove existing rules for current user
        $acl.Access | Where-Object { $_.IdentityReference.Value -eq $currentUser } | ForEach-Object {
            $acl.RemoveAccessRule($_) | Out-Null
        }
        
        # Add new rule
        $acl.AddAccessRule($accessRule)
        
        # Apply new ACL
        Set-Acl -Path $dir -AclObject $acl
        Write-Host "Successfully set permissions for: $dir" -ForegroundColor Green
        
        # Verify permissions
        $newAcl = Get-Acl $dir
        $userRights = $newAcl.Access | Where-Object { $_.IdentityReference.Value -eq $currentUser }
        Write-Host "Verified permissions:" -ForegroundColor Yellow
        Write-Host "  User: $($userRights.IdentityReference)" -ForegroundColor Yellow
        Write-Host "  Rights: $($userRights.FileSystemRights)" -ForegroundColor Yellow
        
    } catch {
        Write-Host "Error setting permissions for $dir : $_" -ForegroundColor Red
    }
    Write-Host "-----------------------------------------"
}

Write-Host "`nPermissions update complete. Press Enter to exit..." -NoNewline
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
