# Safe local developer smoke / full regression (synthetic only; no installs).
param([switch]$Quick, [switch]$IncludeGuiSmoke)
$ErrorActionPreference = 'Stop'
if ($env:OS -ne 'Windows_NT') { throw 'Windows required.' }
$repo = (Resolve-Path -LiteralPath $PSScriptRoot).Path
$python = Get-Command python -ErrorAction SilentlyContinue
if ($null -eq $python) { throw 'Python is missing. No automatic install attempted.' }
$sha = 'UNAVAILABLE'
try {
  $git = Get-Command git -ErrorAction Stop
  $candidate = (& $git.Source -C $repo rev-parse HEAD 2>$null)
  if ($LASTEXITCODE -eq 0 -and $candidate -match '^[0-9a-f]{40}$') { $sha = $candidate.Trim() }
} catch { $sha = 'UNAVAILABLE' }
$checks = [System.Collections.Generic.List[object]]::new()
function Invoke-Check {
  param([string]$Name, [string[]]$Arguments)
  $folder = Join-Path ([System.IO.Path]::GetTempPath()) ('codechecker-check-' + [guid]::NewGuid().ToString('N'))
  [void][System.IO.Directory]::CreateDirectory($folder)
  $stdout = Join-Path $folder 'out.txt'
  $stderr = Join-Path $folder 'err.txt'
  $status = 'FAIL'; $exitCode = -1; $tail = ''
  try {
    $p = Start-Process -FilePath $python.Source -ArgumentList $Arguments -WorkingDirectory $repo -NoNewWindow -Wait -PassThru -RedirectStandardOutput $stdout -RedirectStandardError $stderr
    $exitCode = [int]$p.ExitCode
    if ($exitCode -eq 0) { $status = 'PASS' }
    else {
      $lines = @()
      if (Test-Path -LiteralPath $stdout) { $lines += @(Get-Content -LiteralPath $stdout -Tail 10) }
      if (Test-Path -LiteralPath $stderr) { $lines += @(Get-Content -LiteralPath $stderr -Tail 10) }
      $tail = ($lines | Select-Object -Last 12) -join ([Environment]::NewLine)
    }
  } catch { $tail = $_.Exception.GetType().Name }
  finally { [System.IO.Directory]::Delete($folder, $true) }
  [void]$checks.Add([ordered]@{name=$Name;status=$status;exit_code=$exitCode;error_tail=$tail})
  Write-Output ("{0}: {1}" -f $Name, $status)
}
Push-Location $repo
try {
  Invoke-Check 'syntax' @('-m','py_compile','desktop_core.py','desktop_ui.py','code_input.py','offline_core.py','offline_report.py','static_checks.py','offline_models.py')
  Invoke-Check 'mvp_offline' @('-m','scripts.mvp_acceptance')
  Invoke-Check 'controller_self_test' @('desktop_ui.py','--self-test')
  if (-not $Quick) {
    Invoke-Check 'unittest_full' @('-m','unittest','discover','-s','tests','-q')
    Invoke-Check 'synthetic_rule_accuracy' @('-m','scripts.evaluate_rule_accuracy')
  } else {
    [void]$checks.Add([ordered]@{name='unittest_full';status='SKIP';exit_code=$null;error_tail='Quick mode'})
    [void]$checks.Add([ordered]@{name='synthetic_rule_accuracy';status='SKIP';exit_code=$null;error_tail='Quick mode'})
  }
  if ($IncludeGuiSmoke) {
    Invoke-Check 'windows_tk_synthetic' @('-m','scripts.windows_gui_e2e')
    Invoke-Check 'windows_pdf_synthetic' @('-m','scripts.windows_browser_pdf_smoke')
  } else {
    [void]$checks.Add([ordered]@{name='windows_tk_synthetic';status='SKIP';exit_code=$null;error_tail='Opt-in only'})
    [void]$checks.Add([ordered]@{name='windows_pdf_synthetic';status='SKIP';exit_code=$null;error_tail='Opt-in only'})
  }
} finally { Pop-Location }
$failed = @($checks | Where-Object { $_['status'] -eq 'FAIL' }).Count
$passed = @($checks | Where-Object { $_['status'] -eq 'PASS' }).Count
$skipped = @($checks | Where-Object { $_['status'] -eq 'SKIP' }).Count
$report = [ordered]@{
  format='codechecker_local_synthetic_verify_v1';git_sha=$sha;python=$python.Source
  checks=$checks.ToArray();pass_count=$passed;fail_count=$failed;skip_count=$skipped
  clean_customer_windows='UNVERIFIED';smartscreen='UNVERIFIED';os_packet_capture='UNVERIFIED'
  commercial_release_approved=$false
}
$path = Join-Path ([System.IO.Path]::GetTempPath()) ('codechecker-verify-' + [guid]::NewGuid().ToString('N') + '.json')
$stream = [System.IO.File]::Open($path,[System.IO.FileMode]::CreateNew,[System.IO.FileAccess]::Write,[System.IO.FileShare]::None)
try {
  $writer = [System.IO.StreamWriter]::new($stream,[System.Text.UTF8Encoding]::new($false))
  try { $writer.Write(($report | ConvertTo-Json -Depth 7)); $writer.Flush() }
  finally { $writer.Dispose() }
} finally { $stream.Dispose() }
Write-Output ("SUMMARY PASS={0} FAIL={1} SKIP={2} SHA={3}" -f $passed,$failed,$skipped,$sha)
Write-Output ("LOCAL_EVIDENCE={0}" -f $path)
Write-Output 'CLEAN_CUSTOMER_WINDOWS_AND_RELEASE=UNVERIFIED'
if ($failed -gt 0) { exit 1 }
exit 0
