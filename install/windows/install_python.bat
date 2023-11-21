@echo off
setlocal enableDelayedExpansion

Rem Check which python version is available
Rem https://www.python.org/ftp/python/   # 
Rem For Windows it should there should be file ending with amd64.exe, e.g.:
Rem https://www.python.org/ftp/python/3.9.13/python-3.9.13-amd64.exe

Rem Parse input variables
set python_version=%1
Rem recommended: 3.9.13 
echo python_version is %python_version% and no more.

set python_installation_dir=%2
Rem C:\cems-python
echo python_installation_dir is %python_installation_dir% and no more.

Rem Download python
curl https://www.python.org/ftp/python/%python_version%/python-%python_version%-amd64.exe -O

Rem Install python
mkdir %python_installation_dir%\python-%python_version%
python-%python_version%-amd64.exe TargetDir=%python_installation_dir%\python-%python_version% AppendPath=1






