@echo off
echo Running VDW Tool...
docker run -it --rm -v "%cd%":/data -w /data vdw-tool
pause