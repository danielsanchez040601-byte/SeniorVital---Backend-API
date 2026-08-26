# Script de Inicialización y Arranque de SeniorVital
$ErrorActionPreference = "Stop"

$rootDir = $PSScriptRoot
$backendDir = Join-Path $rootDir "SeniorVital-Backend"
$frontendDir = Join-Path $rootDir "seniorvital-frontend"
$venvPython = Join-Path $backendDir "venv\Scripts\python.exe"

Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host "              INICIALIZADOR DEL ECOSISTEMA SENIOR VITAL            " -ForegroundColor Cyan
Write-Host "==================================================================" -ForegroundColor Cyan

# 1. Verificar dependencias obligatorias
Write-Host "1. Verificando servicios requeridos..." -ForegroundColor Cyan

# Verificar PostgreSQL
$pgConnection = Test-Connection -ComputerName "localhost" -Port 5432 -Quiet -Count 1
if (-not $pgConnection) {
    Write-Warning "PostgreSQL no responde en localhost:5432."
    Write-Warning "Por favor, asegúrate de levantar tu PostgreSQL local e ingresar la contraseña 'Nika'."
    Exit 1
} else {
    Write-Host "   [OK] PostgreSQL está escuchando en el puerto 5432." -ForegroundColor Green
}

# Verificar Ollama
try {
    $ollamaTags = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method Get -TimeoutSec 3
    Write-Host "   [OK] Ollama está corriendo en http://localhost:11434." -ForegroundColor Green
} catch {
    Write-Warning "Ollama no está en ejecución en http://localhost:11434."
    Write-Warning "Por favor, inicia Ollama ('ollama serve') y descarga el modelo 'phi3:mini'."
}

# 2. Inicializar base de datos
Write-Host "`n2. Inicializando y sembrando la base de datos PostgreSQL..." -ForegroundColor Cyan
if (-not (Test-Path $venvPython)) {
    Write-Error "No se encontró el entorno virtual en $venvPython. Asegúrate de ejecutar pip install."
}
& $venvPython "$backendDir/scripts/db_init.py"

# 3. Arrancar servicios del Backend
Write-Host "`n3. Arrancando los 7 microservicios del Backend..." -ForegroundColor Cyan
Set-Location $backendDir
& "./scripts/start_all.ps1"

# 4. Arrancar Workers en segundo plano
Write-Host "`n4. Arrancando trabajadores asíncronos en segundo plano..." -ForegroundColor Cyan
$logDir = Join-Path $backendDir "logs"

# Replicator Job
$replicatorJob = Start-Job -Name "replicator" -ScriptBlock {
    param($dir, $venvPython)
    Set-Location $dir
    & $venvPython scripts/replicator.py *>&1 | Out-File -FilePath (Join-Path $dir "logs/replicator.log") -Encoding utf8
} -ArgumentList $backendDir, $venvPython
$replicatorJob.Id | Out-File -FilePath "$logDir/replicator.pid" -Encoding utf8
Write-Host "   [OK] Replicator iniciado (Job ID: $($replicatorJob.Id))" -ForegroundColor Green

# Preventive Worker Job
$preventiveJob = Start-Job -Name "preventive_worker" -ScriptBlock {
    param($dir, $venvPython)
    Set-Location $dir
    & $venvPython scripts/preventive_worker.py *>&1 | Out-File -FilePath (Join-Path $dir "logs/preventive_worker.log") -Encoding utf8
} -ArgumentList $backendDir, $venvPython
$preventiveJob.Id | Out-File -FilePath "$logDir/preventive_worker.pid" -Encoding utf8
Write-Host "   [OK] Preventive Worker iniciado (Job ID: $($preventiveJob.Id))" -ForegroundColor Green

# 5. Instalar dependencias del Frontend si faltan
Write-Host "`n5. Verificando dependencias del Frontend..." -ForegroundColor Cyan
if (-not (Test-Path (Join-Path $frontendDir "node_modules"))) {
    Write-Host "   node_modules no encontrado en el frontend. Ejecutando npm install..." -ForegroundColor Yellow
    Set-Location $frontendDir
    npm install
} else {
    Write-Host "   [OK] node_modules del frontend ya instalado." -ForegroundColor Green
}

# 6. Ejecutar servidor de desarrollo Frontend
Write-Host ""
Write-Host "==================================================================" -ForegroundColor Green
Write-Host "   TODO EL BACKEND ESTÁ EJECUTÁNDOSE Y LA BASE DE DATOS INICIADA   " -ForegroundColor Green
Write-Host "   INICIANDO FRONTEND. PRESIONA CTRL+C PARA APAGAR EL SISTEMA     " -ForegroundColor Green
Write-Host "==================================================================" -ForegroundColor Green
Write-Host ""

try {
    Set-Location $frontendDir
    npm run dev
} finally {
    Write-Host "`nApagando todo el ecosistema de microservicios y workers..." -ForegroundColor Yellow
    Set-Location $backendDir
    & "./scripts/stop_all.ps1"
    
    # Detener especificamente los jobs de replicator y preventive_worker
    Stop-Job -Name "replicator" -ErrorAction SilentlyContinue
    Stop-Job -Name "preventive_worker" -ErrorAction SilentlyContinue
    Remove-Job -Name "replicator" -Force -ErrorAction SilentlyContinue
    Remove-Job -Name "preventive_worker" -Force -ErrorAction SilentlyContinue
    
    Write-Host "Apagado completo del sistema ejecutado correctamente." -ForegroundColor Green
}
