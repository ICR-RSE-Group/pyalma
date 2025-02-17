import os
import sys
import pandas as pd
import paramiko
import logging
from io import StringIO
import argparse

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(dir_path)
__file__

# Configure logging for better traceability
logging.basicConfig(level=logging.DEBUG)

def main():
    parser = argparse.ArgumentParser(description="SSH Command Runner")
    parser.add_argument('source', choices=['local', 'remote'], help="Source of the command execution (local or remote)")
    parser.add_argument('command', help="The command to run")
    parser.add_argument('--username', help="Username for the SSH server, required with remote")
    parser.add_argument('--password', help="Password for the SSH server, required with remote (use either this or private_key)")
    parser.add_argument('--private_key', help="Path to private key for the SSH server, required with remote (use either this or passowrd)")
    parser.add_argument('--server', default="alma.icr.ac.uk", help="Remote server address (default: alma.icr.ac.uk)")
    parser.add_argument('--df', action='store_true', help="Return the output as pandas DataFrame if set")
    parser.add_argument('--sep', default=',', help="Use selected separator when reading from csv")

    args = parser.parse_args()
 
    # Check for valid authentication method (either password or private_key)
    if args.source=="remote":
        if not args.password and not args.private_key:
            raise ValueError("You must specify either --password or --private_key for remote connections.")
        if args.password and args.private_key:
            raise ValueError("You cannot specify both --password and --private_key at the same time.")

    # Create SSH connection based on authentication method
    if args.password:
        ssh = SshConnection(args.source, args.server, username=args.username, password=args.password)
    else:  # Use private key
        ssh = SshConnection(args.source, args.server, username=args.username, key_path=args.private_key)
    
    result = ssh.run_cmd(cmd=args.command, is_string=not args.df, sep=args.sep)

    # Handle unpacking based on length
    if len(result) == 2:
        output, err = result
    else:
        output, err = result, None

    if err:
        print(f"Error: {err}")
    else:
        print(output)

class SshConnection:
    def __init__(self, source, server="alma-app.icr.ac.uk", username=None, password=None, key_path=None):
        """
        Initializes the SSH connection instance.

        :param source: could be 'local' or 'remote'
        :param username: SSH username for alma
        :param password: SSH password for alma
        :param server: The remote server address (default is 'alma.icr.ac.uk')
        """
        self.source = source.strip()
        self.server = server.strip()
        self.username = username.strip() if username else None
        self.password = password.strip() if password else None
        self.key_path = os.path.expanduser(key_path) if key_path else None  # Expand ~ to full home path

    def _load_private_key(self):
        """Load private key dynamically based on its type."""
        if not self.key_path:
            return None

        key_path = self.key_path

        try:
            # Try loading different key types dynamically
            if key_path.endswith('.pem') or key_path.endswith('.rsa'):
                private_key = paramiko.RSAKey.from_private_key_file(key_path)
            elif key_path.endswith('.dsa'):
                private_key = paramiko.DSSKey.from_private_key_file(key_path)
            elif key_path.endswith('.ecdsa'):
                private_key = paramiko.ECDSAKey.from_private_key_file(key_path)
            elif key_path.endswith('.ed25519'):
                private_key = paramiko.Ed25519Key.from_private_key_file(key_path)
            else:
                # If the extension is not recognized, try automatically detecting it
                private_key = paramiko.RSAKey.from_private_key_file(key_path)
            return private_key
        except paramiko.ssh_exception.SSHException as e:
            logging.error(f"Error loading key: {e}")
            return None
        
    def run_cmd(self, cmd, is_string=True, sep=",", listdir=False):
        """
        Runs a command either locally or remotely via SSH.

        :param cmd: Command to run on local or remote server
        :param return_dataframe: Boolean flag to determine if result should be returned as pandas DataFrame
        :return: Command output as string or pandas DataFrame
        """
        if self.source == "local":
            return self.run_local(cmd)#add support for listdir and csv reading
        else:
            return self.run_remote(cmd, is_string, sep, listdir)

    def run_local(self, cmd):
        """
        Executes a command locally.

        :param cmd: Command to execute locally
        :return: Command output as string
        """
        try:
            logging.info(f"Running local command: {cmd}")
            output = os.popen(cmd).read()
            return output
        except Exception as e:
            logging.error(f"Error running local command: {e}")
            return str(e)

    def run_remote(self, cmd, is_string=True, sep=",", listdir=False):
        """
        Executes a command on the remote server via SSH.

        :param cmd: Command to execute remotely
        :param is_string: Boolean flag to determine if result should be returned as a string or pandas DataFrame
        :param sep: String to use as a separator for csv files
        :return: Command output as string or pandas DataFrame
        """
        try:
            logging.info(f"Running remote command: {cmd}")
            with paramiko.SSHClient() as client:
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                #connection via password
                if self.password:
                    client.connect(self.server, username=self.username, password=self.password, timeout=30)
                #connection via ssh keys
                if self.key_path:
                    private_key = self._load_private_key()
                    client.connect(self.server, username=self.username, pkey=private_key)
                if not is_string or listdir:
                    #Use SFTP to retrieve the file as a Dataframe. sftp is not working for listdir
                    with client.open_sftp() as sftp:
                        if listdir:
                            files = sftp.listdir(cmd)
                            return files, ""
                        #reading files
                        with sftp.open(cmd, 'r') as remote_file:
                            file_content = remote_file.read().decode('utf-8')
                            df = pd.read_csv(StringIO(file_content), sep=sep)
                            return df, ""
                else:
                    # Return the command output as a string
                    _, stdout, stderr = client.exec_command(cmd, get_pty=True)
                    err_str = stderr.read().decode("ascii")
                    out_str = stdout.read().decode("ascii")

                    return out_str, err_str

        except Exception as e:
            logging.error(f"Error running remote command: {e}")
            return "", str(e)
    
if __name__ == "__main__":
    main()