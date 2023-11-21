@echo off
setlocal enableDelayedExpansion

set python_installation_dir=C:\cems-python
set python_version=3.9.13
set plxcontroller_notebook_dir=C:\cems-notebooks\plxcontroller
set kernel_name=plxcontroller-env


echo 1. Download and install python
if not defined CEMS_PYTHON_DIR (
    call install_python %python_version% %python_installation_dir%
    Rem Set the system environmental variables of the location of the new installation
    setx CEMS_PYTHON_DIR %python_installation_dir%\python-%python_version%
    Rem Set it also locally so that it can be accessed without reloading cmd.
    set CEMS_PYTHON_DIR %python_installation_dir%\python-%python_version%
) else (
    echo Python is not downloaded and installed, because environmental variable CEMS_PYTHON_DIR is defined. 
    echo %CEMS_PYTHON_DIR%\python.exe will be used as base to create the python virtual environment. 
)

echo 2. Install jupyter lab
call install_jupyterlab %CEMS_PYTHON_DIR%\python.exe

echo 3. Set-up notebook directory
call setup_notebook_dir %plxcontroller_notebook_dir%

echo 4. Create python environment
if not exist %plxcontroller_notebook_dir%\.env\Scripts\python.exe (
    call create_python_env %CEMS_PYTHON_DIR%\python.exe %plxcontroller_notebook_dir%\.env
) else (
    echo Python virtual environment at %plxcontroller_notebook_dir%\.env will be used, no new one is created.
)

echo 5. Register python environment in ipykernel
call register_env_ipykernel %plxcontroller_notebook_dir%\.env "%kernel_name%"

echo 6. Install plxcontroller
call install_plxcontroller %plxcontroller_notebook_dir%\.env

echo 7. Download sample notebooks
cd /D %plxcontroller_notebook_dir%
call download_sample_notebooks

echo Installation finished!
cmd /k