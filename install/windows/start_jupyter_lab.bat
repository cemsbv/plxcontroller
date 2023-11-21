@echo off
setlocal enableDelayedExpansion

set current_dir_path=%~dp0

if not defined CEMS_PYTHON_DIR (
    echo Environmental variable CEMS_PYTHON_DIR does not exists, jupyterlab cannot be started.
    cmd /k
)

%CEMS_PYTHON_DIR%\python -m jupyter lab --notebook-dir=%current_dir_path% --preferred-dir %current_dir_path%




