@echo off
setlocal enableDelayedExpansion

@REM Parse input variables
set python_exe=%1

@REM Check whether the python.exe exists, otherwise exit without installing.
if not exist %python_exe% (
    echo %python_exe% does not exists, jupyterlab cannot be installed.
    cmd /k
)

@REM Install jupyter lab.
%python_exe% -m pip install jupyterlab
