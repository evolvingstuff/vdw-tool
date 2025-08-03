#!/bin/bash

echo "Running VDW Tool..."
docker run -it --rm -v "$(pwd)":/data -w /data vdw-tool