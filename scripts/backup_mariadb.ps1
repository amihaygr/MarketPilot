[CmdletBinding()]
param(
    [string]$BackupDirectory = "",
    [string]$ArchiveBucket = "marketpilot-archive",
    [switch]$SkipObjectStorageUpload
)

$ErrorActionPreference = "Stop"
if ($ArchiveBucket -notmatch '^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$') {
    throw "ArchiveBucket must be a valid lowercase S3 bucket name"
}
$repositoryRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
if ([string]::IsNullOrWhiteSpace($BackupDirectory)) {
    $BackupDirectory = Join-Path $repositoryRoot "tmp\backups"
}
$resolvedBackupDirectory = [System.IO.Path]::GetFullPath($BackupDirectory)
New-Item -ItemType Directory -Force -Path $resolvedBackupDirectory | Out-Null

$timestamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$fileName = "marketpilot-$timestamp.sql.gz"
$containerPath = "/tmp/$fileName"
$localPath = Join-Path $resolvedBackupDirectory $fileName

Push-Location $repositoryRoot
try {
    $dumpCommand = 'mariadb-dump --single-transaction --routines --triggers --events -uroot -p"$MARIADB_ROOT_PASSWORD" "$MARIADB_DATABASE" | gzip -9 > ' + $containerPath
    docker compose exec -T mariadb sh -c $dumpCommand
    if ($LASTEXITCODE -ne 0) { throw "mariadb-dump failed" }
    docker compose cp "mariadb:$containerPath" $localPath
    if ($LASTEXITCODE -ne 0) { throw "copying the backup from MariaDB failed" }
    docker compose exec -T mariadb rm -f $containerPath
    if ($LASTEXITCODE -ne 0) { throw "cleaning the MariaDB temporary backup failed" }

    $checksum = (Get-FileHash -Algorithm SHA256 -LiteralPath $localPath).Hash.ToLowerInvariant()
    $checksumPath = "$localPath.sha256"
    [System.IO.File]::WriteAllText($checksumPath, "$checksum  $fileName`n")

    $objectUri = $null
    if (-not $SkipObjectStorageUpload) {
        docker compose cp $localPath "minio:/tmp/$fileName"
        if ($LASTEXITCODE -ne 0) { throw "copying the backup to MinIO failed" }
        docker compose cp $checksumPath "minio:/tmp/$fileName.sha256"
        if ($LASTEXITCODE -ne 0) { throw "copying the checksum to MinIO failed" }
        $uploadCommand = 'mc alias set phase8 http://localhost:9000 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD" >/dev/null && mc mb --ignore-existing phase8/' + $ArchiveBucket + ' >/dev/null && mc cp /tmp/' + $fileName + ' phase8/' + $ArchiveBucket + '/backups/mariadb/' + $fileName + ' >/dev/null && mc cp /tmp/' + $fileName + '.sha256 phase8/' + $ArchiveBucket + '/backups/mariadb/' + $fileName + '.sha256 >/dev/null && rm -f /tmp/' + $fileName + ' /tmp/' + $fileName + '.sha256'
        docker compose exec -T minio sh -c $uploadCommand
        if ($LASTEXITCODE -ne 0) { throw "uploading the backup to the archive bucket failed" }
        $objectUri = "s3a://$ArchiveBucket/backups/mariadb/$fileName"
    }

    [pscustomobject]@{
        BackupPath = $localPath
        ChecksumPath = $checksumPath
        ChecksumSha256 = $checksum
        ObjectUri = $objectUri
    }
}
finally {
    Pop-Location
}
