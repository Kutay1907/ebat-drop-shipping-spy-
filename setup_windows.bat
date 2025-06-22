@echo off
echo.
echo ===============================================
echo   eBay Dropshipping Spy - Windows Kurulumu
echo ===============================================
echo.

REM Sistem bilgilerini kontrol et
echo [1/6] Sistem bilgileri kontrol ediliyor...
echo OS: %OS%
echo Architecture: %PROCESSOR_ARCHITECTURE%
echo.

REM Python kontrolü
echo [2/6] Python kontrolü...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo HATA: Python bulunamadi!
    echo.
    echo Python 3.8+ kurmaniz gerekiyor:
    echo 1. https://www.python.org/downloads/ adresine gidin
    echo 2. "Download Python" butonuna tiklayin
    echo 3. Kurulum sirasinda "Add Python to PATH" secenegini isaretleyin
    echo.
    pause
    exit /b 1
)

python --version
echo.

REM Pip kontrolü
echo [3/6] Pip kontrolü...
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo HATA: Pip bulunamadi!
    echo Python ile birlikte pip kurulmali.
    pause
    exit /b 1
)

echo [4/6] Gerekli Python paketleri kuruluyor...
pip install flask flask-cors playwright requests beautifulsoup4 lxml pillow fuzzywuzzy python-levenshtein

echo.
echo [5/6] Playwright browser kuruluyor...
playwright install

echo.
echo [6/6] Test ediliyor...
python -c "import flask, playwright; print('✅ Tum paketler basariyla kuruldu!')"

echo.
echo ===============================================
echo           KURULUM TAMAMLANDI!
echo ===============================================
echo.
echo Sistemi baslatmak icin:
echo   start_windows.bat
echo.
echo Monitor icin:
echo   http://localhost:8082
echo.
echo Web App icin:
echo   http://localhost:8081
echo.
pause 