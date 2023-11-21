@echo off
setlocal enableDelayedExpansion

Rem Parse input variables
set python_env_dir=%1
Rem C:\cems-notebooks\plxcontroller
echo python_env_dir is %python_env_dir% and no more.

Rem Create dir to install the python env dir (if it doesn't exist) 
mkdir %python_env_dir%
cd %python_env_dir%
python -m venv %python_env_dir%
call %python_env_dir%/Scripts/activate.bat




