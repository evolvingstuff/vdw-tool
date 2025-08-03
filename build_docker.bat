@echo off
echo Building VDW Tool Docker container...
docker build -t vdw-tool ./src
if %errorlevel% neq 0 (
    echo Build failed!
    pause
    exit /b %errorlevel%
)

echo Build successful! Running VDW Tool...
docker run -it --rm vdw-tool
pause