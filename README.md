# SSH Connection

A Python library for SSH connections and remote command execution using Paramiko.

## Installation

```bash
pip install sshconnection
```

## For remote access, from within python
```
from sshconnection.sshconnection import SshConnection

ssh = SshConnection(server='your_server', username='your_username', password='your_password')
result = ssh.run_cmd('ls -l')
print(result["output"])
```

## For local access, from within python
```
from sshconnection.sshconnection import LocalFileReader

MY_FReader = LocalFileReader()
output, error = ssh.run_cmd('ls -l')
print(result["output"])
```
## To build the package locally:

```bash
python -m build
```

## To install locally using `pip`:
```
pip install .
``
