@echo off
setlocal enabledelayedexpansion
if exist "dummy.txt" (
    set "APP_IP=localhost"
    for /f "tokens=*" %%i in ('powershell -NoProfile -Command "(Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notmatch 'Loopback' -and $_.InterfaceAlias -notmatch 'vEthernet' } | Sort-Object InterfaceMetric | Select-Object -First 1).IPAddress" 2^>nul') do (
        set "APP_IP=%%i"
    )
    echo !APP_IP!
)
echo fim
