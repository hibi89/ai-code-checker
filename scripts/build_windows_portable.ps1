# Developer-only script. Does not install packages, call AI APIs or upload source.
[CmdletBinding()]
param(
  [switch]$OwnerAcceptance,
  [string]$EvidenceDir
)
$ErrorActionPreference = 'Stop'
# Optional owner-only local acceptance: no automatic dependency installation.
# Resolve relative evidence paths before Push-Location changes the working directory.
$resolvedEvidenceDir = $null
if ($OwnerAcceptance) {
  if ([string]::IsNullOrWhiteSpace($EvidenceDir)) { throw '-OwnerAcceptance requires -EvidenceDir.' }
  if ($PSVersionTable.PSVersion.Major -lt 7) { throw 'Owner acceptance requires PowerShell 7+ (pwsh).' }
  $resolvedEvidenceDir = [System.IO.Path]::GetFullPath($EvidenceDir)
  if (Test-Path -LiteralPath $resolvedEvidenceDir) { throw 'EvidenceDir must be a new local directory.' }
} elseif ($PSBoundParameters.ContainsKey('EvidenceDir')) {
  throw '-EvidenceDir requires explicit -OwnerAcceptance.'
}
if ($env:OS -ne 'Windows_NT') { throw 'Windows is required for EXE packaging.' }
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$dist = Join-Path $repo 'dist-windows'
$work = Join-Path $repo '.build-windows'
$exe = Join-Path $dist 'CodeCheckerOffline.exe'
if (Test-Path -LiteralPath $exe) { throw 'Existing EXE will not be overwritten.' }
# Owner-only guard. Common cloud-sync roots are not privacy-safe output stores.
# Conservatively reject known folder names, environment roots and junctions.
# This does NOT certify that a path is free of third-party backup software.
function Assert-OwnerPrivatePath([string]$RawPath) {
  $full = [System.IO.Path]::GetFullPath($RawPath)
  $root = [System.IO.Path]::GetPathRoot($full)
  if ([string]::IsNullOrWhiteSpace($root) -or
      $full.StartsWith('\\') -or $full.StartsWith('//') -or
      $root.StartsWith('\\') -or $root.StartsWith('//')) {
    throw 'Owner acceptance refuses remote or device paths.'
  }
  $drive = [System.IO.DriveInfo]::new($root)
  if ($drive.DriveType.ToString() -notin @('Fixed', 'Removable', 'Ram')) {
    throw 'Owner acceptance refuses remote or mapped drives.'
  }
  if ($full -match '(?i)(?:^|[\\/])(?:OneDrive(?: - [^\\/]+)?|Dropbox|Google Drive|iCloudDrive)(?:[\\/]|$)') {
    throw 'Owner acceptance refuses known cloud-sync folder paths.'
  }
  foreach ($envRoot in @($env:OneDrive, $env:OneDriveConsumer, $env:OneDriveCommercial)) {
    if (-not [string]::IsNullOrWhiteSpace($envRoot)) {
      $canonical = [System.IO.Path]::GetFullPath($envRoot).TrimEnd([char[]]@('\', '/'))
      if ($full.Equals($canonical, [System.StringComparison]::OrdinalIgnoreCase) -or
          $full.StartsWith(($canonical + '\'), [System.StringComparison]::OrdinalIgnoreCase)) {
        throw 'Owner acceptance refuses configured OneDrive roots.'
      }
    }
  }
  $cursor = $full
  while (-not [string]::IsNullOrWhiteSpace($cursor)) {
    if (Test-Path -LiteralPath $cursor) {
      $item = Get-Item -LiteralPath $cursor -Force -ErrorAction Stop
      if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw 'Owner acceptance refuses linked or junction paths.'
      }
    }
    $parent = [System.IO.Path]::GetDirectoryName($cursor)
    if ([string]::IsNullOrWhiteSpace($parent) -or $parent -eq $cursor) { break }
    $cursor = $parent
  }
}
if ($OwnerAcceptance) {
  # Check all source and output roots before invoking Python or creating a build.
  foreach ($path in @($repo, $dist, $work, $resolvedEvidenceDir)) {
    Assert-OwnerPrivatePath $path
  }
}

Push-Location $repo
try {
  python -c "import PyInstaller, tkinter; print('Build dependencies found')"
  if ($LASTEXITCODE -ne 0) { throw 'Install the pinned build dependencies.' }
  python -m PyInstaller --clean --onefile --windowed --noupx --name CodeCheckerOffline --distpath "$dist" --workpath "$work" --specpath "$work" desktop_ui.py
  if ($LASTEXITCODE -ne 0) { throw 'PyInstaller build failed.' }
  if (-not (Test-Path -LiteralPath $exe)) { throw 'EXE not created.' }
  & $exe --self-test
  if ($LASTEXITCODE -ne 0) { throw 'Packaged offline self-test failed.' }
  & $exe --gui-smoke
  if ($LASTEXITCODE -ne 0) { throw 'Packaged Tk GUI startup smoke failed.' }
  Write-Output 'PACKAGED_TK_WINDOW_STARTUP_PASS'
  # Unlike --gui-smoke, this runs real preview, scan and report controls inside
  # the one-file executable with synthetic local code. No customer data or upload.
  & $exe --scenario-smoke
  if ($LASTEXITCODE -ne 0) { throw 'Packaged full Tk workflow acceptance smoke failed.' }
  Write-Output 'PACKAGED_TK_FULL_WORKFLOW_PASS'
  $hash = Get-FileHash -LiteralPath $exe -Algorithm SHA256
  Write-Output 'CANDIDATE_BUILT_SMOKE_PASS'
  Write-Output "PATH=$exe"
  Write-Output "SHA256=$($hash.Hash)"
  Write-Output 'WINDOWS_GUI_CLICK_TEST=UNVERIFIED'
  Write-Output 'CLEAN_WINDOWS_SMARTSCREEN=UNVERIFIED'
  if ($OwnerAcceptance) {
    $ownerScript = Join-Path $PSScriptRoot 'windows_owner_oneclick_qa.ps1'
    if (-not (Test-Path -LiteralPath $ownerScript -PathType Leaf)) {
      throw 'Adjacent owner acceptance script is missing.'
    }
    & $ownerScript -ExePath $exe -EvidenceDir $resolvedEvidenceDir
    $receiptPath = Join-Path $resolvedEvidenceDir 'owner-preflight.json'
    if (-not (Test-Path -LiteralPath $receiptPath -PathType Leaf)) {
      throw 'Owner acceptance receipt missing; do not release this candidate.'
    }
    $receipt = Get-Content -LiteralPath $receiptPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $gateProperties = @($receipt.manual_gates.PSObject.Properties)
    if ($receipt.format -cne 'code_checker_owner_windows_oneclick_preflight_v1' -or
        $receipt.exe_sha256 -cne $hash.Hash.ToLowerInvariant() -or
        $receipt.customer_release_ready -cne $false -or
        $receipt.customer_os_acceptance_certified -cne $false -or
        $receipt.rights_and_notice_certified -cne $false -or
        $gateProperties.Count -ne 10 -or
        @($gateProperties | Where-Object { $_.Value -cne 'UNVERIFIED' }).Count -ne 0 -or
        (Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash -cne $hash.Hash) {
      throw 'Owner acceptance receipt disagrees with EXE or prematurely approves a release.'
    }
    Write-Output 'OWNER_PRIVATE_CANDIDATE_PREFLIGHT_PASS_CUSTOMER_RELEASE_BLOCKED'
  }
} finally {
  Pop-Location
}
