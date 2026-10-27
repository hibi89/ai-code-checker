# Optional developer/CI Microsoft Defender custom file scan evidence.
# Explicit invocation only. No signature update, OS setting changes, EXE
# execution, remote upload or release authorization. A zero command exit is
# NOT proof that the executable is malware-free.
param(
    [Parameter(Mandatory=$true)][string]$ExePath,
    [Parameter(Mandatory=$true)][string]$OutputPath,
    [ValidateRange(30,300)][int]$TimeoutSeconds = 120
)
$ErrorActionPreference = 'Stop'
if ($env:OS -ne 'Windows_NT' -or $PSVersionTable.PSVersion.Major -lt 7) {
    throw 'Windows PowerShell 7+ is required.'
}
function Assert-LocalPath([string]$RawPath) {
    if ([string]::IsNullOrWhiteSpace($RawPath) -or $RawPath.Contains([char]0) -or
        $RawPath.StartsWith('\\') -or $RawPath.StartsWith('//')) {
        throw 'A local non-UNC path is required.'
    }
    $path = [System.IO.Path]::GetFullPath($RawPath)
    $root = [System.IO.Path]::GetPathRoot($path)
    if ($root.StartsWith('\\') -or $root.StartsWith('//')) {
        throw 'Network paths are not allowed.'
    }
    $drive = [System.IO.DriveInfo]::new($root)
    if ($drive.DriveType.ToString() -notin @('Fixed', 'Removable', 'Ram')) {
        throw 'Only a local filesystem volume is permitted.'
    }
    $cursor = [System.IO.Path]::GetDirectoryName($path)
    while ($cursor) {
        $info = Get-Item -LiteralPath $cursor -ErrorAction Stop
        if (($info.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw 'Linked or reparse parent directories are not accepted.'
        }
        $next = [System.IO.Path]::GetDirectoryName($cursor)
        if ([string]::IsNullOrWhiteSpace($next) -or $next -eq $cursor) { break }
        $cursor = $next
    }
    return $path
}
$exeFull = Assert-LocalPath $ExePath
$outputFull = Assert-LocalPath $OutputPath
$exe = Get-Item -LiteralPath $exeFull -ErrorAction Stop
if (-not ($exe -is [System.IO.FileInfo]) -or $exe.Extension -ine '.exe' -or
    $exe.Length -le 0 -or $exe.Length -gt 268435456 -or
    (($exe.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0)) {
    throw 'An existing regular local EXE of maximum 256 MiB is required.'
}
if ([System.IO.File]::Exists($outputFull) -or [System.IO.Directory]::Exists($outputFull)) {
    throw 'Evidence file already exists; overwrite is forbidden.'
}
$exeHash = (Get-FileHash -LiteralPath $exeFull -Algorithm SHA256).Hash.ToLowerInvariant()
$availability = 'UNVERIFIED'
try {
    $mp = Get-MpComputerStatus -ErrorAction Stop
    if ($null -ne $mp -and $null -ne $mp.AntivirusEnabled) {
        $availability = if ($mp.AntivirusEnabled -eq $true) { 'ENABLED' } else { 'DISABLED' }
    }
} catch {
    $availability = 'UNVERIFIED'
}
$scanner = $null
$platformRoot = Join-Path $env:ProgramData 'Microsoft\Windows Defender\Platform'
if (Test-Path -LiteralPath $platformRoot -PathType Container) {
    $versions = @(Get-ChildItem -LiteralPath $platformRoot -Directory -ErrorAction SilentlyContinue |
        Sort-Object Name -Descending | Select-Object -First 16)
    foreach ($version in $versions) {
        $candidate = Join-Path $version.FullName 'MpCmdRun.exe'
        if (Test-Path -LiteralPath $candidate -PathType Leaf) {
            $scanner = Get-Item -LiteralPath $candidate
            break
        }
    }
}
if ($null -eq $scanner) {
    $fallback = Join-Path $env:ProgramFiles 'Windows Defender\MpCmdRun.exe'
    if (Test-Path -LiteralPath $fallback -PathType Leaf) {
        $scanner = Get-Item -LiteralPath $fallback
    }
}
if ($null -ne $scanner -and
    (($scanner.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0)) {
    $scanner = $null
}
$scannerAvailable = $null -ne $scanner
$attempted = $false
$status = 'UNVERIFIED'
$exitCode = $null
if ($availability -eq 'ENABLED' -and $scannerAvailable) {
    $process = [System.Diagnostics.Process]::new()
    try {
        $psi = [System.Diagnostics.ProcessStartInfo]::new()
        $psi.FileName = $scanner.FullName
        foreach ($arg in @('-Scan', '-ScanType', '3', '-File', $exeFull, '-DisableRemediation')) {
            [void]$psi.ArgumentList.Add($arg)
        }
        $psi.UseShellExecute = $false
        $psi.CreateNoWindow = $true
        # Drain native command output without printing candidate paths or findings
        # in a public repository's CI logs. No files/network receipt emitted.
        $psi.RedirectStandardOutput = $true
        $psi.RedirectStandardError = $true
        $process.StartInfo = $psi
        if ($process.Start()) {
            $attempted = $true
            $null = $process.StandardOutput.ReadToEndAsync()
            $null = $process.StandardError.ReadToEndAsync()
            if ($process.WaitForExit($TimeoutSeconds * 1000)) {
                $exitCode = [int]$process.ExitCode
                $status = if ($exitCode -eq 0) { 'ZERO_EXIT' } else { 'NONZERO_EXIT' }
            } else {
                $status = 'TIMEOUT'
                try { $process.Kill() } catch { }
                try { [void]$process.WaitForExit(5000) } catch { }
            }
        }
    } catch {
        # Missing privileges/disabled Defender/service errors stay unverified.
        if (-not $attempted) { $status = 'UNVERIFIED' }
        else { $status = 'SCAN_ERROR' }
    } finally {
        $process.Dispose()
    }
}
# Defender may quarantine/mutate a file independent of no-remediation CLI
# switches; any missing or changed EXE fails the evidence integrity gate.
$unchanged = $false
try {
    $after = Get-Item -LiteralPath $exeFull -ErrorAction Stop
    $afterHash = (Get-FileHash -LiteralPath $exeFull -Algorithm SHA256).Hash.ToLowerInvariant()
    $unchanged = ($after.Length -eq $exe.Length -and $afterHash -eq $exeHash)
} catch { $unchanged = $false }
if (-not $unchanged) { $status = 'EXE_CHANGED' }
$receipt = [ordered]@{
    format = 'code_checker_defender_file_scan_v1'
    collection_method = 'local_mpcmdrun_custom_file_scan_no_remediation'
    scope = 'local_developer_or_hosted_windows_binary_only'
    exe_sha256 = $exeHash
    exe_bytes = [int64]$exe.Length
    defender_availability = $availability
    scanner_available = [bool]$scannerAvailable
    scan_attempted = [bool]$attempted
    scan_command_status = $status
    command_exit_code = $exitCode
    exe_unchanged = [bool]$unchanged
    malware_free_certified = $false
    retail_defender_acceptance = 'UNVERIFIED'
    customer_release_ready = $false
}
# CreateNew prevents replacing previous evidence; receipt contains no machine,
# source, user, full path, malware names or command stdout.
$serialized = $receipt | ConvertTo-Json -Depth 4
$stream = [System.IO.File]::Open($outputFull, [System.IO.FileMode]::CreateNew,
    [System.IO.FileAccess]::Write, [System.IO.FileShare]::None)
try {
    $writer = [System.IO.StreamWriter]::new($stream, [System.Text.UTF8Encoding]::new($false))
    try { $writer.Write($serialized); $writer.Flush() }
    finally { $writer.Dispose() }
} finally { $stream.Dispose() }
Write-Output 'DEFENDER_SCAN_LOCAL_RECEIPT_CAPTURED'
Write-Output "DEFENDER_SCAN_COMMAND_STATUS=$status"
Write-Output "DEFENDER_SCAN_ATTEMPTED=$attempted"
Write-Output 'MALWARE_FREE_CERTIFIED=False'
Write-Output 'RETAIL_DEFENDER_ACCEPTANCE=UNVERIFIED'
Write-Output 'CUSTOMER_RELEASE_READY=False'
