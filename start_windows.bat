@echo off
echo.
echo ===============================================
echo   eBay Dropshipping Spy - Windows Baslatici
echo ===============================================
echo.

REM Mevcut servisleri kontrol et
echo [1/3] Mevcut servisler kontrol ediliyor...
netstat -an | findstr ":8081" >nul
if %errorlevel% equ 0 (
    echo Port 8081 zaten kullaniliyor!
    echo Mevcut servisi durdurun veya farkli port kullanin.
    pause
    exit /b 1
)

netstat -an | findstr ":8082" >nul
if %errorlevel% equ 0 (
    echo Port 8082 zaten kullaniliyor!
    echo Mevcut servisi durdurun veya farkli port kullanin.
    pause
    exit /b 1
)

echo [2/3] Background Scraper baslatiliyor...
start "Background Scraper" python background_scraper.py

echo Bekliyor... (3 saniye)
timeout /t 3 /nobreak >nul

echo [3/3] Monitor baslatiliyor...
start "Simple Monitor" python simple_monitor.py

echo Bekliyor... (2 saniye)
timeout /t 2 /nobreak >nul

echo [4/4] Web App baslatiliyor...
echo.
echo ===============================================
echo             SISTEM BASLATILDI!
echo ===============================================
echo.
echo 🖥️  Monitor Dashboard: http://localhost:8082
echo 🌐 Web Application:   http://localhost:8081
echo 📊 Background Scraper: Arkaplanda calisiyor
echo.
echo Servisleri durdurmak icin:
echo   stop_windows.bat
echo.
echo Web App baslatiliyor...
python web_app.py 