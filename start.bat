@echo off
REM Přesuneme se do složky skriptu
cd /d "%~dp0"

REM Aktivace virtuálního prostředí
call venv\Scripts\activate

REM Nastavíme Flask aplikaci (upravte, pokud máte jiný název souboru)
set FLASK_APP=app.py

REM Spustíme Flask s hostem a portem
start "" python -m flask run --host=127.0.0.1 --port=5000

REM Počkejme chvíli, aby server stihl odstartovat
timeout /t 2 >nul

REM Otevřeme výchozí prohlížeč na lokální adresu
start http://127.0.0.1:5000

