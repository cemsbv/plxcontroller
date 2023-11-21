@echo off
setlocal enableDelayedExpansion

@REM Parse input variables
set python_env_dir=%1
set kernel_name=%2

Rem Install ipykernel and register virtual environment
call %python_env_dir%/Scripts/activate.bat
python -m pip install --upgrade pip setuptools
pip install ipykernel
python -m ipykernel install --name %kernel_name%



