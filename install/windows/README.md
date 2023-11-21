## Install notebook in Windows


To install the notebooks, simpy download all the files in this directory and run the script `full_installation.bat`.

The files can be downloaded using the command line following the instructions:

1. Installing the command-line JSON processor `jq` (if not already installed, requires admin privileges). Note that starting a new cmd is then required.

```bash
curl --output-dir C:\Windows\System32 -L -o jq.exe https://github.com/jqlang/jq/releases/download/jq-1.7/jq-windows-amd64.exe
```

2. Downloading all the files in this directory:

```bash
curl https://api.github.com/repos/cemsbv/plxcontroller/contents/install/windows | jq -r ".[] | .download_url" | for /F "usebackq" %F in (`findstr "."`) do curl -O %F
```