@echo off
setlocal enableDelayedExpansion

Rem This script assumes that you have python installed and it will use the default python
Rem Parse input variables
set python_env_dir=%1
Rem C:\cems-notebooks\plxcontroller\.env
echo python_env_dir is %python_env_dir% and no more.

Rem Install ipykernel and register virtual environment
call %python_env_dir%\Scripts\activate.bat
python -m pip install --upgrade pip setuptools
pip install plxcontroller

