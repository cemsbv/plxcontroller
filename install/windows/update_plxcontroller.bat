@echo off
setlocal enableDelayedExpansion

Rem Install ipykernel and register virtual environment
call .env\Scripts\activate.bat
pip install --upgrade plxcontroller

Rem Download files under the notebooks directory in plxcontroller repo
curl https://raw.githubusercontent.com/cemsbv/plxcontroller/main/notebooks/Plaxis3D_input_controller.ipynb -O
curl https://raw.githubusercontent.com/cemsbv/plxcontroller/main/notebooks/image.png -O
curl https://raw.githubusercontent.com/cemsbv/plxcontroller/main/notebooks/requirements.txt -O

Rem Save the files under the local sample folder
mkdir sample
move Plaxis3D_input_controller.ipynb sample
move image.png sample
move requirements.txt sample