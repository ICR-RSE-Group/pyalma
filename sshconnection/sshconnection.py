import os
import paramiko
import logging
import argparse
import pandas as pd
from io import StringIO, BytesIO
from stat import S_ISDIR, S_ISREG
import pysam
import tempfile 
import PyPDF2

# Configure logging for better traceability
logging.basicConfig(level=logging.DEBUG)

class FileReader:
    """Base class for reading files."""
    def read_file(self, path):
        raise NotImplementedError("Subclasses must implement read_file")
    
    def listdir(self, path):
        raise NotImplementedError("Subclasses must implement listdir")

    def read_file_into_df(self, path, type, sep=",", header=None, colnames=[], on_bad_lines='skip'):
        raise NotImplementedError("Subclasses must implement read_file_into_df")

class LocalFileReader(FileReader):
    """Reads local files and executes local commands."""
    def read_file(self, path, type=None):
        try:
            with open(path, 'r') as file:
                content = file.read()
                if type is not None:
                    content = decode_file_by_type(content, type)
                return content
        except Exception as e:
            logging.error(f"Error reading local file {path}: {e}")
            return None
    
    def listdir(self, path):
        try:
            with os.scandir(path) as entries:
                files = [entry.name for entry in entries if entry.is_file()]
                #for some reason entries empty after this loop
            with os.scandir(path) as entries:
                dirs =  [entry.name for entry in entries if entry.is_dir()]
                print(dirs)
            return dirs, files
        except Exception as e:
            logging.error(f"Error listing directory {path}: {e}")
            return []
    
    def run_cmd(self, command):
        try:
            result = os.popen(command).read()
            print(result)
            return {"output": result, "err": None}
        except Exception as e:
            logging.error(f"Error executing command {command}: {e}")
            return {"output": None, "err": str(e)}
    def read_file_into_df(self, path, type, sep=",", header=None, colnames=[], on_bad_lines='skip'):
        try:
            if type == "vcf":
                return read_vcf_file_into_df(path)
            return pd.read_csv(path, sep=sep, header=header, names=colnames, on_bad_lines=on_bad_lines)
        except Exception as e:
            logging.error(f"Error reading local file into DataFrame {path}: {e}")
            return None
class SshConnection(FileReader):
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
    
    def _connect(self):
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(self.server, username=self.username, password=self.password, timeout=30)
        return client
    
    def read_file(self, path, type=None):
        try:
            client = self._connect()
            sftp = client.open_sftp()
            with sftp.file(path, 'r') as file:
                content = file.read()
                if type is not None:
                    content = decode_file_by_type(content, type)
            sftp.close()
            client.close()
            return content
        except Exception as e:
            logging.error(f"Error reading SSH file {path}: {e}")
            return None
    
    def listdir(self, path):
        try:
            client = self._connect()
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
            client = self._connect()
            _, stdout, _ = client.exec_command(command)
            output = stdout.read().decode("ascii")
            client.close()
            return {"output":output,"err":None}
        except Exception as e:
            logging.error(f"Error executing SSH command {command}: {e}")
            return {"output":None,"err":str(e)}

    def read_file_into_df(self, path, type, sep=",", header=None, colnames=[], on_bad_lines='skip'):
        try:
            client = self._connect()
            #Use SFTP to retrieve the file as a Dataframe. sftp is not working for listdir
            sftp = client.open_sftp()
            if type == "vcf":
                with tempfile.TemporaryDirectory() as tmpdirname:
                    print('created temporary directory', tmpdirname)
                    local_file = os.path.join(tmpdirname, "tmp.vcf")
                    sftp.get(path, local_file)
                    return read_vcf_file_into_df(local_file)
            else:
                with sftp.open(path, 'r') as remote_file:
                    file_content = remote_file.read()
                    return decode_file_by_type(file_content, type, sep=sep, header=header, colnames=colnames, on_bad_lines=on_bad_lines)
        except Exception as e:
            logging.error(f"Error reading SSH file into DataFrame {path}: {e}")
            return None
        
def decode_file_by_type(content, type, sep=",", header=None, colnames=[], on_bad_lines='skip'):
    """Decodes file content based on type."""
    if type in ['csv', 'tsv', 'bed']:
        return pd.read_csv(StringIO(content.decode('utf-8')), sep=sep, header=header, names=colnames, on_bad_lines=on_bad_lines)
        #elif type == 'vcf':
        #    return pd.read_csv(StringIO(content), comment='#', delimiter='\t')
    elif type in ["pdf"]:
        pdf_file = BytesIO(content)
        reader = PyPDF2.PdfReader(pdf_file)
        # num_pages = len(reader.pages)
        # if num_pages > 0:
        #     page = reader.pages[0]
        #     print(page.extract_text())  # Extract and print the text from the first page

        return reader
    else:
        return content.decode()
def read_vcf_file_into_df(path):
    vcf_in = pysam.VariantFile(path)
    return vcf_in

def main():
    parser = argparse.ArgumentParser(description="File Reader")
    parser.add_argument("--local", help="Path to local file", type=str)
    parser.add_argument("--ssh", help="Path to remote file", type=str)
    parser.add_argument("--host", help="SSH server", type=str)
    parser.add_argument("--user", help="SSH Username", type=str)
    parser.add_argument("--password", help="SSH Password", type=str)
    parser.add_argument("--cmd", help="Command to execute", type=str)
    
    args = parser.parse_args()
    
    if args.local:
        reader = LocalFileReader()
        content = reader.read_file(args.local)
        if content:
            print("Local File Content:\n", content)
    elif args.ssh and args.host and args.user and args.password:
        reader = SshConnection(args.host, args.user, args.password)
        content = reader.read_file(args.ssh)
        if content:
            print("Remote File Content:\n", content)
    elif args.cmd:
        reader = LocalFileReader()
        output = reader.run_cmd(args.cmd)
        if output:
            print("Command Output:\n", output)
    else:
        print("Invalid arguments. Provide either --local or --ssh with SSH details, or --cmd for command execution.")

if __name__ == "__main__":
    main()
