# Developer-only script. Does not install packages, call AI APIs or upload source.
$ErrorActionPreference = 'Stop'
if ($env:OS -ne 'Windows_NT') { throw 'Windows is required for EXE packaging.' }
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$dist = Join-Path $repo 'dist-windows'
$work = Join-Path $repo '.build-windows'
$exe = Join-Path $dist 'CodeCheckerOffline.exe'
if (Test-Path -LiteralPath $exe) { throw 'Existing EXE will not be overwritten.' }
Push-Location $repo
try {
  python -c "import pydantic, PyInstaller, tkinter; print('Build dependencies found')"
  if ($LASTEXITCODE -ne 0) { throw 'Install the pinned build dependencies.' }
  python -m PyInstaller --clean --onefile --windowed --noupx --name CodeCheckerOffline --distpath "$dist" --workpath "$work" --specpath "$work" --collect-submodules pydantic desktop_ui.py
  if ($LASTEXITCODE -ne 0) { throw 'PyInstaller build failed.' }
  if (-not (Test-Path -LiteralPath $exe)) { throw 'EXE not created.' }
  & $exe --self-test
  if ($LASTEXITCODE -ne 0) { throw 'Packaged offline self-test failed.' }
  & $exe --gui-smoke
  if ($LASTEXITCODE -ne 0) { throw 'Packaged Tk GUI startup smoke failed.' }
  Write-Output 'PACKAGED_TK_WINDOW_STARTUP_PASS'
  $hash = Get-FileHash -LiteralPath $exe -Algorithm SHA256
  Write-Output 'CANDIDATE_BUILT_SMOKE_PASS'
  Write-Output "PATH=$exe"
  Write-Output "SHA256=$($hash.Hash)"
  Write-Output 'WINDOWS_GUI_CLICK_TEST=UNVERIFIED'
  Write-Output 'CLEAN_WINDOWS_SMARTSCREEN=UNVERIFIED'
} finally {
  Pop-Location
}
