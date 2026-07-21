@echo off
setlocal EnableExtensions EnableDelayedExpansion

title Depurador Automatico de Direcciones

set "ROOT_DIR=%~dp0"
set "TARGET_DIR=%ROOT_DIR%EJEMPLOS\DEJAR_ACA"
pushd "%ROOT_DIR%"

echo.
echo ================================================
echo       DEPURADOR AUTOMATICO DE DIRECCIONES
echo ================================================
echo.
echo Carpeta de trabajo:
echo %TARGET_DIR%
echo.

if not exist "%TARGET_DIR%" (
    echo La carpeta objetivo no existe.
    echo %TARGET_DIR%
    pause
    exit /b 1
)

set "INPUT_FILE="
set /a MATCH_COUNT=0

for /f "usebackq delims=" %%F in (`cmd /c py -c "from pathlib import Path; files=[str(p.resolve()) for p in Path(r'%TARGET_DIR%').glob('*.xlsx') if '_DEPURADO' not in p.stem.upper() and '_DEPURADO_FINAL' not in p.stem.upper()]; [print(f) for f in files]"`) do (
    set /a MATCH_COUNT+=1
    if !MATCH_COUNT! EQU 1 (
        set "INPUT_FILE=%%F"
    )
)

if %MATCH_COUNT% EQU 0 (
    echo No se encontro ningun archivo .xlsx pendiente en la carpeta.
    echo.
    echo Deja un Excel original en:
    echo %TARGET_DIR%
    echo.
    pause
    exit /b 1
)

if %MATCH_COUNT% GTR 1 (
    echo Hay mas de un archivo .xlsx pendiente en la carpeta.
    echo Deja solo un archivo original a la vez.
    echo.
    for /f "usebackq delims=" %%F in (`cmd /c py -c "from pathlib import Path; files=[p.name for p in Path(r'%TARGET_DIR%').glob('*.xlsx') if '_DEPURADO' not in p.stem.upper() and '_DEPURADO_FINAL' not in p.stem.upper()]; [print(f) for f in files]"`) do echo - %%F
    echo.
    pause
    popd
    exit /b 1
)

for %%I in ("%INPUT_FILE%") do (
    set "INPUT_NAME=%%~nI"
)

set "OUTPUT_DEPURADO=%TARGET_DIR%\%INPUT_NAME%_DEPURADO.xlsx"
set "OUTPUT_FINAL=%TARGET_DIR%\%INPUT_NAME%_DEPURADO_FINAL.xlsx"

echo Archivo detectado:
echo %INPUT_FILE%
echo.
echo Ejecutando primera pasada...
echo.

cmd /c py src/main.py --input "%INPUT_FILE%" --output "%OUTPUT_DEPURADO%" --column DIRECCION --threshold 88 --disable-ai
set "FIRST_EXIT=%ERRORLEVEL%"

if not "%FIRST_EXIT%"=="0" (
    echo.
    echo La primera pasada termino con error. Codigo: %FIRST_EXIT%
    pause
    popd
    exit /b %FIRST_EXIT%
)

echo.
echo Primera pasada lista:
echo %OUTPUT_DEPURADO%
echo.

set "HIGH_ALERTS=0"
for /f %%A in ('cmd /c py -c "import pandas as pd; p=r""%OUTPUT_DEPURADO%""; m=pd.read_excel(p, sheet_name='metricas_calidad'); d=dict(zip(m['metrica'], m['valor'])); total=int(d.get('PALABRA_PEGADA_REVISAR',0) or 0)+int(d.get('REPETICION_PEGADA',0) or 0); print(total)"') do set "HIGH_ALERTS=%%A"

echo Alertas altas detectadas: %HIGH_ALERTS%

if "%HIGH_ALERTS%"=="0" (
    echo.
    echo No se detectaron alertas altas. Puedes usar el archivo depurado.
    echo Archivo final: %OUTPUT_DEPURADO%
    echo.
    pause
    popd
    exit /b 0
)

echo.
set "RUN_SECOND_PASS="
set /p RUN_SECOND_PASS=Se detectaron alertas altas. Deseas generar segunda pasada? [s/N]: 

if /I not "%RUN_SECOND_PASS%"=="s" if /I not "%RUN_SECOND_PASS%"=="si" if /I not "%RUN_SECOND_PASS%"=="y" if /I not "%RUN_SECOND_PASS%"=="yes" (
    echo.
    echo Se conserva solo la primera pasada:
    echo %OUTPUT_DEPURADO%
    echo.
    pause
    popd
    exit /b 0
)

echo.
echo Ejecutando segunda pasada...
echo.

cmd /c py src/main.py --input "%INPUT_FILE%" --output "%OUTPUT_FINAL%" --column DIRECCION --threshold 88 --disable-ai
set "SECOND_EXIT=%ERRORLEVEL%"

if not "%SECOND_EXIT%"=="0" (
    echo.
    echo La segunda pasada termino con error. Codigo: %SECOND_EXIT%
    echo Se mantiene la primera salida:
    echo %OUTPUT_DEPURADO%
    echo.
    pause
    popd
    exit /b %SECOND_EXIT%
)

set "FINAL_HIGH_ALERTS=0"
for /f %%A in ('cmd /c py -c "import pandas as pd; p=r""%OUTPUT_FINAL%""; m=pd.read_excel(p, sheet_name='metricas_calidad'); d=dict(zip(m['metrica'], m['valor'])); total=int(d.get('PALABRA_PEGADA_REVISAR',0) or 0)+int(d.get('REPETICION_PEGADA',0) or 0); print(total)"') do set "FINAL_HIGH_ALERTS=%%A"

echo.
echo Segunda pasada lista:
echo %OUTPUT_FINAL%
echo Alertas altas restantes: %FINAL_HIGH_ALERTS%
echo.
pause
popd
exit /b 0
