# Bootstrap Script for EduAgenda
# Automates Python 3.12 and Git installation

$TargetPython = "3.12"
$WingetIdPython = "Python.Python.3.12"
$WingetIdGit = "Git.Git"

function Write-Step($msg) {
    Write-Host "`n[*] $msg" -ForegroundColor Cyan
}

function Write-Warning-Custom($msg) {
    Write-Host "[!] $msg" -ForegroundColor Yellow
}

function Write-Error-Custom($msg) {
    Write-Host "[X] $msg" -ForegroundColor Red
}

# 1. Check Winget
Write-Step "Verificando Winget (Windows Package Manager)..."
if (!(Get-Command winget -ErrorAction SilentlyContinue)) {
    Write-Error-Custom "Winget nao encontrado. Este script requer Windows 10/11 atualizado."
    exit 1
}

# 2. Check Python
Write-Step "Verificando Python..."
$pyInstalled = $false
$needsPyUpdate = $false

if (Get-Command python -ErrorAction SilentlyContinue) {
    $verString = python --version 2>&1
    if ($verString -match "3\.14" -or $verString -match "3\.15") {
        Write-Warning-Custom "Versao experimental detectada ($verString). Instalando Python 3.12 estavel..."
        $needsPyUpdate = $true
    } else {
        $pyInstalled = $true
        Write-Host "Python detectado: $verString" -ForegroundColor Green
    }
} else {
    Write-Warning-Custom "Python nao encontrado."
    $needsPyUpdate = $true
}

if ($needsPyUpdate) {
    Write-Step "Instalando Python $TargetPython via Winget (Pode demorar)..."
    winget install --id $WingetIdPython --source winget --silent --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Python $TargetPython instalado com sucesso!" -ForegroundColor Green
        $pyInstalled = $true
    } else {
        Write-Error-Custom "Falha ao instalar Python via Winget."
    }
}

# 3. Check Git
Write-Step "Verificando Git..."
if (!(Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Warning-Custom "Git nao encontrado. Instalando..."
    winget install --id $WingetIdGit --source winget --silent --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Git instalado com sucesso!" -ForegroundColor Green
    } else {
        Write-Error-Custom "Falha ao instalar Git via Winget."
    }
} else {
    Write-Host "Git detectado." -ForegroundColor Green
}

# 4. Refresh Env for the current process (limited)
Write-Step "Atualizando ambiente da sessao..."
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

Write-Step "Bootstrap concluido!"
