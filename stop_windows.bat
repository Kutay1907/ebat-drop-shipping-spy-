@echo off
echo.
echo ===============================================
echo   eBay Dropshipping Spy - Windows Durdurucu
echo ===============================================
echo.

echo [1/3] Python processler durduruluyor...

REM Background Scraper'i durdur
tasklist | findstr "python" >nul
if %errorlevel% equ 0 (
    echo Background Scraper durduruluyor...
    taskkill /f /im python.exe /fi "WINDOWTITLE eq Background Scraper" >nul 2>&1
)

REM Simple Monitor'u durdur
tasklist | findstr "python" >nul
if %errorlevel% equ 0 (
    echo Simple Monitor durduruluyor...
    taskkill /f /im python.exe /fi "WINDOWTITLE eq Simple Monitor" >nul 2>&1
)

echo [2/3] Port 8081 ve 8082 kontrol ediliyor...

REM Port 8081'i temizle
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8081"') do (
    echo Port 8081 temizleniyor (PID: %%a)
    taskkill /f /pid %%a >nul 2>&1
)

REM Port 8082'yi temizle
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8082"') do (
    echo Port 8082 temizleniyor (PID: %%a)
    taskkill /f /pid %%a >nul 2>&1
)

echo [3/3] Tum Python processler durduruluyor...
taskkill /f /im python.exe >nul 2>&1

echo.
echo ===============================================
echo           TUM SERVISLER DURDURULDU!
echo ===============================================
echo.
echo Sistemi yeniden baslatmak icin:
echo   start_windows.bat
echo.
pause 