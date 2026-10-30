# Read-only Windows acceptance inventory for an EXISTING unsigned developer EXE.
# No registry/Defender/firewall/SmartScreen settings changed. No network tool,
# packet capture or source scan. Runs ONLY when explicitly invoked.
# Does NOT certify retail-machine safety or approve redistribution.
param(
    [Parameter(Mandatory=$true)][string]$ExePath,
    [Parameter(Mandatory=$true)][string]$OutputPath
)
$ErrorActionPreference = 'Stop'
if ($env:OS -ne 'Windows_NT') { throw 'Windows is required.' }
if ([string]::IsNullOrWhiteSpace($ExePath) -or [string]::IsNullOrWhiteSpace($OutputPath)) {
    throw 'Both paths are required.'
}
# Read-only volume and parent checks: a drive-letter path can still be
# a mapped network share. Do not follow junction/symlink parents.
function Assert-LocalPath([string]$RawPath) {
    if ([string]::IsNullOrWhiteSpace($RawPath) -or
        $RawPath.StartsWith('\\') -or $RawPath.StartsWith('//')) {
        throw 'UNC or device paths are not accepted.'
    }
    $full = [System.IO.Path]::GetFullPath($RawPath)
    $root = [System.IO.Path]::GetPathRoot($full)
    if ([string]::IsNullOrWhiteSpace($root) -or
        $root.StartsWith('\\') -or $root.StartsWith('//')) {
        throw 'Local filesystem volume required.'
    }
    $drive = [System.IO.DriveInfo]::new($root)
    if ($drive.DriveType.ToString() -notin @('Fixed', 'Removable', 'Ram')) {
        throw 'Remote or unknown filesystem volume is not allowed.'
    }
    $cursor = [System.IO.Path]::GetDirectoryName($full)
    while (-not [string]::IsNullOrWhiteSpace($cursor)) {
        $item = Get-Item -LiteralPath $cursor -Force -ErrorAction Stop
        if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw 'Reparse or linked parent is not allowed.'
        }
        $next = [System.IO.Path]::GetDirectoryName($cursor)
        if ([string]::IsNullOrWhiteSpace($next) -or $next -eq $cursor) { break }
        $cursor = $next
    }
    return $full
}
$exeFull = Assert-LocalPath $ExePath
$outFull = Assert-LocalPath $OutputPath
$exe = Get-Item -LiteralPath $exeFull -ErrorAction Stop
if (-not ($exe -is [System.IO.FileInfo]) -or $exe.Extension -ine '.exe' -or
    $exe.Length -le 0 -or $exe.Length -gt 268435456 -or
    (($exe.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0)) {
    throw 'Expected an existing regular local EXE, no links, maximum 256 MiB.'
}
$parent = Split-Path -Parent $outFull
if (-not [System.IO.Directory]::Exists($parent)) {
    throw 'Existing local evidence destination folder required.'
}
$parentItem = Get-Item -LiteralPath $parent
if (($parentItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
    throw 'Evidence output directory cannot be a reparse point.'
}
$outFile = $outFull
if ([System.IO.File]::Exists($outFile) -or [System.IO.Directory]::Exists($outFile)) {
    throw 'No overwrite of previous evidence is allowed.'
}

$hash = (Get-FileHash -LiteralPath $exe.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
$signature = 'Unavailable'
try {
    $sig = Get-AuthenticodeSignature -LiteralPath $exe.FullName -ErrorAction Stop
    $observed = [string]$sig.Status
    if ($observed -eq 'Valid' -or $observed -eq 'NotSigned') {
        $signature = $observed
    } else {
        $signature = 'Other'
    }
} catch {
    $signature = 'Unavailable'
}

$defenderStatus = 'UNVERIFIED'
$antivirusEnabled = $null
$realtimeEnabled = $null
# Defender's WMI/service status query can block indefinitely on some hosted
# Windows builds. Run only the fixed, read-only query in a bounded child pwsh,
# never in this evidence writer. A timeout stays UNVERIFIED (not disabled).
$probe = [System.Diagnostics.Process]::new()
try {
    $start = [System.Diagnostics.ProcessStartInfo]::new()
    $start.FileName = [System.Diagnostics.Process]::GetCurrentProcess().MainModule.FileName
    $start.UseShellExecute = $false
    $start.CreateNoWindow = $true
    $start.RedirectStandardOutput = $true
    $start.RedirectStandardError = $true
    foreach ($arg in @('-NoProfile', '-NonInteractive', '-Command')) {
        [void]$start.ArgumentList.Add($arg)
    }
    $query = @'
$ErrorActionPreference = 'Stop'
try {
    $mp = Get-MpComputerStatus -ErrorAction Stop
    if ($null -eq $mp -or $null -eq $mp.AntivirusEnabled -or $null -eq $mp.RealTimeProtectionEnabled) { exit 2 }
    $antivirus = [bool]$mp.AntivirusEnabled
    $realtime = [bool]$mp.RealTimeProtectionEnabled
    Write-Output "$antivirus,$realtime"
    exit 0
} catch { exit 2 }
'@
    [void]$start.ArgumentList.Add($query)
    $probe.StartInfo = $start
    if ($probe.Start()) {
        if ($probe.WaitForExit(10000)) {
            $observed = $probe.StandardOutput.ReadToEnd().Trim()
            if ($probe.ExitCode -eq 0 -and $observed -cmatch '^(True|False),(True|False)$') {
                $defenderStatus = 'OBSERVED'
                $antivirusEnabled = ($Matches[1] -ceq 'True')
                $realtimeEnabled = ($Matches[2] -ceq 'True')
            }
        } else {
            # Stop only the exact status-query child, not Defender or other
            # Windows processes. The absence of observation is not PASS/FAIL.
            try { $probe.Kill() } catch { }
            try { [void]$probe.WaitForExit(2000) } catch { }
        }
    }
} catch {
    $defenderStatus = 'UNVERIFIED'
    $antivirusEnabled = $null
    $realtimeEnabled = $null
} finally {
    $probe.Dispose()
}

$evidence = [ordered]@{
    format = 'code_checker_readonly_windows_acceptance_v1'
    collection_method = 'win32_readonly_powershell'
    scope = 'local_binary_only'
    exe_sha256 = $hash
    exe_bytes = [int64]$exe.Length
    signature_observation = $signature
    defender = [ordered]@{
        availability = $defenderStatus
        antivirus_enabled = $antivirusEnabled
        real_time_protection_enabled = $realtimeEnabled
    }
    pending_gates = [ordered]@{
        retail_windows_user_acceptance = 'UNVERIFIED'
        smartscreen_reputation = 'UNVERIFIED'
        os_packet_capture = 'UNVERIFIED'
        defender_exe_scan = 'UNVERIFIED'
        korean_pdf_visual = 'UNVERIFIED'
        third_party_legal_notice = 'UNVERIFIED'
    }
    customer_release_ready = $false
    legal_notice_approved = $false
}
$serialized = $evidence | ConvertTo-Json -Depth 6
# CreateNew: no overwriting old receipts or modifying any input files.
$stream = [System.IO.File]::Open($outFile, [System.IO.FileMode]::CreateNew,
    [System.IO.FileAccess]::Write, [System.IO.FileShare]::None)
try {
    $writer = [System.IO.StreamWriter]::new($stream, [System.Text.UTF8Encoding]::new($false))
    try { $writer.Write($serialized); $writer.Flush() }
    finally { $writer.Dispose() }
} finally {
    $stream.Dispose()
}
Write-Output 'WINDOWS_ACCEPTANCE_LOCAL_READONLY_CAPTURED'
Write-Output 'BINARY_SHA256_CAPTURED=True'
Write-Output "DEFENDER_SETTINGS_OBSERVED=$($defenderStatus -eq 'OBSERVED')"
Write-Output 'DEFENDER_FILE_SCAN=UNVERIFIED'
Write-Output 'OS_PACKET_CAPTURE=UNVERIFIED'
Write-Output 'SMARTSCREEN_REPUTATION=UNVERIFIED'
Write-Output 'CUSTOMER_RELEASE_READY=False'
