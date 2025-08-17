@echo off

REM Check if Docker is running and start it if needed
echo Checking Docker status...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo Docker is not running. Attempting to start Docker Desktop...
    
    REM Try to start Docker Desktop on Windows
    if exist "C:\Program Files\Docker\Docker\Docker Desktop.exe" (
        echo Starting Docker Desktop...
        start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
        echo Waiting for Docker to start...
        
        REM Wait up to 60 seconds for Docker to be ready
        for /L %%i in (1,1,60) do (
            docker info >nul 2>&1
            if !errorlevel! equ 0 (
                echo Docker is now running!
                goto docker_ready
            )
            echo Waiting... (%%i/60)
            timeout /t 1 >nul
        )
        
        REM Final check
        docker info >nul 2>&1
        if %errorlevel% neq 0 (
            echo Docker failed to start. Please start Docker Desktop manually and try again.
            pause
            exit /b 1
        )
    ) else (
        echo Docker Desktop not found at standard location.
        echo Please install Docker Desktop or start it manually.
        pause
        exit /b 1
    )
) else (
    echo Docker is running
)

:docker_ready
echo Building VDW Tool Docker container...
docker build -t vdw-tool ./_src
if %errorlevel% neq 0 (
    echo Build failed!
    pause
    exit /b %errorlevel%
)

echo Build successful! Running VDW Tool...

echo Checking for processes on port 1313...
for /f "tokens=5" %%i in ('netstat -aon ^| findstr :1313') do (
    echo Killing process %%i using port 1313
    taskkill /F /PID %%i >nul 2>&1
)

docker run -it --rm -p 1313:1313 -v "%cd%":/data -w /data --memory="8g" --memory-swap="8g" vdw-tool
pause