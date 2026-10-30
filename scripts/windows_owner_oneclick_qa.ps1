# Owner-only, local Windows acceptance preflight for an existing candidate EXE.
# Python-free: reuses two existing read-only/synthetic PowerShell checks.
# A successful receipt NEVER certifies clean consumer OS, legal NOTICE, or sale.
# No customer input, file uploads, network probes, security-setting changes,
# privilege escalation, registry edits, or automatic public distribution.
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$ExePath,
    [Parameter(Mandatory=$true)][string]$EvidenceDir,
    [switch]$IncludeDefenderFileScan
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ($env:OS -ne 'Windows_NT' -or $PSVersionTable.PSVersion.Major -lt 7) {
    throw 'Windows PowerShell 7+ (pwsh) is required for this owner QA tool.'
}
function Assert-LocalPath([string]$RawPath, [bool]$MustExist) {
    if ([string]::IsNullOrWhiteSpace($RawPath) -or $RawPath.Contains([char]0) -or
        $RawPath.StartsWith('\\') -or $RawPath.StartsWith('//')) {
        throw 'UNC/device/blank paths are not accepted.'
    }
    $full = [System.IO.Path]::GetFullPath($RawPath)
    $root = [System.IO.Path]::GetPathRoot($full)
    if ([string]::IsNullOrWhiteSpace($root) -or
        $root.StartsWith('\\') -or $root.StartsWith('//')) {
        throw 'A local filesystem root is required.'
    }
    $drive = [System.IO.DriveInfo]::new($root)
    if ($drive.DriveType.ToString() -notin @('Fixed', 'Removable', 'Ram')) {
        throw 'Mapped or remote drives are not accepted.'
    }
    $cursor = [System.IO.Path]::GetDirectoryName($full)
    while ($cursor) {
        $parent = Get-Item -LiteralPath $cursor -Force -ErrorAction Stop
        if (($parent.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw 'Symlink/junction parent is not accepted.'
        }
        $next = [System.IO.Path]::GetDirectoryName($cursor)
        if ([string]::IsNullOrWhiteSpace($next) -or $cursor -eq $next) { break }
        $cursor = $next
    }
    if ($MustExist -and -not [System.IO.File]::Exists($full)) {
        throw 'Required EXE is absent.'
    }
    return $full
}
$exe = Assert-LocalPath $ExePath $true
$outdir = Assert-LocalPath $EvidenceDir $false
if ($outdir -eq $exe -or (Test-Path -LiteralPath $outdir)) {
    throw 'EvidenceDir must be a fresh, distinct local directory.'
}
$info = Get-Item -LiteralPath $exe -Force -ErrorAction Stop
if (-not ($info -is [System.IO.FileInfo]) -or
    $info.Extension -ine '.exe' -or $info.Length -le 0 -or
    $info.Length -gt 268435456 -or
    (($info.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0)) {
    throw 'Expected a regular, non-linked local EXE up to 256 MiB.'
}
$scriptRoot = Split-Path -Parent $PSCommandPath
$readScript = Join-Path $scriptRoot 'windows_acceptance_readonly.ps1'
$smokeScript = Join-Path $scriptRoot 'windows_local_exe_smoke.ps1'
$scanScript = Join-Path $scriptRoot 'windows_defender_file_scan.ps1'
foreach ($source in @($readScript, $smokeScript)) {
    if (-not [System.IO.File]::Exists($source)) {
        throw 'This owner QA tool requires adjacent original scripts.'
    }
}
if ($IncludeDefenderFileScan -and -not [System.IO.File]::Exists($scanScript)) {
    throw 'Optional Defender scan script is missing.'
}
$initialSha = (Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash.ToLowerInvariant()
$initialSize = [int64]$info.Length
[void][System.IO.Directory]::CreateDirectory($outdir)
# A failed partial run remains local for debugging; it has NO final summary.
$readonlyFile = Join-Path $outdir 'readonly-os-observation.json'
$smokeFile = Join-Path $outdir 'exe-synthetic-gui.json'
$defenderFile = Join-Path $outdir 'optional-defender-command.json'
& $readScript -ExePath $exe -OutputPath $readonlyFile | Out-Null
& $smokeScript -ExePath $exe -OutputPath $smokeFile -TimeoutSeconds 120 | Out-Null
if ($IncludeDefenderFileScan) {
    & $scanScript -ExePath $exe -OutputPath $defenderFile -TimeoutSeconds 120 | Out-Null
}
$readonly = Get-Content -LiteralPath $readonlyFile -Raw -Encoding UTF8 | ConvertFrom-Json
$smoke = Get-Content -LiteralPath $smokeFile -Raw -Encoding UTF8 | ConvertFrom-Json
$valid = (
    $readonly.format -ceq 'code_checker_readonly_windows_acceptance_v1' -and
    $smoke.format -ceq 'code_checker_windows_local_exe_smoke_v1' -and
    $readonly.exe_sha256 -ceq $initialSha -and
    $smoke.exe_sha256 -ceq $initialSha -and
    [int64]$readonly.exe_bytes -eq $initialSize -and
    [int64]$smoke.exe_bytes -eq $initialSize -and
    $readonly.customer_release_ready -ceq $false -and
    $readonly.legal_notice_approved -ceq $false -and
    $smoke.actual_customer_release_ready -ceq $false -and
    $smoke.legal_notice_approved -ceq $false -and
    $smoke.actual_customer_code_used -ceq $false -and
    $smoke.observed_synthetic.packaged_tk_gui_startup -ceq 'PASS' -and
    $smoke.observed_synthetic.packaged_preview_scan_report -ceq 'PASS' -and
    $smoke.observed_synthetic.executable_hash_stable -ceq $true
)
foreach ($state in $readonly.pending_gates.PSObject.Properties) {
    if ($state.Value -cne 'UNVERIFIED') { $valid = $false }
}
foreach ($state in $smoke.pending_gates.PSObject.Properties) {
    if ($state.Value -cne 'UNVERIFIED') { $valid = $false }
}
$scanStatus = 'NOT_REQUESTED'
if ($IncludeDefenderFileScan) {
    $defender = Get-Content -LiteralPath $defenderFile -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($defender.format -cne 'code_checker_defender_file_scan_v1' -or
        $defender.exe_sha256 -cne $initialSha -or
        [int64]$defender.exe_bytes -ne $initialSize -or
        $defender.customer_release_ready -cne $false -or
        $defender.malware_free_certified -cne $false -or
        $defender.retail_defender_acceptance -cne 'UNVERIFIED' -or
        $defender.exe_unchanged -cne $true) {
        $valid = $false
    }
    $scanStatus = [string]$defender.scan_command_status
}
$finalInfo = Get-Item -LiteralPath $exe -Force -ErrorAction Stop
$finalSha = (Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash.ToLowerInvariant()
if (-not $valid -or $finalSha -cne $initialSha -or
    $finalInfo.Length -ne $initialSize) {
    throw 'Different, changed or prematurely approved EXE evidence; NO owner summary.'
}
$gates = [ordered]@{
    buyer_pc_without_python = 'UNVERIFIED'
    user_driven_gui_and_scan = 'UNVERIFIED'
    smartscreen_actual_warning = 'UNVERIFIED'
    defender_buyer_pc_findings = 'UNVERIFIED'
    os_level_network_packets = 'UNVERIFIED'
    korean_html_pdf_visual = 'UNVERIFIED'
    original_tcl_tk_license_terms = 'UNVERIFIED'
    other_bundled_vendor_ownership_and_notice = 'UNVERIFIED'
    customer_zip_license_refund_support = 'UNVERIFIED'
    owner_release_approval = 'UNVERIFIED'
}
$record = [ordered]@{
    format = 'code_checker_owner_windows_oneclick_preflight_v1'
    collection_method = 'python_free_local_powershell_owner_preflight'
    scope = 'owner_candidate_exe_only'
    exe_sha256 = $initialSha
    exe_bytes = $initialSize
    verified_synthetic = [ordered]@{
        readonly_os_receipt_hash = $true
        packaged_tk_gui = 'PASS'
        packaged_preview_scan_report = 'PASS'
    }
    optional_defender_command_status = $scanStatus
    manual_gates = $gates
    customer_source_executed = $false
    os_network_packet_capture = 'NOT_PERFORMED'
    customer_os_acceptance_certified = $false
    rights_and_notice_certified = $false
    customer_release_ready = $false
}
$manual = @"
# Code Checker — Windows owner acceptance checklist (NOT APPROVED)

Candidate EXE SHA-256: $initialSha
Byte size: $initialSize

Do not fill this checklist with simulated CI claims. Use a real, ordinary
Windows 10/11 computer. Keep Defender and SmartScreen enabled; if Windows
blocks an unsigned candidate, record BLOCKED and do NOT bypass the warning
merely to make an acceptance test pass.

- [ ] EXE launches without developer Python or additional installs
- [ ] Human opens the real GUI and confirms Korean labels/controls
- [ ] Human tests paste, file, folder, and ZIP input preview, then scan
- [ ] Human opens HTML and Markdown reports; reruns and checks cleanup
- [ ] Windows SmartScreen/Defender warning and detection outcome observed
- [ ] No unexpected connections with an approved OS-level capture method
- [ ] Korean Edge/Chrome Print-to-PDF visually inspected, multiple pages
- [ ] Exact Tcl and Tk 8.6.15 original license terms separately compared
- [ ] All 71 previously unresolved bundled items reviewed for owner/NOTICE
- [ ] Final customer ZIP, LICENSE/NOTICE, support and refund policy reviewed
- [ ] Owner explicitly approves a specific EXE SHA and the release package

This file is a manual worksheet, not proof any box was completed. Never
upload original EXE, source code, account tokens, screenshots or findings
into a public GitHub repository. Keep local receipts with this exact SHA.
If the EXE changes, collect new receipts and repeat the actual checks.

CUSTOMER_RELEASE_READY=False
"@
# Write outputs only to the fresh local directory; no client data in either.
[System.IO.File]::WriteAllText(
    (Join-Path $outdir 'owner-manual-checklist.md'), $manual,
    [System.Text.UTF8Encoding]::new($false))
$json = $record | ConvertTo-Json -Depth 8
[System.IO.File]::WriteAllText(
    (Join-Path $outdir 'owner-preflight.json'), $json,
    [System.Text.UTF8Encoding]::new($false))
Write-Output 'OWNER_WINDOWS_ONECLICK_SYNTHETIC_PASS'
Write-Output ('EXE_SHA256=' + $initialSha)
Write-Output 'MANUAL_CHECKS=10_UNVERIFIED'
Write-Output 'CUSTOMER_RELEASE_READY=False'
