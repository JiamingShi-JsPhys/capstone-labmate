# capstone-labmate installer (Windows / WorkBuddy)
# Usage: .\install.ps1 [DEST_DIR]
$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Definition
$src = Join-Path $here "capstone-labmate"
$dest = if ($args.Count -ge 1) { $args[0] } else { Join-Path $env:USERPROFILE ".workbuddy\skills\capstone-labmate" }
if (Test-Path $dest) { Remove-Item $dest -Recurse -Force }
New-Item -ItemType Directory -Force -Path (Split-Path $dest) | Out-Null
Copy-Item $src $dest -Recurse -Force
Write-Host "Installed capstone-labmate -> $dest"
