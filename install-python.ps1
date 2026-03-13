winget install -e --id Python.Python.3.14
$homedir = $env:USERPROFILE
$env:PATH += ";$homedir\AppData\Local\Programs\Python\Python314"
python.exe -m pip install pip --upgrade --no-cache
