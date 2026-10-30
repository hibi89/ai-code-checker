# Run an EXISTING Code Checker Windows EXE with synthetic, offline GUI smoke modes.
# No Python, package installation, API calls, source extraction, Defender setting
# change, firewall change, elevated permission, or customer files are required.
# This is NOT a clean consumer OS, packet-capture, SmartScreen or legal signoff.
param(
    [Parameter(Mandatory=$true)][string]$ExePath,
    [Parameter(Mandatory=$true)][string]$OutputPath,
    [ValidateRange(15,180)][int]$TimeoutSeconds = 120
)
$ErrorActionPreference = 'Stop'
if ($env:OS -ne 'Windows_NT') { throw 'Windows host required.' }

function Assert-LocalPath([string]$RawPath) {
    if ([string]::IsNullOrWhiteSpace($RawPath) -or
        $RawPath.StartsWith('\\') -or $RawPath.StartsWith('//')) {
        throw 'UNC, network device or blank path rejected.'
    }
    $full = [System.IO.Path]::GetFullPath($RawPath)
    $root = [System.IO.Path]::GetPathRoot($full)
    if ([string]::IsNullOrWhiteSpace($root) -or
        $root.StartsWith('\\') -or $root.StartsWith('//')) {
        throw 'Local filesystem volume required.'
    }
    $drive = [System.IO.DriveInfo]::new($root)
    if ($drive.DriveType.ToString() -notin @('Fixed', 'Removable', 'Ram')) {
        throw 'Remote or unsupported volume rejected.'
    }
    $cursor = [System.IO.Path]::GetDirectoryName($full)
    while (-not [string]::IsNullOrWhiteSpace($cursor)) {
        $item = Get-Item -LiteralPath $cursor -Force -ErrorAction Stop
        if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw 'Linked or junction ancestor rejected.'
        }
        $next = [System.IO.Path]::GetDirectoryName($cursor)
        if ([string]::IsNullOrWhiteSpace($next) -or $next -eq $cursor) { break }
        $cursor = $next
    }
    return $full
}

$exeFull = Assert-LocalPath $ExePath
$outFull = Assert-LocalPath $OutputPath
$exe = Get-Item -LiteralPath $exeFull -Force -ErrorAction Stop
if (-not ($exe -is [System.IO.FileInfo]) -or $exe.Extension -ine '.exe' -or
    $exe.Length -le 0 -or $exe.Length -gt 268435456 -or
    (($exe.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0)) {
    throw 'A regular local EXE <= 256 MiB is required.'
}
if ([System.IO.Path]::GetExtension($outFull) -ine '.json') {
    throw 'Evidence filename must end with .json.'
}
if ([System.IO.File]::Exists($outFull) -or
    [System.IO.Directory]::Exists($outFull) -or
    $outFull -eq $exeFull) {
    throw 'Refuse to overwrite or alias any existing evidence.'
}
$parent = Split-Path -Parent $outFull
if (-not [System.IO.Directory]::Exists($parent)) {
    throw 'The evidence output parent must already exist.'
}
$beforeHash = (Get-FileHash -LiteralPath $exeFull -Algorithm SHA256).Hash.ToLowerInvariant()
$beforeBytes = [int64]$exe.Length

function Invoke-SyntheticSmoke([string]$Option) {
    # The only permitted arguments are built-in Code Checker test modes.
    if ($Option -notin @('--gui-smoke', '--scenario-smoke')) {
        throw 'Unexpected test mode.'
    }
    $settings = [System.Diagnostics.ProcessStartInfo]::new()
    $settings.FileName = $exeFull
    $settings.Arguments = $Option
    $settings.WorkingDirectory = [System.IO.Path]::GetDirectoryName($exeFull)
    $settings.UseShellExecute = $false
    $settings.CreateNoWindow = $true
    $proc = [System.Diagnostics.Process]::new()
    try {
        $proc.StartInfo = $settings
        if (-not $proc.Start()) { throw 'Cannot start synthetic GUI mode.' }
        if (-not $proc.WaitForExit($TimeoutSeconds * 1000)) {
            # Only the exact process started above is terminated.
            try { $proc.Kill() } catch { }
            try { [void]$proc.WaitForExit(5000) } catch { }
            throw 'Synthetic GUI mode exceeded the bounded timeout.'
        }
        if ($proc.ExitCode -ne 0) {
            throw ('Synthetic GUI mode returned nonzero exit: ' + $Option)
        }
    } finally {
        $proc.Dispose()
    }
}

# GUI init and complete preview -> scan -> report are separate, bounded runs.
# No untrusted customer source or URL is passed into the EXE.
Invoke-SyntheticSmoke '--gui-smoke'
Invoke-SyntheticSmoke '--scenario-smoke'

$after = Get-Item -LiteralPath $exeFull -Force -ErrorAction Stop
$afterHash = (Get-FileHash -LiteralPath $exeFull -Algorithm SHA256).Hash.ToLowerInvariant()
if ($after.Length -ne $beforeBytes -or $afterHash -ne $beforeHash -or
    (($after.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0)) {
    throw 'EXE changed during synthetic local validation.'
}

$record = [ordered]@{
    format = 'code_checker_windows_local_exe_smoke_v1'
    collection_method = 'two_synthetic_exe_modes_no_python_required'
    scope = 'existing_local_exe_only'
    exe_sha256 = $beforeHash
    exe_bytes = $beforeBytes
    observed_synthetic = [ordered]@{
        packaged_tk_gui_startup = 'PASS'
        packaged_preview_scan_report = 'PASS'
        executable_hash_stable = $true
    }
    pending_gates = [ordered]@{
        clean_consumer_windows = 'UNVERIFIED'
        interactive_human_gui = 'UNVERIFIED'
        smartscreen_reputation = 'UNVERIFIED'
        defender_customer_acceptance = 'UNVERIFIED'
        os_packet_capture = 'UNVERIFIED'
        korean_pdf_visual = 'UNVERIFIED'
        third_party_license_notice = 'UNVERIFIED'
    }
    actual_customer_code_used = $false
    actual_customer_release_ready = $false
    legal_notice_approved = $false
}
# CreateNew prevents clobber; a previous run must be kept for audit.
$json = $record | ConvertTo-Json -Depth 7
$stream = [System.IO.File]::Open($outFull, [System.IO.FileMode]::CreateNew,
    [System.IO.FileAccess]::Write, [System.IO.FileShare]::None)
try {
    $writer = [System.IO.StreamWriter]::new($stream, [System.Text.UTF8Encoding]::new($false))
    try { $writer.Write($json); $writer.Flush() }
    finally { $writer.Dispose() }
} finally {
    $stream.Dispose()
}
Write-Output 'WINDOWS_LOCAL_EXE_SYNTHETIC_PASS'
Write-Output 'GUI_STARTUP_AND_PREVIEW_SCAN_REPORT=PASS'
Write-Output 'EXE_SHA256=' $beforeHash
Write-Output 'CLEAN_CONSUMER_WINDOWS=UNVERIFIED'
Write-Output 'SMARTSCREEN_OS_PACKET_PDF_NOTICE=UNVERIFIED'
Write-Output 'CUSTOMER_RELEASE_READY=False'
