set pip_dependencies=watchdog==7.1.0 filelock==4.2.9 psutil pyinstaller pysimplegui
set bundle_name=edcopilot-mfd.zip

if NOT "%1"=="" set bundle_name=edcopilot-mfd-%1.zip

echo %bundle_name%

rmdir /s /q .venv_windows
python -mvenv .venv_windows || exit /b 1
rmdir /q .venv
mklink /j .venv .venv_windows || exit /b 1
.\.venv_windows\Scripts\pip.exe install %pip_dependencies%  || exit /b 1

rmdir /s /q dist
.venv_windows\Scripts\pyinstaller.exe  -n edcopilot-mfd src\main.py || exit /b 1
del edcopilot-mfd.spec

echo delete bundle
rmdir /s /q bundle\edcopilot
mkdir bundle
mkdir bundle\edcopilot
mkdir bundle\edcopilot\bin
mkdir bundle\edcopilot\screens
echo mkdirs done
copy plugin\manifest.json bundle\edcopilot\manifest.json  || exit /b 1
copy plugin\edcopilot.json bundle\edcopilot\screens\edcopilot.json  || exit /b 1
copy dist\edcopilot-mfd\edcopilot-mfd.exe bundle\edcopilot\bin\edcopilot-mfd.exe || exit /b 1
robocopy dist\edcopilot-mfd\_internal bundle\edcopilot\bin\_internal || exit /b 1

cd bundle
..\.venv_windows\Scripts\python.exe -m zipfile -c %bundle_name% edcopilot || exit /b 1