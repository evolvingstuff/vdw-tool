#!/bin/bash

echo "Building VDW Tool Docker container..."
docker build -t vdw-tool ./src

if [ $? -ne 0 ]; then
    echo "Build failed!"
    exit 1
fi

echo "Build successful! Running VDW Tool..."
docker run -it --rm vdw-tool