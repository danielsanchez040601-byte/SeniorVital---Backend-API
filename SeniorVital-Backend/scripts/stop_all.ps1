$logDir = Join-Path (Split-Path -Parent $PSScriptRoot) "logs"
if (Test-Path $logDir) {
    Get-ChildItem "$logDir\*.pid" | ForEach-Object {
        $pid = Get-Content $_.FullName
        Write-Host "Stopping $($_.BaseName) (Job ID: $pid)"
        try {
            Stop-Job -Id $pid -ErrorAction SilentlyContinue
            Remove-Job -Id $pid -Force -ErrorAction SilentlyContinue
        } catch {
            Write-Host "  Already stopped."
        }
        Remove-Item $_.FullName -Force -ErrorAction SilentlyContinue
    }
    # Also stop any lingering uvicorn processes on our ports
    $ports = @(8000,8001,8002,8003,8004,8005,8006)
    foreach ($port in $ports) {
        $conn = netstat -ano | Select-String ":$port "
        if ($conn) {
            foreach ($line in $conn) {
                $parts = $line.ToString().Trim().Split(" ", [StringSplitOptions]::RemoveEmptyEntries)
                if ($parts.Count -ge 5) {
                    $procId = $parts[-1]
                    try {
                        Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
                        Write-Host "Killed process $procId on port $port"
                    } catch {}
                }
            }
        }
    }
}
Write-Host "All services stopped."
