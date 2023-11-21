@echo off
setlocal enableDelayedExpansion

set current_dir_path=%~dp0

jupyter lab --notebook-dir=%current_dir_path% --preferred-dir %current_dir_path%

Rem Parse input variables
Rem set notebooks_installation_dir=%1
Rem C:\cems-notebooks\plxcontroller
Rem echo notebooks_installation_dir is %notebooks_installation_dir% and no more.

Rem Create notebook installation dir and add batch file 
Rem mkdir %notebooks_installation_dir% %notebooks_installation_dir%\sample




