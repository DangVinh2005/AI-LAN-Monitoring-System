# Script to download noVNC library
# Run this script to download noVNC locally

$novncDir = "public\js\novnc"
$outputFile = "$novncDir\rfb.min.js"

# Create directory if it doesn't exist
if (-not (Test-Path $novncDir)) {
    New-Item -ItemType Directory -Force -Path $novncDir | Out-Null
    Write-Host "Created directory: $novncDir" -ForegroundColor Green
}

# Try to download from GitHub releases (more reliable)
Write-Host "Attempting to download noVNC from GitHub..." -ForegroundColor Yellow

# Try downloading from CDN (npm package)
$cdnUrls = @(
    "https://cdn.jsdelivr.net/npm/novnc@1.4.0/core/rfb.js",
    "https://unpkg.com/novnc@1.4.0/core/rfb.js"
)

# Try downloading from raw.githubusercontent.com as fallback
$githubUrls = @(
    "https://raw.githubusercontent.com/novnc/noVNC/v1.4.0/core/rfb.js",
    "https://raw.githubusercontent.com/novnc/noVNC/master/core/rfb.js"
)

$allUrls = $cdnUrls + $githubUrls

$success = $false
foreach ($url in $allUrls) {
    try {
        Write-Host "Trying: $url" -ForegroundColor Cyan
        Invoke-WebRequest -Uri $url -OutFile $outputFile -ErrorAction Stop
        Write-Host "Successfully downloaded noVNC to: $outputFile" -ForegroundColor Green
        $success = $true
        break
    } catch {
        Write-Host "Failed: $_" -ForegroundColor Red
    }
}

if (-not $success) {
    Write-Host "`nCould not download automatically. Please:" -ForegroundColor Yellow
    Write-Host "1. Visit: https://github.com/novnc/noVNC" -ForegroundColor Cyan
    Write-Host "2. Download the core/rfb.js file" -ForegroundColor Cyan
    Write-Host "3. Save it as: $outputFile" -ForegroundColor Cyan
    Write-Host "`nOr use npm:" -ForegroundColor Yellow
    Write-Host "npm install novnc" -ForegroundColor Cyan
    Write-Host "Then copy node_modules/novnc/core/rfb.js to $outputFile" -ForegroundColor Cyan
}

