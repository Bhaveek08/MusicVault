$ErrorActionPreference = 'Stop'
$Version = '2.9.8'
$Asset = 'deno-x86_64-pc-windows-msvc.zip'
$ExpectedSha256 = 'cba84b26e0df5ae7f74fc66b86a95b866872a86292ebd84fa1e959927edd93bf'
$Base = "https://github.com/denoland/deno/releases/download/v$Version/$Asset"
$Root = Split-Path -Parent $PSScriptRoot
$Vendor = Join-Path $Root 'vendor'
$Temp = Join-Path $Root '.build-deno'
$Zip = Join-Path $Temp $Asset

New-Item -ItemType Directory -Force -Path $Vendor, $Temp | Out-Null
# Always stage from the verified archive; do not trust a pre-existing binary in vendor/.
Write-Host "Downloading official Deno $Version Windows x64 runtime..." -ForegroundColor Cyan
Invoke-WebRequest -Uri $Base -OutFile $Zip -UseBasicParsing
$Actual = (Get-FileHash -Algorithm SHA256 -Path $Zip).Hash.ToLowerInvariant()
if ($Actual -ne $ExpectedSha256) {
    throw 'Deno download checksum did not match the pinned SHA-256 for this release archive.'
}

$Extract = Join-Path $Temp 'extracted'
if (Test-Path $Extract) { Remove-Item -Recurse -Force $Extract }
Expand-Archive -LiteralPath $Zip -DestinationPath $Extract -Force
$Binary = Get-ChildItem -Path $Extract -Filter 'deno.exe' -Recurse | Select-Object -First 1
if (-not $Binary) { throw 'The verified Deno archive did not contain deno.exe.' }
Copy-Item -LiteralPath $Binary.FullName -Destination (Join-Path $Vendor 'deno.exe') -Force
$VersionOutput = & (Join-Path $Vendor 'deno.exe') --version 2>&1
if ($LASTEXITCODE -ne 0 -or ($VersionOutput -join ' ') -notmatch "deno $Version") {
    Remove-Item -Force (Join-Path $Vendor 'deno.exe') -ErrorAction SilentlyContinue
    throw 'Bundled Deno failed its version check.'
}
Remove-Item -Recurse -Force $Temp
Write-Host "Verified and staged Deno $Version." -ForegroundColor Green
