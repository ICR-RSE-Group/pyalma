# Pyalma

A Python library for SSH connections and remote command execution using Paramiko.

## For remote access, from within python
```
from pyalma import SshConnection

ssh = SshConnection(server='your_server', username='your_username', password='your_password')
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

### For command line,
```bash
pyalma-cli --cmd "ls -l"
```
## To build the package locally:

```bash
python -m pip wheel --no-deps .
```

## To install locally using `pip`:
```bash
pip install -e .
```
