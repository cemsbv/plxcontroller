@echo off
setlocal enableDelayedExpansion

Rem Parse input variables
set python_env_dir=%1
Rem C:\cems-notebooks\plxcontroller\.env
echo python_env_dir is %python_env_dir% and no more.

set kernel_name=%2
Rem "plxcontroller-env"
echo kernel_name is %kernel_name% and no more.

Rem Install ipykernel and register virtual environment
call %python_env_dir%/Scripts/activate.bat
python -m pip install --upgrade pip setuptools
pip install ipykernel
python -m ipykernel install --name %kernel_name%



