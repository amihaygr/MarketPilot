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

function Invoke-JsonApi {
    param([string]$Name, [string]$Uri)
    try {
        $value = Invoke-RestMethod -Uri $Uri -TimeoutSec 15
        Write-Check $Name $true "responded"
        return $value
    }
    catch {
        Write-Check $Name $false $_.Exception.Message
        $script:failed = $true
        return $null
    }
}

$failed = $false
Write-Host "MarketPilot demo preflight" -ForegroundColor Cyan
Write-Host "Project: $projectRoot"

try {
    docker compose config --quiet | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "docker compose config returned $LASTEXITCODE" }
    Write-Check "Compose configuration" $true "valid"
}
catch {
    Write-Check "Compose configuration" $false $_.Exception.Message
    $failed = $true
}

$requiredServices = @(
    "kafka", "mariadb", "minio", "market-producer", "raw-archive-sink",
    "spark-master", "spark-worker", "spark-streaming", "spark-ui-proxy",
    "airflow-db", "airflow-scheduler", "airflow-api-server", "airflow-dag-processor",
    "backend-api", "web-app", "operational-monitor", "kafka-ui", "adminer"
)
try {
    $containers = @(docker compose ps --format json | ConvertFrom-Json)
    if ($LASTEXITCODE -ne 0) { throw "docker compose ps returned $LASTEXITCODE" }
    $problems = @()
    foreach ($service in $requiredServices) {
        $container = $containers | Where-Object { $_.Service -eq $service } | Select-Object -First 1
        if ($null -eq $container) {
            $problems += "$service missing"
            continue
        }
        if ($container.State -ne "running") {
            $problems += "$service state=$($container.State)"
            continue
        }
        if ($container.Health -and $container.Health -ne "healthy") {
            $problems += "$service health=$($container.Health)"
        }
    }
    $detail = if ($problems.Count -eq 0) {
        "$($requiredServices.Count) required runtime services are running and healthy"
    }
    else {
        $problems -join "; "
    }
    Write-Check "Docker runtime" ($problems.Count -eq 0) $detail
    $failed = $failed -or ($problems.Count -gt 0)
}
catch {
    Write-Check "Docker runtime" $false $_.Exception.Message
    $failed = $true
}

$pages = [ordered]@{
    "Dashboard" = "http://localhost:3000/"
    "Opportunity Center" = "http://localhost:3000/opportunities.html"
    "Backtesting Lab" = "http://localhost:3000/backtesting.html"
    "Project Story" = "http://localhost:3000/showcase.html"
    "Presenter Console" = "http://localhost:3000/presenter.html"
    "Kafka UI" = "http://localhost:8085/"
    "MinIO Console" = "http://localhost:9001/"
    "Airflow" = "http://localhost:8080/"
    "Spark Master" = "http://localhost:18080/"
    "Spark Worker" = "http://localhost:18081/"
    "Adminer" = "http://localhost:8086/"
    "Backend API docs" = "http://localhost:8000/docs"
}

foreach ($entry in $pages.GetEnumerator()) {
    try {
        $statusCode = & curl.exe --silent --show-error --output NUL --write-out "%{http_code}" --max-time 12 $entry.Value
        if ($LASTEXITCODE -ne 0) { throw "curl returned $LASTEXITCODE" }
        $passed = [string]$statusCode -eq "200"
        Write-Check $entry.Key $passed ("HTTP {0}" -f $statusCode)
        $failed = $failed -or (-not $passed)
    }
    catch {
        Write-Check $entry.Key $false $_.Exception.Message
        $failed = $true
    }
}

$live = Invoke-JsonApi "API liveness" "http://localhost:8000/health/live"
$ready = Invoke-JsonApi "API readiness" "http://localhost:8000/health/ready"
$freshness = Invoke-JsonApi "Freshness evidence" "http://localhost:8000/api/v1/freshness"
$symbols = Invoke-JsonApi "Symbol catalogue" "http://localhost:8000/api/v1/symbols"
$opportunities = Invoke-JsonApi "Opportunity catalogue" "http://localhost:8000/api/v1/opportunities"
$shadow = Invoke-JsonApi "Shadow Mode status" "http://localhost:8000/api/v1/decision-evaluation/status"
$model = Invoke-JsonApi "Hybrid model status" "http://localhost:8000/api/v1/decision-model/status"
$backtests = Invoke-JsonApi "Published backtests" "http://localhost:8000/api/v1/backtests?page=1&page_size=1"

