@echo off
setlocal

set "PROJECT_DIR=C:\Users\deanv\OneDrive\Documents\TCC"
cd /d "%PROJECT_DIR%"
if errorlevel 1 goto erro

echo.
echo === Privacy Scanner LGPD: Setup Windows ===
echo Pasta: %CD%
echo.

echo [1/4] Instalando dependencias Python...
python -m pip install -r requirements.txt
if errorlevel 1 goto erro

echo.
echo [2/4] Criando workspace externo de teste...
python scripts\create_test_workspace.py
if errorlevel 1 goto erro

echo.
echo [3/4] Instalando dependencias da extensao VS Code...
cd /d "%PROJECT_DIR%\vscode-extension"
npm install
if errorlevel 1 goto erro

echo.
echo [4/4] Compilando extensao...
npm run compile
if errorlevel 1 goto erro

echo.
echo Setup concluido com sucesso.
echo Abra o VS Code na pasta %PROJECT_DIR% e pressione F5.
goto fim

:erro
echo.
echo Erro no setup. Verifique a mensagem acima.
pause
exit /b 1

:fim
echo.
pause
endlocal
