@echo off
setlocal enableDelayedExpansion

@REM Parse input variables
set python_exe=%1
set python_env_dir=%2

@REM Check whether the python.exe exists, otherwise exit without installing.
if not exist %python_exe% (
    echo %python_exe% does not exists, python environment cannot be created from it.
    cmd /k
)

Rem Create dir to install the python env dir (if it doesn't exist) 
mkdir %python_env_dir%
cd %python_env_dir%
%python_exe% -m venv %python_env_dir%




