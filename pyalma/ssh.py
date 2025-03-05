import os
import paramiko
import logging
from stat import S_ISDIR, S_ISREG
import tempfile 
from .fileReader import FileReader

# Configure logging for better traceability
logging.basicConfig(level=logging.DEBUG)

class SshClient(FileReader):
    """Initializes the SSH connection instance.
        :param username: SSH username for alma
        :param password: SSH password for alma
        :param server: The remote server address (default is 'alma.icr.ac.uk')
    """
    #use alma-app since it has an sftp server
    def __init__(self, server="alma-app.icr.ac.uk", username=None, password=None):
        self.server = server.strip()
        self.username = username.strip() if username else None
        self.password = password.strip() if password else None                
        # super().__init__(arg)# will be useful later
        self.authentication = None
        self.ssh = False
        try:
            self._connect(ssh=True)
            self.authentication = "ssh"
            self.ssh = True
        except Exception as e:
            try:
                self._connect(ssh=False)
                self.authentication = "password"
            except:
                self.authentication = "failed"
            
            
    def _connect(self,ssh=False):
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        if ssh:
            client.connect(self.server, username=self.username, password=self.password, timeout=30)
        else:
            client.connect(self.server, username=self.username, timeout=30)
        return client
    
    def read_file(self, path):
        try:
            client = self._connect(self.ssh)
            sftp = client.open_sftp()
            with sftp.file(path, 'r') as file:
                content = file.read().decode()
            sftp.close()
            client.close()
            return content
        except Exception as e:
            logging.error(f"Error reading SSH file {path}: {e}")
            return None
    
    def listdir(self, path):
        try:
            client = self._connect(self.ssh)
            sftp = client.open_sftp()
            files = sftp.listdir(path)
            directories = []
            files = []
            # List directory contents with attributes
            for entry in sftp.listdir_attr(path):
                mode = entry.st_mode
                if S_ISDIR(mode):
                    directories.append(entry.filename)
                elif S_ISREG(mode):
                    files.append(entry.filename)
            sftp.close()
            client.close()
            return directories, files 
        except Exception as e:
            logging.error(f"Error listing SSH directory {path}: {e}")
            return []
    
    def run_cmd(self, command):
        """
        Executes a command on the remote server via SSH.

        :param cmd: Command to execute remotely
        :return: Command output as string always, since file reading 
                 is another command
        """
        try:
            client = self._connect(self.ssh)
            _, stdout, _ = client.exec_command(command)
            output = stdout.read().decode("ascii")
            client.close()
            return {"output":output,"err":None}
        except Exception as e:
            logging.error(f"Error executing SSH command {command}: {e}")
            return {"output":None,"err":str(e)}

    def read_file_into_df(self, path, type, sep=",", header=None, colnames=[], on_bad_lines='skip'):
        try:
            client = self._connect(self.ssh)
            #Use SFTP to retrieve the file as a Dataframe. sftp is not working for listdir
            sftp = client.open_sftp()
            if type == "vcf":
                with tempfile.TemporaryDirectory() as tmpdirname:
                    print('created temporary directory', tmpdirname)
                    local_file = os.path.join(tmpdirname, "tmp.vcf")
                    sftp.get(path, local_file)
                    return self.read_vcf_file_into_df(local_file)
            else:
                with sftp.open(path, 'r') as remote_file:
                    file_content = remote_file.read()
                    return self.decode_file_by_type(file_content, type, sep=sep, header=header, colnames=colnames, on_bad_lines=on_bad_lines)
        except Exception as e:
            logging.error(f"Error reading SSH file into DataFrame {path}: {e}")
            return None

