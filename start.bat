@echo off
title Sorteador Mediateca
echo.
echo  ================================================
echo    Sorteador Mediateca - Instagram
echo  ================================================
echo.

:: Si no existe sesion guardada, ejecutar setup primero
if not exist "ig-session.json" (
    echo  Primera vez detectada: configurando sesion de Instagram...
    echo  Se abrira Chrome. Esperá a que se complete el login automaticamente.
    echo.
    venv\Scripts\python setup_session.py
    echo.
    if not exist "ig-session.json" (
        echo  ERROR: La sesion no se pudo guardar. Revisa el .env
        pause
        exit /b 1
    )
)

echo  Iniciando servidor en http://localhost:8000
echo  Abre tu navegador en esa direccion para usar la app.
echo  Presiona Ctrl+C para detener el servidor.
echo.
venv\Scripts\uvicorn server:app --host 127.0.0.1 --port 8000
pause
