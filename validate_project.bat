@echo off
setlocal

set "PROJECT_DIR=C:\Users\deanv\OneDrive\Documents\TCC"
cd /d "%PROJECT_DIR%"
if errorlevel 1 goto erro

echo.
echo === Privacy Scanner LGPD: Validacao ===
echo Pasta: %CD%
echo.

echo [1/3] Recriando workspace de teste...
python scripts\create_test_workspace.py
if errorlevel 1 goto erro

echo.
echo [2/3] Rodando testes Python...
pytest
if errorlevel 1 goto erro

echo.
echo [3/3] Compilando extensao VS Code...
cd /d "%PROJECT_DIR%\vscode-extension"
npm run compile
if errorlevel 1 goto erro

echo.
echo Validacao concluida com sucesso.
goto fim

:erro
echo.
echo Validacao falhou. Verifique a mensagem acima.
pause
exit /b 1

:fim
echo.
pause
endlocal
