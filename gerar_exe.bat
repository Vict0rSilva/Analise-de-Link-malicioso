@echo off
rem ============================================================
rem  AnalisaLink - gera o executavel para Windows (pasta portatil)
rem  Uso:  duplo clique, ou  gerar_exe.bat          (padrao: pasta)
rem                          gerar_exe.bat onefile  (arquivo unico)
rem ============================================================
setlocal
cd /d "%~dp0"

echo ===== AnalisaLink: gerando o executavel =====
echo Pasta do projeto: %cd%
echo.

set "MODO=--onedir"
if /i "%~1"=="onefile" set "MODO=--onefile"

rem --- 1) localizar o Python ---------------------------------
set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY where python >nul 2>nul && set "PY=python"
if not defined PY goto :sem_python

rem --- 2) ambiente virtual so para o build -------------------
if not exist ".venv_build\Scripts\python.exe" (
    echo [1/3] Criando ambiente virtual .venv_build ...
    %PY% -m venv ".venv_build"
    if errorlevel 1 goto :falha
)
set "VPY=%~dp0.venv_build\Scripts\python.exe"

echo [2/3] Instalando dependencias ...
"%VPY%" -m pip install --upgrade pip
if errorlevel 1 goto :falha
"%VPY%" -m pip install -r "requirements.txt" -r "requirements-build.txt"
if errorlevel 1 goto :falha

echo.
echo [3/3] Gerando o executavel (%MODO%) ...
"%VPY%" -m PyInstaller --noconfirm --clean --windowed %MODO% ^
    --name AnalisaLink ^
    --icon "assets\icon.ico" ^
    --add-data "assets;assets" ^
    --hidden-import socks ^
    --exclude-module tkinter ^
    "main.py"
if errorlevel 1 goto :falha

echo.
echo ===== PRONTO =====
if /i "%~1"=="onefile" (
    echo Executavel: dist\AnalisaLink.exe
) else (
    echo Executavel: dist\AnalisaLink\AnalisaLink.exe
    echo Distribua a pasta dist\AnalisaLink inteira ^(pode compactar em .zip^).
)
goto :fim

:sem_python
echo.
echo *** ERRO: Python nao encontrado. Instale o Python 3.10-3.13 64 bits em python.org
echo     e marque "Add python.exe to PATH" ou use o instalador com o launcher "py".
goto :fim

:falha
echo.
echo *** O BUILD FALHOU. Leia a mensagem de erro acima. ***

:fim
echo.
pause
endlocal
