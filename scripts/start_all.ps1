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
    $pidFile = Join-Path $logDir "$Name.pid"
    $logFile = Join-Path $logDir "$Name.log"
    $errFile = Join-Path $logDir "$Name.err.log"
    $powershellArg = "-NoProfile -Command `"`$env:PYTHONPATH = '$rootDir'; cd '$Dir'; & '$rootDir/venv/Scripts/python.exe' -m uvicorn main:app --host 0.0.0.0 --port $Port --reload`""
    $proc = Start-Process -FilePath "powershell.exe" -ArgumentList $powershellArg -PassThru -WindowStyle Hidden -RedirectStandardOutput $logFile -RedirectStandardError $errFile
    $proc.Id | Out-File -FilePath $pidFile -Encoding utf8
    Write-Host "Started $Name on port $Port (PID: $($proc.Id))"
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
