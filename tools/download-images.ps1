# Downloads every image the site uses from Webflow's CDN into src\images.
# Run from the project folder BEFORE cancelling Webflow:
#   powershell -ExecutionPolicy Bypass -File tools\download-images.ps1
# Then run: python build.py

$root = Split-Path -Parent $PSScriptRoot
$dest = Join-Path $root "src\images"
New-Item -ItemType Directory -Force -Path $dest | Out-Null
$ok = 0; $failed = 0; $skipped = 0

Get-Content (Join-Path $PSScriptRoot "images.txt") | Where-Object { $_.Trim() } | ForEach-Object {
    $url, $name = $_ -split "`t"
    $target = Join-Path $dest $name
    if ((Test-Path $target) -and ((Get-Item $target).Length -gt 0)) { $skipped++; return }
    try {
        Invoke-WebRequest -Uri $url -OutFile $target -UseBasicParsing -TimeoutSec 30
        Write-Host "saved    $name"; $ok++
    } catch {
        Write-Host "FAILED   $name - $($_.Exception.Message)" -ForegroundColor Red; $failed++
    }
}
Write-Host "`n$ok downloaded, $skipped already present, $failed failed"
Write-Host "Now run: python build.py"
