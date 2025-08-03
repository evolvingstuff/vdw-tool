#!/bin/bash

echo "Running VDW Tool..."
cd ..
docker run -it --rm -v "$(pwd)":/data -w /data vdw-tool