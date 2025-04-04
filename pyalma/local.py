from .fileReader import FileReader
import logging
import pandas as pd
import os
logging.basicConfig(level=logging.DEBUG)

class LocalFileReader(FileReader):
    """Reads local files and executes local commands."""
    def __init__(self):
        super().__init__()

    #we might consider merging read_file and read_file_into_df
    def read_file(self, path):
        type = self.get_file_extension(path)
        try:
            with open(path, 'r') as file:
                content = file.read()
                return self.decode_file_by_type(content, type)
        except Exception as e:
            logging.error(f"❌ [read_file]: Error reading local file {path}: {e}")
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
            logging.error(f"❌ [listdir]: Error listing directory {path}: {e}")
            return []
    
    def run_cmd(self, command):
        try:
            result = os.popen(command).read()
            print(result)
            return {"output": result, "err": None}
        except Exception as e:
            logging.error(f"❌ [run_cmd]: Error executing command {command}: {e}")
            return {"output": None, "err": str(e)}
        
    def read_file_into_df(self, path, type, **kwargs):
        try:
            if type == "vcf":
                return self.read_vcf_file_into_df(path)
            return self.decode_file_by_type(path, type, **kwargs)
        except Exception as e:
            logging.error(f"❌ [read_file_into_df]: Error reading local file into DataFrame {path}: {e}")
            return None
    def get_local_file_size(file_path):
        """
        Returns the size in bytes.
        """
        if os.path.exists(file_path):
            return os.path.getsize(file_path)
        else:
            logging.error("❌ [get_local_file_size]: Error File not found.")
            return None