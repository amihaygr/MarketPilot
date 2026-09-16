[CmdletBinding()]
param(
    [switch]$OpenPages
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot

function Write-Check {
    param([string]$Name, [bool]$Passed, [string]$Detail)
    $status = if ($Passed) { "PASS" } else { "FAIL" }
    $color = if ($Passed) { "Green" } else { "Red" }
    Write-Host ("[{0}] {1} - {2}" -f $status, $Name, $Detail) -ForegroundColor $color
}

$failed = $false

try {
    docker compose config --quiet | Out-Null
    Write-Check "Compose configuration" $true "valid"
} catch {
    Write-Check "Compose configuration" $false $_.Exception.Message
    $failed = $true
}

$requiredServices = @(
    "kafka", "mariadb", "minio", "spark-master", "spark-worker",
    "spark-streaming", "airflow-scheduler", "airflow-api-server",
    "backend-api", "web-app"
)
try {
    $running = @(docker compose ps --status running --services)
    $missing = @($requiredServices | Where-Object { $_ -notin $running })
    $serviceDetail = if ($missing.Count -eq 0) {
        "all required services are running"
    } else {
        "missing: $($missing -join ', ')"
    }
    Write-Check "Core services" ($missing.Count -eq 0) $serviceDetail
    $failed = $failed -or ($missing.Count -gt 0)
} catch {
    Write-Check "Core services" $false $_.Exception.Message
    $failed = $true
}

$pages = [ordered]@{
    "Dashboard" = "http://localhost:3000/"
    "Opportunity Center" = "http://localhost:3000/opportunities.html"
    "Backtesting Lab" = "http://localhost:3000/backtesting.html"
    "Project Story" = "http://localhost:3000/showcase.html"
    "Kafka UI" = "http://localhost:8085/"
    "MinIO" = "http://localhost:9001/"
    "Airflow" = "http://localhost:8080/"
}

foreach ($entry in $pages.GetEnumerator()) {
    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri $entry.Value -TimeoutSec 10
        $passed = $response.StatusCode -eq 200
        Write-Check $entry.Key $passed ("HTTP {0}" -f $response.StatusCode)
        $failed = $failed -or (-not $passed)
    } catch {
        Write-Check $entry.Key $false $_.Exception.Message
        $failed = $true
    }
}

try {
    $shadow = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/decision-evaluation/status" -TimeoutSec 10
    Write-Check "Shadow Mode API" $true (
        "{0}/{1} sessions, status={2}, latest={3}" -f
        $shadow.completed_sessions,
        $shadow.required_sessions,
        $shadow.promotion_status,
        $shadow.latest_session_date
    )
} catch {
    Write-Check "Shadow Mode API" $false $_.Exception.Message
    $failed = $true
}

try {
    $dagList = docker compose exec -T airflow-scheduler airflow dags list -o json | ConvertFrom-Json
    $dailyDag = $dagList | Where-Object { $_.dag_id -eq "daily_market_close" }
    $active = $null -ne $dailyDag -and $dailyDag.is_paused -eq "False"
    $dagDetail = if ($active) { "active and available to the scheduler" } else { "paused or unavailable" }
    Write-Check "daily_market_close" $active $dagDetail
    $failed = $failed -or (-not $active)
} catch {
    Write-Check "daily_market_close" $false $_.Exception.Message
    $failed = $true
}

if ($OpenPages -and -not $failed) {
    foreach ($url in $pages.Values) {
        Start-Process $url
    }
}

if ($failed) {
    Write-Host "Demo preflight failed. Fix the red checks before presenting." -ForegroundColor Red
    exit 1
}

Write-Host "Demo preflight passed. The environment is ready for the read-only golden path." -ForegroundColor Green
