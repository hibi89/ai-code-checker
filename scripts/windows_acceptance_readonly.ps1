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
if ($ExePath.StartsWith('\\') -or $ExePath.StartsWith('//') -or
    $OutputPath.StartsWith('\\') -or $OutputPath.StartsWith('//')) {
    throw 'UNC or device paths are not accepted.'
}
$exe = Get-Item -LiteralPath $ExePath -ErrorAction Stop
if (-not ($exe -is [System.IO.FileInfo]) -or $exe.Extension -ine '.exe' -or
    $exe.Length -le 0 -or $exe.Length -gt 268435456 -or
    (($exe.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0)) {
    throw 'Expected an existing regular local EXE, no links, maximum 256 MiB.'
}
$parent = Split-Path -Parent ([System.IO.Path]::GetFullPath($OutputPath))
if (-not [System.IO.Directory]::Exists($parent)) {
    throw 'Existing local evidence destination folder required.'
}
$parentItem = Get-Item -LiteralPath $parent
if (($parentItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
    throw 'Evidence output directory cannot be a reparse point.'
}
$outFile = [System.IO.Path]::GetFullPath($OutputPath)
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
try {
    $mp = Get-MpComputerStatus -ErrorAction Stop
    if ($null -ne $mp -and $null -ne $mp.AntivirusEnabled -and
        $null -ne $mp.RealTimeProtectionEnabled) {
        $defenderStatus = 'OBSERVED'
        $antivirusEnabled = [bool]$mp.AntivirusEnabled
        $realtimeEnabled = [bool]$mp.RealTimeProtectionEnabled
    }
} catch {
    # No third-party AV claims, no inference from missing Defender cmdlet.
    $defenderStatus = 'UNVERIFIED'
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
