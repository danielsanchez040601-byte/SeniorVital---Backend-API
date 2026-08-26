$ErrorActionPreference = "Stop"
$rootDir = Split-Path -Parent $PSScriptRoot
$logDir = Join-Path $rootDir "logs"
$storageDirs = @(
    (Join-Path $rootDir "storage\videos"),
    (Join-Path $rootDir "storage\progress-photos")
)

# Create directories
foreach ($dir in $storageDirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "Created: $dir"
    }
}
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

function Start-ServiceProcess {
    param($Name, $Port, $Dir)
    $startScript = @"
import sys
sys.path.insert(0, "$rootDir")
import uvicorn
uvicorn.run("main:app", host="0.0.0.0", port=$Port)
"@
    $pidFile = Join-Path $logDir "$Name.pid"
    $logFile = Join-Path $logDir "$Name.log"
    $startJob = Start-Job -Name $Name -ScriptBlock {
        param($d, $p, $r, $s)
        Set-Location $d
        $env:PYTHONPATH = "$r;$env:PYTHONPATH"
        python -m uvicorn main:app --host 0.0.0.0 --port $p --reload *>&1 | Out-File -FilePath $s -Encoding utf8
    } -ArgumentList $Dir, $Port, $rootDir, $logFile
    $startJob.Id | Out-File -FilePath $pidFile -Encoding utf8
    Write-Host "Started $Name on port $Port (Job ID: $($startJob.Id))"
}

$services = @(
    @{Name="auth-profile"; Port=8001; Dir=(Join-Path $rootDir "auth-profile-service")},
    @{Name="catalog"; Port=8002; Dir=(Join-Path $rootDir "catalog-service")},
    @{Name="routines-ai"; Port=8003; Dir=(Join-Path $rootDir "routines-ai-service")},
    @{Name="tracking"; Port=8004; Dir=(Join-Path $rootDir "tracking-service")},
    @{Name="dashboard"; Port=8005; Dir=(Join-Path $rootDir "dashboard-service")},
    @{Name="notification"; Port=8006; Dir=(Join-Path $rootDir "notification-service")},
    @{Name="gateway"; Port=8000; Dir=(Join-Path $rootDir "gateway")}
)

foreach ($svc in $services) {
    Start-ServiceProcess -Name $svc.Name -Port $svc.Port -Dir $svc.Dir
    Start-Sleep -Seconds 5
}

Write-Host ""
Write-Host "All services started. PIDs saved in $logDir"
