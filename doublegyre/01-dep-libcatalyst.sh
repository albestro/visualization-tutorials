#!/usr/bin/env bash

set -e

[[ ${VIRTUAL_ENV:-not-set} == "not-set" ]] && (echo "you should run this in a python virtual environment" && false)

LIBCATALYST_REPO=$(pwd)/libcatalyst.git
LIBCATALYST_ROOT=${LIBCATALYST_REPO}/install-here

[ -d ${LIBCATALYST_REPO} ] || git clone --depth 1 https://gitlab.kitware.com/paraview/catalyst.git ${LIBCATALYST_REPO}
cd ${LIBCATALYST_REPO}

cmake\
  -S .\
  -B build\
  --install-prefix ${LIBCATALYST_ROOT}\
  --fresh\
  -DCATALYST_WRAP_PYTHON=on\
  -DCATALYST_BUILD_STUB_IMPLEMENTATION=on\
  -DCATALYST_BUILD_TOOLS=on

cmake --build build
cmake --install build

PYTHON_WRAPPERS_ROOT=$(ls -d ${LIBCATALYST_ROOT}/lib/python3*/site-packages)
VIRTUALENV_SITE_ROOT=$(ls -d ${VIRTUAL_ENV:-.venv}/lib/python3*/site-packages)

cat <<- EOF
  Now you have to install Catalyst python wrappers in your python venv with something like:

  echo ${PYTHON_WRAPPERS_ROOT:-install-here/lib/python3.14/site-packages} > ${VIRTUALENV_SITE_ROOT:-.venv/lib/python3.14/site-packages}/catalyst.pth
