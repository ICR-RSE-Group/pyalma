import os
import paramiko
import logging
from stat import S_ISDIR, S_ISREG
import tempfile 
from .fileReader import FileReader
import pandas as pd
from io import StringIO
# Configure logging for better traceability
logging.basicConfig(level=logging.DEBUG)

class SshClient(FileReader):
    """Initializes the SSH connection instance.
        :param username: SSH username for alma
        :param password: SSH password for alma
        :param server: The remote server address (default is 'alma.icr.ac.uk')
    """
    #use alma-app since it has an sftp server
    def __init__(self, server="alma.icr.ac.uk", username=None, password=None, sftp="alma-app.icr.ac.uk"):
        self.server = server.strip()
        self.sftp = self.server if sftp is None else sftp.strip()
        self.username = username.strip() if username else None
        self.password = password.strip() if password else None                
        super().__init__()
                
    def _connect(self,sftp=False):
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            if sftp:
                client.connect(self.sftp, username=self.username, password=self.password, timeout=30)
                return client.open_sftp()       
            else:
                client.connect(self.server, username=self.username, password=self.password, timeout=30)
                return client        
        except paramiko.AuthenticationException:
            raise ConnectionError(f"Authentication failed for {self.username}@{self.server}. Please check your credentials.")
        
        except paramiko.SSHException as e:
            raise ConnectionError(f"SSH connection error: {e}. Please check the server or the SSH configuration.")
        
        except Exception as e:
            raise ConnectionError(f"An unexpected error occurred: {e}")
    
    # specific function for remote anndata reading
    # reads the remote file in chunks and write it to a local file, minimizing memory usage during the transfer.​
    # returns a path to a local file
    def load_h5ad_file(self, path, local_path):
        type = self.get_file_extension(path)
        self.files_to_clean.append(local_path)
        try:
            with self._connect(sftp=True) as sftp:
                with sftp.file(path, 'r') as file:
                    with open(local_path, 'wb') as local_file:
                        file.prefetch()
                        for data in iter(lambda: file.read(32768), b''):
                            local_file.write(data)                          
                    return local_path
        except Exception as e:
            logging.error(f"Error reading SSH file {path}: {e}")
            return None 
          
    def read_file(self, path):
        type = self.get_file_extension(path)
        try:
            with self._connect(sftp=True) as sftp:
                with sftp.file(path, 'r') as file:
                    file_content = file.read()
                    return self.decode_file_by_type(file_content, type)
        except Exception as e:
            logging.error(f"❌ Error reading SSH file {path}: {e}")
            return None
    
    def listdir(self, path):
        try:            
            with self._connect(sftp=True) as sftp:
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
            return directories, files 
        except Exception as e:
            logging.error(f"❌ Error listing SSH directory {path}: {e}")
            return []
    
    def run_cmd(self, command):
        """
        Executes a command on the remote server via SSH.

        :param cmd: Command to execute remotely
        :return: Command output as string always, since file reading 
                 is another command
        """
        try:
            with self._connect() as client:
                _, stdout, _ = client.exec_command(command)
                output = stdout.read().decode("ascii")            
            return {"output":output,"err":None}
        except Exception as e:
            logging.error(f"❌ Error executing SSH command {command}: {e}")
            return {"output":None,"err":str(e)}

    def read_file_into_df(self, path, type, **kwargs):
        try:
            with self._connect(sftp=True) as sftp:                        
                if type == "vcf":
                    with tempfile.TemporaryDirectory() as tmpdirname:
                        print('created temporary directory', tmpdirname)
                        local_file = os.path.join(tmpdirname, "tmp.vcf")
                        sftp.get(path, local_file)
                        return self.read_vcf_file_into_df(local_file)
                else:
                    with sftp.open(path, 'rb') as remote_file:
                        file_content = remote_file.read()
                        return self.decode_file_by_type(file_content, type, **kwargs)
        except Exception as e:
            logging.error(f"❌ Error reading SSH file into DataFrame {path}: {e}")
            return None
    #this is available only for ssh
    def download_remote_file(self, remote_path, local_path):
        try:
            with self._connect(sftp=True) as sftp:
                sftp.get(remote_path, local_path)
                print(f"✅ Downloaded: {remote_path} → {local_path}")
        except Exception as e:
            logging.error(f"❌ Error copying SSH file to local path:{local_path}: {e}")
            return None   
    
    def write_to_remote_file(self, data, remote_path, file_format="csv"):
        # checks on data
        if isinstance(data, pd.DataFrame):
            if file_format in ["csv", "tsv"]:
                buffer = StringIO()
                data.to_csv(buffer, index=False)
                file_content = buffer.getvalue()
            else:
                raise ValueError("Unsupported file format for DataFrame. Use 'csv'.")
        elif isinstance(data, str):
            file_content = data  # Assume it's plain text?
        else:
            raise TypeError("Data must be a DataFrame or string.")

        try:
            with self._connect(sftp=True) as sftp:       
                with sftp.file(remote_path, "w") as remote_file:
                    remote_file.write(file_content)
                    print(f"✅ Successfully wrote data to {remote_path}")
        except Exception as e:
            logging.error(f"❌ Error writing to remote file: {e}")
            print(f"❌ Error writing to remote file: {e}")

            return None   
    def isfile(self, path):
        try:
            with self._connect(sftp=True) as sftp:
                try:
                    file_stat = sftp.lstat(path)
                    if file_stat.st_mode & 0o170000 == 0o100000:
                        return True
                    else:
                        return False
                except FileNotFoundError:
                    return False
        except Exception as e:
            logging.error(f"Error reading SSH file {path}: {e}")
            return None
        
    def get_file_size(self, path):
        try:
            with self._connect(sftp=True) as sftp:
                file_size = sftp.stat(path).st_size
                return file_size
        except Exception as e:
            logging.error(f"Error reading SSH file {path}: {e}")
            return None
        
