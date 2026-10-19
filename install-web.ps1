<#
.SYNOPSIS
  One-line web installer for capstone-labmate -- no local installer file needed.

.DESCRIPTION
  Self-contained bootstrap designed to be piped straight into PowerShell:

      irm https://raw.githubusercontent.com/<owner>/capstone-labmate/main/install-web.ps1 | iex

  It downloads the skill package to a temp folder, copies the capstone-labmate
  skill into each target harness framework's skills directory, verifies the
  install, and cleans up after itself. By default it pulls the lightweight
  release asset (capstone-labmate.zip); if that is unavailable it falls back to
  the full repository archive. Pure Windows PowerShell 5.1+; no Python required.

  To pass parameters through the pipe, use the scriptblock form:

      & ([scriptblock]::Create((irm https://raw.githubusercontent.com/<owner>/capstone-labmate/main/install-web.ps1))) `
          -Frameworks workbuddy,codex -Scope user

.PARAMETER Repo
  GitHub "owner/name" of the published repository.
  >>> CHANGE THIS to wherever you push this folder. The one-liner in the
  >>> README uses the same value; nothing works until the repo exists.

.PARAMETER Branch
  Branch or tag to fetch for the codeload fallback. Defaults to "main".

.PARAMETER Tag
  Specific release tag for the release asset (e.g. "v0.0.0-beta").
  Empty = use the latest release. Ignored when the release asset is missing
  (falls back to codeload).

.PARAMETER Skill
  Skill name(s) to install; comma-separated values are accepted.
  Defaults to "capstone-labmate" (the only skill in this package).

.PARAMETER Frameworks
  Target harness framework(s): workbuddy, claude, codex, dsh.
  Comma-separated values are accepted. Defaults to workbuddy.

.PARAMETER Scope
  "user" installs into your home folder (every project of the framework can
  use the skill); "project" installs into one task folder only.

.PARAMETER Dir
  Task folder for project scope (defaults to the current directory).

.PARAMETER Force
  Overwrite an existing install instead of skipping it.
#>
[CmdletBinding()]
param(
    [string]$Repo = "JiamingShi-JsPhys/capstone-labmate",
    [string]$Branch = "main",
    [string]$Tag = "",
    [string[]]$Skill = @("capstone-labmate"),
    [string[]]$Frameworks = @("workbuddy"),
    [ValidateSet("user", "project")]
    [string]$Scope = "user",
    [string]$Dir = "",
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
try {
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
}
catch { }

# --------------------------------------------------------------------------
# Framework table
# --------------------------------------------------------------------------
$FrameworkLabels = @{
    workbuddy = "WorkBuddy"
    claude    = "Claude Code"
    codex     = "OpenAI Codex"
    dsh       = "DeepSeek Harness"
}
$UserRoots = @{
    workbuddy = ".workbuddy\skills"
    claude    = ".claude\skills"
    codex     = ".codex\skills"
    dsh       = ".dsh\skills"
}
$ProjectRoots = @{
    workbuddy = ".workbuddy\skills"
    claude    = ".claude\skills"
    codex     = ".agents\skills"
    dsh       = ".dsh\skills"
}

# --------------------------------------------------------------------------
# Install manifest: only these files are copied into the skills folder.
# A skill missing from the table is copied whole (forward-compatible default).
# --------------------------------------------------------------------------
$InstallManifest = @{
    "capstone-labmate" = @("SKILL.md", "skill.json", "scripts", "config", "templates")
}

$SkillZip = "capstone-labmate.zip"

function Resolve-TargetRoot {
    param([string]$Framework, [string]$Scope, [string]$ProjectDir)
    if ($Scope -eq "user") {
        return (Join-Path $HOME $UserRoots[$Framework])
    }
    return (Join-Path $ProjectDir $ProjectRoots[$Framework])
}

# --------------------------------------------------------------------------
# Validate inputs
# --------------------------------------------------------------------------
$badFw = $Frameworks | Where-Object { -not $FrameworkLabels.ContainsKey($_) }
if ($badFw) {
    throw "Unknown framework(s): $($badFw -join ', '). Choose from: $($FrameworkLabels.Keys -join ', ')"
}
if ($Scope -eq "project") {
    if ([string]::IsNullOrWhiteSpace($Dir)) { $Dir = (Get-Location).Path }
    if (-not (Test-Path -LiteralPath $Dir)) { throw "Task folder not found: $Dir" }
}

# --------------------------------------------------------------------------
# Download the package (release asset first, codeload fallback) with retries
# --------------------------------------------------------------------------
$token = [guid]::NewGuid().ToString("N")
$archive = Join-Path $env:TEMP "capstone-labmate-$token.zip"
$expand = Join-Path $env:TEMP "capstone-labmate-$token"

function Get-Archive {
    $urls = @()
    if ($Tag) {
        $urls += "https://github.com/$Repo/releases/download/$Tag/$SkillZip"
    }
    else {
        $urls += "https://github.com/$Repo/releases/latest/download/$SkillZip"
    }
    $urls += "https://codeload.github.com/$Repo/zip/refs/heads/$Branch"

    foreach ($u in $urls) {
        for ($i = 1; $i -le 3; $i++) {
            try {
                Write-Host "Downloading $u (attempt $i/3) ..."
                Invoke-WebRequest -Uri $u -OutFile $archive -UseBasicParsing
                return $u
            }
            catch {
                if ($i -eq 3) { Write-Host "  failed: $_" }
                else { Start-Sleep -Seconds 2 }
            }
        }
    }
    throw "All download sources failed for $Repo."
}

try {
    $src = Get-Archive
    Write-Host "capstone-labmate web installer"
    Write-Host "  source  : $src"
    Write-Host "  scope   : $Scope$(if ($Scope -eq 'project') { " -> $Dir" })"
    Write-Host "  targets : $(($Frameworks | ForEach-Object { $FrameworkLabels[$_] }) -join ', ')"
    Write-Host ""

    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [System.IO.Compression.ZipFile]::ExtractToDirectory($archive, $expand)

    # Discover the skill folder(s) containing SKILL.md (handles both layouts).
    $skillDirs = @()
    $candidates = Get-ChildItem -Path $expand -Recurse -Filter SKILL.md -File
    foreach ($c in $candidates) {
        $skillDirs += $c.Directory.FullName
    }
    if (-not $skillDirs) {
        throw "No skill (folder with SKILL.md) found in $src"
    }

    if ($Skill -contains "*" -or $Skill -contains "all") {
        $skills = $skillDirs
    }
    else {
        $skills = @()
        foreach ($name in $Skill) {
            $m = $skillDirs | Where-Object { (Split-Path $_ -Leaf) -eq $name }
            if ($m) { $skills += $m }
            else { throw "Skill '$name' not found. Available: $(($skillDirs | Split-Path -Leaf) -join ', ')" }
        }
    }
    Write-Host "  skills  : $(($skills | Split-Path -Leaf) -join ', ')"
    Write-Host ""

    $installed = 0; $skipped = 0; $failed = @()
    foreach ($s in $skills) {
        $name = Split-Path $s -Leaf
        foreach ($fw in $Frameworks) {
            $label = $FrameworkLabels[$fw]
            $targetRoot = Resolve-TargetRoot -Framework $fw -Scope $Scope -ProjectDir $Dir
            $dst = Join-Path $targetRoot $name
            if (Test-Path -LiteralPath $dst) {
                if ($Force) { Remove-Item -LiteralPath $dst -Recurse -Force }
                else {
                    Write-Host ("  SKIP  {0,-24} {1,-14} already exists (use -Force)" -f $name, $label)
                    $skipped++; continue
                }
            }
            New-Item -ItemType Directory -Path $targetRoot -Force | Out-Null
            New-Item -ItemType Directory -Path $dst -Force | Out-Null
            $keep = $InstallManifest[$name]
            $installOk = $true
            if ($keep) {
                foreach ($rel in $keep) {
                    $item = Join-Path $s $rel
                    if (-not (Test-Path -LiteralPath $item)) {
                        Write-Host ("  FAIL  {0,-24} {1,-14} manifest entry missing: {2}" -f $name, $label, $rel)
                        $installOk = $false; break
                    }
                    Copy-Item -LiteralPath $item -Destination (Join-Path $dst $rel) -Recurse -Force
                }
            }
            else {
                Copy-Item -LiteralPath $s -Destination $dst -Recurse -Force
            }
            if ($installOk -and (Test-Path -LiteralPath (Join-Path $dst "SKILL.md"))) {
                Write-Host ("  OK    {0,-24} {1,-14} {2}" -f $name, $label, $dst)
                $installed++
            }
            else {
                Write-Host ("  FAIL  {0,-24} {1,-14} verification failed" -f $name, $label)
                $failed += "$name -> $label"
            }
        }
    }

    Write-Host ""
    if ($failed.Count -gt 0) {
        Write-Host "Installation finished with errors:" -ForegroundColor Red
        $failed | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
        exit 1
    }
    Write-Host "Installation complete: $installed skill install(s), $skipped skipped."
    if ($Scope -eq "project") { Write-Host "Only this task folder can see the skill(s): $Dir" }
    else { Write-Host "Every project of the selected framework(s) can use the skill(s)." }
    exit 0
}
finally {
    Remove-Item -LiteralPath $expand -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $archive -Force -ErrorAction SilentlyContinue
}
