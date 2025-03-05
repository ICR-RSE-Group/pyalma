# Pyalma

A Python library for SSH connections and remote command execution using Paramiko.

## To build and install the package locally:
Before building and installing the package, it is recommended to create a dedicated Python environment for your project.
1. Create a Python Environment and activate it:
```bash
python -m venv .env-py
source .env-py/bin/activate
```

2. Install Build Dependencies
```bash
python -m pip install --upgrade pip build
```

3. Clone this repo locally to your machine:
```bash
git clone git@github.com:ICR-RSE-Group/pyalma.git
```
4. Build the Package Locally:
Make sure to navigate to the package directory before building
```bash
cd pyalma
python -m build
```
5. Install locally using `pip`:
```bash
pip install -e .
```

### For command line,
```bash
pyalma-cli --cmd "ls -l"
```
## For remote access, from within python
```
from pyalma import SshClient

ssh = SshClient(server='your_server', username='your_username', password='your_password')
result = ssh.run_cmd('ls -l')
print(result["output"])
```

## For local access, from within python
```
from pyalma import LocalFileReader

local = LocalFileReader()
output, error = local.run_cmd('ls -l')
print(result["output"])
```

