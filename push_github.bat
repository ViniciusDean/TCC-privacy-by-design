@echo off
setlocal

set "PROJECT_DIR=C:\Users\deanv\OneDrive\Documents\TCC"
cd /d "%PROJECT_DIR%"
if errorlevel 1 goto erro

set "MSG=%~1"
if "%MSG%"=="" (
    set /p "MSG=Digite a mensagem do commit: "
)
if "%MSG%"=="" set "MSG=Atualiza projeto"

echo.
echo === Privacy Scanner LGPD: Git Push ===
echo Pasta: %CD%
echo Commit: %MSG%
echo.

git status --short
echo.

git add .
if errorlevel 1 goto erro

git diff --cached --quiet
if not errorlevel 1 (
    echo Nenhuma alteracao para commitar.
    goto push
)

git commit -m "%MSG%"
if errorlevel 1 goto erro

:push
git push
if errorlevel 1 goto erro

echo.
echo Push concluido com sucesso.
goto fim

:erro
echo.
echo Erro ao executar o push. Verifique a mensagem acima.
pause
exit /b 1

:fim
echo.
pause
endlocal
