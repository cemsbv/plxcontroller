@echo off
setlocal enableDelayedExpansion

Rem 1. Download and install python
Rem call install_python 3.9.13 C:\cems-python

Rem 2. Install jupyter lab
Rem call install_jupyterlab

Rem 3. Set-up notebook directory
call setup_notebook_dir C:\cems-notebooks\plxcontroller

Rem 4. Create python environment
call create_python_env C:\cems-notebooks\plxcontroller\.env

Rem 5. Register python environment in ipykernel
call register_env_ipykernel C:\cems-notebooks\plxcontroller\.env "plxcontroller-env"

Rem 6. Install plxcontroller
call install_plxcontroller C:\cems-notebooks\plxcontroller\.env

Rem 7. Update plxcontroller (so that the sample notebooks are downloaded)
cd C:\cems-notebooks\plxcontroller
call update_plxcontroller