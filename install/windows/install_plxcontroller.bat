@echo off
setlocal enableDelayedExpansion

Rem Parse input variables
set python_env_dir=%1

Rem Install ipykernel and register virtual environment
call %python_env_dir%\Scripts\activate.bat
python -m pip install --upgrade pip setuptools
pip install plxcontroller

