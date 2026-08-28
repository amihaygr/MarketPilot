[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$BackupPath,
    [string]$TargetDatabase = "marketpilot_restore_drill",
    [switch]$Recreate
)

$ErrorActionPreference = "Stop"
if ($TargetDatabase -notmatch '^marketpilot_restore_[a-z0-9_]+$') {
    throw "TargetDatabase must start with marketpilot_restore_ and contain lowercase safe characters"
}

$repositoryRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$resolvedBackupPath = (Resolve-Path -LiteralPath $BackupPath).Path
$checksumPath = "$resolvedBackupPath.sha256"
if (-not (Test-Path -LiteralPath $checksumPath)) {
    throw "Backup checksum sidecar is missing: $checksumPath"
}
$expectedChecksum = ([System.IO.File]::ReadAllText($checksumPath).Split(' ', [System.StringSplitOptions]::RemoveEmptyEntries)[0]).ToLowerInvariant()
$actualChecksum = (Get-FileHash -Algorithm SHA256 -LiteralPath $resolvedBackupPath).Hash.ToLowerInvariant()
if ($actualChecksum -ne $expectedChecksum) {
    throw "Backup checksum verification failed"
}

$temporaryName = "marketpilot-restore-$([guid]::NewGuid().ToString('N')).sql.gz"
$containerPath = "/tmp/$temporaryName"
Push-Location $repositoryRoot
try {
    docker compose cp $resolvedBackupPath "mariadb:$containerPath"
    if ($LASTEXITCODE -ne 0) { throw "copying the backup into MariaDB failed" }

    if ($Recreate) {
        $prepareCommand = 'mariadb -uroot -p"$MARIADB_ROOT_PASSWORD" -e "DROP DATABASE IF EXISTS ' + $TargetDatabase + '; CREATE DATABASE ' + $TargetDatabase + ' CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"'
    }
    else {
        $prepareCommand = 'mariadb -uroot -p"$MARIADB_ROOT_PASSWORD" -e "CREATE DATABASE IF NOT EXISTS ' + $TargetDatabase + ' CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"'
    }
    docker compose exec -T mariadb sh -c $prepareCommand
    if ($LASTEXITCODE -ne 0) { throw "preparing the isolated restore database failed" }

    $restoreCommand = 'gzip -dc ' + $containerPath + ' | mariadb -uroot -p"$MARIADB_ROOT_PASSWORD" ' + $TargetDatabase
    docker compose exec -T mariadb sh -c $restoreCommand
    if ($LASTEXITCODE -ne 0) { throw "restoring the logical backup failed" }
    docker compose exec -T mariadb rm -f $containerPath
    if ($LASTEXITCODE -ne 0) { throw "cleaning the restore temporary file failed" }

    $countCommand = 'mariadb -N -uroot -p"$MARIADB_ROOT_PASSWORD" -D ' + $TargetDatabase + ' -e "SELECT COUNT(*) FROM fact_market_bar_1m; SELECT COUNT(*) FROM fact_sec_filing;"'
    $counts = docker compose exec -T mariadb sh -c $countCommand
    if ($LASTEXITCODE -ne 0) { throw "validating restored row counts failed" }
    [pscustomobject]@{
        TargetDatabase = $TargetDatabase
        ChecksumSha256 = $actualChecksum
        RestoredCounts = @($counts)
    }
}
finally {
    Pop-Location
}
