$ErrorActionPreference = "Stop"

$windows = Get-CimInstance Win32_OperatingSystem
$wslStatus = & wsl.exe --status 2>&1 | Out-String
$wslList = & wsl.exe --list --verbose 2>&1 | Out-String
$dockerVersion = $null
if (Get-Command docker -ErrorAction SilentlyContinue) {
    $dockerVersion = (& docker version --format '{{.Client.Version}}' 2>$null | Out-String).Trim()
}

$result = [ordered]@{
    layer = "windows"
    windows_caption = $windows.Caption
    windows_version = $windows.Version
    windows_build = $windows.BuildNumber
    powershell_version = $PSVersionTable.PSVersion.ToString()
    wsl_status = $wslStatus.Trim()
    wsl_distributions = $wslList.Trim()
    docker_client_version = $dockerVersion
}

$result | ConvertTo-Json -Depth 4
