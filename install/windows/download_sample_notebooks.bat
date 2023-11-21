@echo off
setlocal enableDelayedExpansion

mkdir sample
curl --output-dir sample -O https://raw.githubusercontent.com/cemsbv/plxcontroller/main/notebooks/Plaxis3D_input_controller.ipynb
curl --output-dir sample -O https://raw.githubusercontent.com/cemsbv/plxcontroller/main/notebooks/Plaxis3D_output_controller.ipynb
curl --output-dir sample -O https://raw.githubusercontent.com/cemsbv/plxcontroller/main/notebooks/image.png
curl --output-dir sample -O https://raw.githubusercontent.com/cemsbv/plxcontroller/main/notebooks/requirements.txt