@echo off

echo Converting the Python file into an executable

pyinstaller --onefile --name PackageInstaller --add-data "lang;lang" main.py

echo Cleaning build artifacts...

rmdir /s /q build 2>nul
rmdir /s /q __pycache__ 2>nul
del *.spec 2>nul

move dist\PackageInstaller.exe .
rmdir /s /q dist

echo Done.
pause