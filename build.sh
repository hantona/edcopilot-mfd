#!/bin/bash

pip_dependencies=(watchdog==7.1.0 filelock==4.2.9 psutil pyinstaller pysimplegui)

version="$1"

set -e

if [[ -n "${version}" ]] ; then
  bundle_name="edcopilot-mfd-linux-${version}.tar.gz"
else
  bundle_name="edcopilot-mfd-linux.tar.gz"
fi

echo "Removing .venv_linux"
rm -rf .venv_linux

echo "Creating .venv_linux"
python3 -mvenv .venv_linux


# Replace the .venv symlink unless it is an NTFS junction link to .venv_windows
# If the project is outside the WSL filesystem, the junction link will point to an absolute path under /mnt/c/
# A Linux symlink will be relative to the current directory
# The file command returns the raw symlink target without resolving it to an absolute path
if ! file .venv 2>&1 |grep -q ': symbolic link to /mnt/[a-z]/' ; then
  rm .venv
  ln -s .venv_linux .venv
fi

ln -s .venv_linux .venv

echo "Installing dependencies"
# shellcheck disable=SC2086
.venv_linux/bin/pip install "${pip_dependencies[@]}"

echo "Compiling"
rm -rf dist
.venv_linux/bin/pyinstaller  -n edcopilot-mfd src/main.py
rm edcopilot-mfd.spec

echo "Building installer bundle"
rm -rf bundle/edcopilot
mkdir -p bundle/edcopilot/bin bundle/edcopilot/screens

cp plugin/manifest.json bundle/edcopilot/manifest.json
# Fix the command line for Linux
sed -i -e 's|bin/edcopilot-mfd.exe|bin/edcopilot-mfd|' bundle/edcopilot/manifest.json

cp plugin/edcopilot.json bundle/edcopilot/screens/edcopilot.json
cp dist/edcopilot-mfd/edcopilot-mfd bundle/edcopilot/bin/edcopilot-mfd
cp -r dist/edcopilot-mfd/_internal bundle/edcopilot/bin/_internal

cd bundle
tar -zcf "${bundle_name}" edcopilot