if ($ready -and $ready.status -ne "ready") {
    Write-Check "API readiness state" $false "status=$($ready.status)"
    $failed = $true
}

if ($freshness -and $symbols -and $opportunities -and $shadow -and $model -and $backtests) {
    $symbolCount = @($symbols.items).Count
    $opportunityCount = @($opportunities.items).Count
    $certifiedBars = [int64]$freshness.market.certified_count
    $historySessions = [int]$shadow.historical_certified_sessions
    $publishedBacktests = [int]$shadow.published_backtest_runs
    $evidencePassed = $symbolCount -ge 11 -and $opportunityCount -ge 11 -and $certifiedBars -gt 0 -and $historySessions -gt 0 -and $publishedBacktests -gt 0
    Write-Check "Presentation evidence" $evidencePassed (
        "symbols={0}, opportunities={1}, certified_bars={2}, history_sessions={3}, backtests={4}" -f
        $symbolCount, $opportunityCount, $certifiedBars, $historySessions, $publishedBacktests
    )
    $failed = $failed -or (-not $evidencePassed)

    Write-Check "Decision release state" $true (
        "v1={0}/{1} ({2}), v2={3}; FALLBACK is expected until a trained model passes validation" -f
        $shadow.completed_sessions,
        $shadow.required_sessions,
        $shadow.promotion_status,
        $model.status
    )
}

try {
    $localEnv = @{}
    foreach ($line in Get-Content -LiteralPath (Join-Path $projectRoot ".env")) {
        if ($line -match '^\s*([^#][^=]*)=(.*)$') {
            $localEnv[$matches[1].Trim()] = $matches[2].Trim()
        }
    }
    $authPayload = @{
        username = $localEnv["AIRFLOW_ADMIN_USERNAME"]
        password = $localEnv["AIRFLOW_ADMIN_PASSWORD"]
    } | ConvertTo-Json -Compress
    # Invoke-RestMethod preserves JSON quoting and special characters in local
    # credentials. curl.exe on Windows may reinterpret --data-raw and produce a
    # malformed request body even when the credentials themselves are valid.
    $tokenResponse = Invoke-RestMethod -Method Post `
        -Uri "http://localhost:8080/auth/token" `
        -ContentType "application/json" `
        -Body $authPayload `
        -TimeoutSec 12
    $airflowToken = $tokenResponse.access_token
    if (-not $airflowToken) { throw "Airflow did not return an access token" }

    $authorization = "Authorization: Bearer $airflowToken"
    $dailyDag = (& curl.exe --silent --show-error --max-time 12 `
        --header $authorization "http://localhost:8080/api/v2/dags/daily_market_close") | ConvertFrom-Json
    if ($LASTEXITCODE -ne 0) { throw "Airflow DAG request returned $LASTEXITCODE" }
    $active = $null -ne $dailyDag -and ([string]$dailyDag.is_paused).ToLowerInvariant() -eq "false"
    $dagDetail = if ($active) { "active and available to the scheduler" } else { "paused or unavailable" }
    Write-Check "daily_market_close" $active $dagDetail
    $failed = $failed -or (-not $active)

    $importErrors = (& curl.exe --silent --show-error --max-time 12 `
        --header $authorization "http://localhost:8080/api/v2/importErrors?limit=1") | ConvertFrom-Json
    if ($LASTEXITCODE -ne 0) { throw "Airflow import-error request returned $LASTEXITCODE" }
    $importCount = [int]$importErrors.total_entries
    $importDetail = if ($importCount -eq 0) { "no import errors" } else { "$importCount import errors" }
    Write-Check "Airflow DAG imports" ($importCount -eq 0) $importDetail
    $failed = $failed -or ($importCount -gt 0)
}
catch {
    Write-Check "Airflow scheduler" $false $_.Exception.Message
    $failed = $true
}

Write-Host ""
if ($failed) {
    Write-Host "Demo preflight failed. Fix every red check before presenting." -ForegroundColor Red
    exit 1
}

Write-Host "Demo preflight passed. The read-only golden path is ready." -ForegroundColor Green
Write-Host "Recommended order: Project Story -> Dashboard -> Kafka -> MinIO -> Airflow -> Opportunity Center -> Backtesting."

if ($OpenPages) {
    foreach ($url in $pages.Values) {
        Start-Process $url
    }
}
