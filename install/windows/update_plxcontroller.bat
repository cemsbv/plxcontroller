@echo off
setlocal enableDelayedExpansion

Rem Install ipykernel and register virtual environment
call .env\Scripts\activate.bat
pip install --upgrade --no-cache-dir plxcontroller

Rem Download sample notebooks
call download_sample_notebooks

echo. 
echo.
echo The following version of the plxcontroller is installed:
echo.
pip show plxcontroller

Rem Keep the window open
cmd /k