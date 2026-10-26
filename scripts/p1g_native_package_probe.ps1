# Research-only Windows builder. Creates TWO local unsigned CI probe executables.
# No artifact upload, customers' code, installed product change or paid AI calls.
$ErrorActionPreference = 'Stop'
if ($env:OS -ne 'Windows_NT') { throw 'Windows CI required.' }
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Push-Location $repo
try {
  $root = Join-Path $repo '.build-p1g'
  if (Test-Path -LiteralPath $root) { throw 'Refusing existing probe build directory.' }
  New-Item -ItemType Directory -Path $root | Out-Null
  $entry = 'scripts/p1g_native_exe_entry.py'
  $common = @('--clean','--noconfirm','--onefile','--console','--noupx','--paths','.')
  $baselineDist = Join-Path $root 'baseline-dist'
  $candidateDist = Join-Path $root 'native-dist'
  $baselineWork = Join-Path $root 'baseline-work'
  $candidateWork = Join-Path $root 'native-work'
  $baselineSpec = Join-Path $root 'baseline-spec'
  $candidateSpec = Join-Path $root 'native-spec'
  python -m PyInstaller @common --distpath "$baselineDist" --workpath "$baselineWork" --specpath "$baselineSpec" --name P1GBaseline --exclude-module scripts.prototype_js_ts_adapter --exclude-module tree_sitter --exclude-module tree_sitter_javascript --exclude-module tree_sitter_typescript "$entry"
  if ($LASTEXITCODE -ne 0) { throw 'Baseline PyInstaller failed.' }
  $baseline = Join-Path $baselineDist 'P1GBaseline.exe'
  if (-not (Test-Path -LiteralPath $baseline)) { throw 'Missing baseline EXE.' }
  & $baseline --baseline
  if ($LASTEXITCODE -ne 0) { throw 'Baseline EXE failed.' }

  python -m PyInstaller @common --distpath "$candidateDist" --workpath "$candidateWork" --specpath "$candidateSpec" --name P1GNative --hidden-import scripts.prototype_js_ts_adapter --collect-all tree_sitter --collect-all tree_sitter_javascript --collect-all tree_sitter_typescript "$entry"
  if ($LASTEXITCODE -ne 0) { throw 'Native candidate PyInstaller failed.' }
  $candidate = Join-Path $candidateDist 'P1GNative.exe'
  if (-not (Test-Path -LiteralPath $candidate)) { throw 'Missing native research EXE.' }
  & $candidate --synthetic
  if ($LASTEXITCODE -ne 0) { throw 'Frozen native JS/TS/TSX synthetic smoke failed.' }

  $baseBytes = (Get-Item -LiteralPath $baseline).Length
  $nativeBytes = (Get-Item -LiteralPath $candidate).Length
  if ($baseBytes -le 0 -or $nativeBytes -le 0) { throw 'Empty EXE.' }
  $delta = $nativeBytes - $baseBytes
  if ($delta -le 0) { throw 'Unexpected native parser size delta.' }
  $measurement = @{
    kind = 'P1G_RESEARCH_WINDOWS_EXE_DELTA'
    baseline_bytes = $baseBytes
    candidate_bytes = $nativeBytes
    delta_bytes = $delta
    measurement_is_not_product_exe_delta = $true
    grammar_native_smoke = 'PASS'
    signed = $false
    customer_exe_modified = $false
    customer_exe_published = $false
    original_notice_in_exe_approved = $false
    customer_release_ready = $false
  }
  Write-Output ($measurement | ConvertTo-Json -Compress)
} finally {
  Pop-Location
}
