#!/bin/bash

echo "Building VDW Tool Docker container..."
cd ..
docker build -t vdw-tool ./_src

if [ $? -ne 0 ]; then
    echo "Build failed!"
    exit 1
fi

echo "Build successful! Running VDW Tool..."
docker run -it --rm -v "$(pwd)":/data -w /data vdw-tool