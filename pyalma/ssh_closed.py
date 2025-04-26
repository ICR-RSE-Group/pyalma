import os
import paramiko
import logging
from stat import S_ISDIR, S_ISREG
import tempfile
from .fileReader import FileReader
import pandas as pd
from io import StringIO
import yaml

# Configure logging for debugging and error tracing
logging.basicConfig(level=logging.ERROR)

class SshClientClosed(FileReader):
    """
    SSH-based file reader that extends FileReader to handle file operations over SSH/SFTP.
    Enables reading, writing, listing, and transferring files on a remote server securely.
    This version does not stay alive
    """

    def __init__(self, server="alma.icr.ac.uk", username=None, password=None, sftp="alma-app.icr.ac.uk"):
        """
        Initialize SSH and SFTP connection parameters.

        :param server: Main SSH server address.
        :type server: str
        :param username: SSH username.
        :type username: str
        :param password: SSH password.
        :type password: str
        :param sftp: SFTP host (defaults to `server` if not specified).
        :type sftp: str
        """
        super().__init__()
        self.remote = True
        self.server = server.strip()
        self.sftp = self.server if sftp is None else sftp.strip()
        self.username = username.strip() if username else None
        self.password = password.strip() if password else None
        self.filter_file = os.path.join(os.path.dirname(__file__), "config", "messages.yaml")
        self.filtered_patterns = self._load_filtered_patterns()
        

    def _connect(self, sftp=False):
        """
        Establish SSH and SFTP connections using Paramiko.

        :raises ConnectionError: If authentication or connection fails.
        """
        ssh_client = None
        ssh_client = paramiko.SSHClient()
        ssh_client.load_system_host_keys()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                        
        try:
            if sftp:            
                ssh_client.connect(self.sftp, username=self.username, password=self.password, timeout=30)
                ssh_client = ssh_client.open_sftp()
            else:
                ssh_client.connect(self.server, username=self.username, password=self.password, timeout=30)                
        except paramiko.AuthenticationException:
            raise ConnectionError(f"❌ [_connect]: Authentication failed for {self.username}@{self.server}.")
        except paramiko.SSHException as e:
            raise ConnectionError(f"❌ [_connect]: SSH connection error: {e}")
        except Exception as e:
            raise ConnectionError(f"❌ [_connect]: Unexpected SSH connection error: {e}")
        return ssh_client

    def _load_filtered_patterns(self):
        """
        Load SSH output filter patterns from YAML configuration.

        :return: Filter configuration dictionary.
        :rtype: dict
        """
        try:
            with open(self.filter_file, "r") as file:
                return yaml.safe_load(file) or []
        except Exception as e:
            logging.error(f"❌ [_load_filtered_patterns]: Error loading filter file {self.filter_file}: {e}")
            return []

    def filter_output(self, output):
        """
        Filter SSH command output using predefined patterns.

        :param output: Raw output from SSH command.
        :type output: str
        :return: Filtered output string.
        :rtype: str
        """
        if output != "":
            filters = self.filtered_patterns.get("filters", [])
            return "\n".join(
                line for line in output.splitlines() if not any(line.startswith(f) for f in filters)
            )
        return ""

    def run_cmd(self, command):
        """
        Run a command on the remote server via SSH.

        :param command: Command to execute.
        :type command: str
        :return: Dictionary with 'output' and 'err' keys.
        :rtype: dict
        """
        try:
            with self._connect() as ssh_client:
                _, stdout, _ = ssh_client.exec_command(command)
                output = stdout.read().decode("ascii")
                return {"output": self.filter_output(output), "err": None}  
        except Exception as e:
            logging.error(f"❌ [run_cmd]: Error executing SSH command {command}: {e}")
            return {"output": None, "err": str(e)}

    def load_h5ad_file(self, path, local_path):
        """
        Download an h5ad file from the remote server in chunks.

        :param path: Remote file path.
        :type path: str
        :param local_path: Destination on local machine.
        :type local_path: str
        :return: Local path of the saved file or None if failed.
        :rtype: str | None
        """
        self.files_to_clean.append(local_path)
        try:
            with self._connect(sftp=True) as sftp_client:
                with sftp_client.open(path, 'r') as file:
                    with open(local_path, 'wb') as local_file:
                        file.prefetch()
                        for data in iter(lambda: file.read(32768), b''):
                            local_file.write(data)
                return local_path
        except Exception as e:
            logging.error(f"❌ [load_h5ad_file]: Error reading SSH h5ad file {path}: {e}")
            return None

    def read_file(self, path):
        """
        Read contents of a remote file.

        :param path: Remote file path.
        :type path: str
        :return: Decoded content (DataFrame, string, etc.).
        :rtype: Any
        """
        try:
            with self._connect(sftp=True) as sftp_client:
                with sftp_client.file(path, 'r') as file:
                    file_content = file.read()
                    return self.decode_file_by_type(file_content, self.get_file_extension(path))
        except Exception as e:
            logging.error(f"❌ [read_file]: Error reading SSH file {path}: {e}")
            return None

    def read_file_into_df(self, path, type, **kwargs):
        """
        Read a remote file and convert it into a DataFrame.

        :param path: Path to the remote file.
        :type path: str
        :param type: File type (e.g., 'csv', 'vcf').
        :type type: str
        :param kwargs: Additional keyword arguments for parsing.
        :return: Parsed data as a DataFrame or None.
        :rtype: pd.DataFrame | None
        """
        try:
            with self._connect(sftp=True) as sftp_client:
                if type == "vcf":
                    with tempfile.TemporaryDirectory() as tmpdirname:
                        local_file = os.path.join(tmpdirname, "tmp.vcf")
                        sftp_client.get(path, local_file)
                        return self.read_vcf_file_into_df(local_file)
                else:
                    with sftp_client.open(path, 'rb') as remote_file:
                        file_content = remote_file.read()
                        return self.decode_file_by_type(file_content, type, **kwargs)
        except Exception as e:
            logging.error(f"❌ [read_file_into_df]: Error reading SSH file into DataFrame {path}: {e}")
            return None

    def listdir(self, path):
        """
        List files and directories at a remote path.

        :param path: Remote directory path.
        :type path: str
        :return: Tuple of (directories, files).
        :rtype: tuple[list[str], list[str]]
        """
        try:
            with self._connect(sftp=True) as sftp_client:
                files, directories = [], []
                for entry in sftp_client.listdir_attr(path):
                    if S_ISDIR(entry.st_mode):
                        directories.append(entry.filename)
                    elif S_ISREG(entry.st_mode):
                        files.append(entry.filename)
                return directories, files
        except Exception as e:
            logging.error(f"❌ [listdir]: Error listing SSH directory {path}: {e}")
            return [], []

    def download_remote_file(self, remote_path, local_path):
        """
        Download a remote file via SFTP.

        :param remote_path: Path on the remote server.
        :type remote_path: str
        :param local_path: Local destination path.
        :type local_path: str
        """
        try:
            with self._connect(sftp=True) as sftp_client:
                sftp_client.get(remote_path, local_path)
                print(f"✅ Downloaded: {remote_path} → {local_path}")
        except Exception as e:
            logging.error(f"❌ [download_remote_file]: Error copying SSH file to {local_path}: {e}")
            return None

    def write_to_remote_file(self, data, remote_path, file_format="csv"):
        """
        Write data (string or DataFrame) to a file on the remote server.

        :param data: The data to write.
        :type data: pd.DataFrame | str
        :param remote_path: Destination path on the remote server.
        :type remote_path: str
        :param file_format: Format to use ('csv' supported for DataFrames).
        :type file_format: str
        :raises ValueError: If unsupported DataFrame format is specified.
        :raises TypeError: If data is not string or DataFrame.
        """
        if isinstance(data, pd.DataFrame):
            if file_format in ["csv", "tsv"]:
                buffer = StringIO()
                data.to_csv(buffer, index=False)
                file_content = buffer.getvalue()
            else:
                raise ValueError("❌ [write_to_remote_file]: Unsupported file format for DataFrame. Use 'csv'.")
        elif isinstance(data, str):
            file_content = data
        else:
            raise TypeError("❌ [write_to_remote_file]: Data must be a DataFrame or string.")

        try:
            with self._connect(sftp=True) as sftp_client:
                with sftp_client.open(remote_path, "w") as remote_file:
                    remote_file.write(file_content)
                    print(f"✅ Successfully wrote data to {remote_path}")
        except Exception as e:
            logging.error(f"❌ [write_to_remote_file]: Error writing to remote file: {e}")
            return None

    def isfile(self, path):
        """
        Check whether the given remote path points to a file.

        :param path: Remote path.
        :type path: str
        :return: True if path is a file.
        :rtype: bool
        """
        try:
            with self._connect(sftp=True) as sftp_client:
                file_stat = sftp_client.lstat(path)
                return file_stat.st_mode & 0o170000 == 0o100000
        except Exception as e:
            logging.error(f"❌ [isfile]: Error checking SSH file type {path}: {e}")
            raise

    def get_file_size(self, path):
        """
        Get the size of a file on the remote server.

        :param path: Remote file path.
        :type path: str
        :return: Size in bytes, or None if error.
        :rtype: int | None
        """
        try:
            with self._connect(sftp=True) as sftp_client:
                return sftp_client.stat(path).st_size
        except Exception as e:
            logging.error(f"❌ [get_file_size]: Error reading SSH file size for {path}: {e}")
            return None

    def __del__(self):
        """
        Destructor that closes SSH and SFTP connections and cleans up resources.
        """
        super().__del__()
        
