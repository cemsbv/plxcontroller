@echo off
setlocal enableDelayedExpansion

Rem Parse input variables
set notebooks_installation_dir=%1
Rem C:\cems-notebooks\plxcontroller
echo notebooks_installation_dir is %notebooks_installation_dir% and no more.

Rem Create notebook installation dir and add batch file 
mkdir %notebooks_installation_dir% %notebooks_installation_dir%\sample

Rem Copy sample notebooks (old)
Rem xcopy sample %notebooks_installation_dir%\sample

Rem Copy batch file "start_jupyter_lab"
copy start_jupyter_lab.bat %notebooks_installation_dir%
copy update_plxcontroller.bat %notebooks_installation_dir%


