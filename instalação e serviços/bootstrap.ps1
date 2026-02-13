# Bootstrap Script for EduAgenda - V2 (Robust)
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

function Is-Real-Python {
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if (!$cmd) { return $false }
    
    # Ignorar o atalho da Windows Store (que tem "WindowsApps" no caminho)
    if ($cmd.Source -match "WindowsApps") {
        Write-Warning-Custom "Detectado atalho da Microsoft Store (Shim). Ignorando para instalacao real."
        return $false
    }
    
    # Tenta rodar versao rapida
    try {
        $v = python --version 2>&1
        if ($v -match "Python 3") { return $true }
    }
    catch { return $false }
    
    return $false
}

# 1. Check Winget
Write-Step "Verificando Gerenciador de Pacotes (Winget)..."
if (!(Get-Command winget -ErrorAction SilentlyContinue)) {
    Write-Error-Custom "Winget nao encontrado. Verifique se seu Windows esta atualizado."
    exit 1
}

# 2. Check Python
Write-Step "Verificando Python..."
$needsPyUpdate = $false

if (Is-Real-Python) {
    $verString = python --version 2>&1
    if ($verString -match "3\.14" -or $verString -match "3\.15") {
        Write-Warning-Custom "Versao experimental detectada ($verString). Precisamos da 3.12."
        $needsPyUpdate = $true
    }
    else {
        Write-Host "Python detectado: $verString" -ForegroundColor Green
    }
}
else {
    Write-Warning-Custom "Python real nao detectado ou e apenas o atalho da Loja."
    $needsPyUpdate = $true
}

if ($needsPyUpdate) {
    Write-Step "Instalando Python $TargetPython via Winget (Instalacao Silenciosa)..."
    # Tenta instalar no escopo da maquina para facilitar detecçao
    winget install --id $WingetIdPython --source winget --silent --accept-package-agreements --accept-source-agreements --scope machine
    
    if ($LASTEXITCODE -ne 0) {
        Write-Warning-Custom "Falha na instalacao 'machine'. Tentando escopo 'user'..."
        winget install --id $WingetIdPython --source winget --silent --accept-package-agreements --accept-source-agreements --scope user
    }
}

# 3. Check Git
Write-Step "Verificando Git..."
if (!(Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Warning-Custom "Git nao encontrado. Instalando..."
    winget install --id $WingetIdGit --source winget --silent --accept-package-agreements --accept-source-agreements
}
else {
    Write-Host "Git detectado." -ForegroundColor Green
}

# 4. Refresh Env for the current process
Write-Step "Finalizando e atualizando Variaveis de Ambiente..."
$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")

# Tenta localizar onde o Python foi parar se ainda nao estiver no path do PS
if (!(Is-Real-Python)) {
    $commonPaths = @(
        "$env:ProgramFiles\Python312",
        "$env:ProgramFiles(x86)\Python312",
        "$env:LocalAppData\Programs\Python\Python312"
    )
    foreach ($p in $commonPaths) {
        if (Test-Path "$p\python.exe") {
            Write-Host "Python encontrado manualmente em: $p" -ForegroundColor Green
            $env:Path += ";$p;$p\Scripts"
            break
        }
    }
}

Write-Step "Sincronizacao de ambiente concluida!"
