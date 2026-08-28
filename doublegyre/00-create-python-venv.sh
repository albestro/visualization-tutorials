#!/usr/bin/env bash

# note:
# --managed-python ensures that there are development files
# --python 3.12 ensures that we use the same version used by paraview (check it!)
uv venv --managed-python --python 3.12
uv pip install -r requirements.txt
