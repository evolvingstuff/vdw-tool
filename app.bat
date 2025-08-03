@echo off
echo Building VDW Tool Docker container...
docker build -t vdw-tool ./_src
if %errorlevel% neq 0 (
    echo Build failed!
    pause
    exit /b %errorlevel%
)

echo Build successful! Running VDW Tool...
docker run -it --rm -p 1313:1313 -v "%cd%":/data -w /data vdw-tool
pause