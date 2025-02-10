# SSH Connection

A Python library for SSH connections and remote command execution using Paramiko.

## Installation

```bash
pip install sshconnection
```

## To use from another library
```
from sshconnection.sshconnection import SshConnection

ssh = SshConnection(source='remote', username='your_username', password='your_password', server='your_server')
output, error = ssh.run_cmd('ls -l')
print(output)
```

## To build the package locally:

```bash
python -m build
```

## To install locally using `pip`:
```
pip install .
``
