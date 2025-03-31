import os
import paramiko
import logging
from stat import S_ISDIR, S_ISREG
import tempfile
from .fileReader import FileReader
import pandas as pd
from io import StringIO
import yaml

# Configure logging for better traceability
logging.basicConfig(level=logging.DEBUG)

class SshClient(FileReader):
    def __init__(self, server="alma.icr.ac.uk", username=None, password=None, sftp="alma-app.icr.ac.uk"):
        """Initializes the SSH connection instance.
            :param username: SSH username for alma
            :param password: SSH password for alma
            :param server: The remote server address (default is 'alma.icr.ac.uk')
        """
        super().__init__()
        self.remote = True
        self.server = server.strip()
        self.sftp = self.server if sftp is None else sftp.strip()
        self.username = username.strip() if username else None
        self.password = password.strip() if password else None
        self.filter_file = os.path.join(os.path.dirname(__file__), "config", "messages.yaml")
        self.filtered_patterns = self._load_filtered_patterns()
        self._connect()

    def _connect(self):
        # should be called only at initialisation
        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.load_system_host_keys()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.sftp_client = None
        try:
            #one single connection 
            self.ssh_client.connect(self.sftp, username=self.username, password=self.password, timeout=30)
            self.sftp_client = self.ssh_client.open_sftp()
        except paramiko.AuthenticationException:
            raise ConnectionError(f"❌ [_connect]: Authentication failed for {self.username}@{self.server}. Please check your credentials.")
        
        except paramiko.SSHException as e:
            raise ConnectionError(f"❌ [_connect]: SSH connection error: {e}. Please check the server or the SSH configuration.")
        
        except Exception as e:
            raise ConnectionError(f"❌ [_connect]: An unexpected error occurred: {e}")

    def _load_filtered_patterns(self):
        try:
            with open(self.filter_file, "r") as file:
                return yaml.safe_load(file) or []
        except Exception as e:
            logging.error(f"❌ [_load_filtered_patterns]: Error loading filter file {self.filter_file}: {e}")
            return []

    def run_cmd(self, command):
        try:
            stdin, stdout, stderr = self.ssh_client.exec_command(command)
            output = stdout.read().decode("ascii")
            filtered_output = "\n".join(
                line for line in output.split("\n") 
                if not any(line.startswith(_filter) for _filter in self.filtered_patterns)
            )
            return {"output": filtered_output, "err": None}
        except Exception as e:
            logging.error(f"❌ [run_cmd]: Error executing SSH command {command}: {e}")
            return {"output": None, "err": str(e)}

    # specific function for remote anndata reading
    # reads the remote file in chunks and write it to a local file, minimizing memory usage during the transfer.​
    # returns a path to a local file
    def load_h5ad_file(self, path, local_path):
        self.files_to_clean.append(local_path)
        try:
            with self.sftp_client.open(path, 'r') as file:
                with open(local_path, 'wb') as local_file:
                    file.prefetch()
                    for data in iter(lambda: file.read(32768), b''):
                        local_file.write(data)                          
            return local_path
        except Exception as e:
            logging.error(f"❌ [load_h5ad_file]: Error reading SSH h5ad file {path}: {e}")
            return None

    def read_file(self, path):
        try:
            with self.sftp_client.file(path, 'r') as file:
                file_content = file.read()
                return self.decode_file_by_type(file_content, self.get_file_extension(path))
        except Exception as e:
            logging.error(f"❌ [read_file]: Error reading SSH file {path}: {e}")
            return None
    def read_file_into_df(self, path, type, **kwargs):
        try:
            if type == "vcf":
                with tempfile.TemporaryDirectory() as tmpdirname:
                    print('created temporary directory', tmpdirname)
                    local_file = os.path.join(tmpdirname, "tmp.vcf")
                    self.sftp_client.get(path, local_file)
                    return self.read_vcf_file_into_df(local_file)
            else:
                with self.sftp_client.open(path, 'rb') as remote_file:
                    file_content = remote_file.read()
                    return self.decode_file_by_type(file_content, type, **kwargs)
        except Exception as e:
            logging.error(f"❌ [read_file_into_df]: Error reading SSH file into DataFrame {path}: {e}")
            return None

    def listdir(self, path):
        try:
            files, directories = [], []
            for entry in self.sftp_client.listdir_attr(path):
                mode = entry.st_mode
                if S_ISDIR(mode):
                    directories.append(entry.filename)
                elif S_ISREG(mode):
                    files.append(entry.filename)            
            return directories, files
        except Exception as e:
            logging.error(f"❌ [listdir]: Error listing SSH directory {path}: {e}")
            return [], []

    def download_remote_file(self, remote_path, local_path):
        try:
            self.sftp_client.get(remote_path, local_path)
            print(f"✅ Downloaded: {remote_path} → {local_path}")
        except Exception as e:
            logging.error(f"❌ [download_remote_file]: Error copying SSH file to local path:{local_path}: {e}")
            return None

    def write_to_remote_file(self, data, remote_path, file_format="csv"):
        if isinstance(data, pd.DataFrame):
            if file_format in ["csv", "tsv"]:
                buffer = StringIO()
                data.to_csv(buffer, index=False)
                file_content = buffer.getvalue()
            else:
                raise ValueError("Unsupported file format for DataFrame. Use 'csv'.")
        elif isinstance(data, str):
            file_content = data
        else:
            raise TypeError("Data must be a DataFrame or string.")

        try:
            with self.sftp_client.open(remote_path, "w") as remote_file:
                remote_file.write(file_content)
                print(f"✅ Successfully wrote data to {remote_path}")
        except Exception as e:
            logging.error(f"❌ [write_to_remote_file]: Error writing to remote file: {e}")
            return None

    def isfile(self, path):
        try:
            file_stat = self.sftp_client.lstat(path)
            return file_stat.st_mode & 0o170000 == 0o100000
        except Exception as e:
            logging.error(f"❌ [isfile]: Error checking SSH file type {path}: {e}")
            raise

    def get_file_size(self, path):
        try:
            return self.sftp_client.stat(path).st_size
        except Exception as e:
            logging.error(f"❌ [get_file_size]: Error reading SSH file {path}: {e}")
            return None

    def __del__(self):
        super().__del__()#make sure to call parent destructor
        # Ensure we close both SSH and SFTP connections when the object is destroyed
        try:
            if self.sftp_client:
                self.sftp_client.close()
            if self.ssh_client:
                self.ssh_client.close()
        except Exception as e:
            logging.error(f"❌ [__del__]: Error closing SSH/SFTP connections: {e}")
