@echo off
setlocal enableDelayedExpansion

Rem Parse input variables
set plxcontroller_notebook_dir=%1

Rem Create notebook installation dir and add batch file 
mkdir %plxcontroller_notebook_dir% 
Rem mkdir %plxcontroller_notebook_dir%\sample

Rem Copy batch files "start_jupyter_lab", "update_plxcontroller", "download_sample_notebooks"
copy start_jupyter_lab.bat %plxcontroller_notebook_dir%
copy update_plxcontroller.bat %plxcontroller_notebook_dir%
copy download_sample_notebooks.bat %plxcontroller_notebook_dir%


