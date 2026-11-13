@echo off
cd /d "%~dp0"
python dfir_workbench.py
if errorlevel 1 pause
