from .fileReader import FileReader
import logging
import pandas as pd
import os
logging.basicConfig(level=logging.DEBUG)

class LocalFileReader(FileReader):
    """Reads local files and executes local commands."""
    #def __init__(self, arg):
    #    super().__init__(arg)

    def read_file(self, path):
        try:
            with open(path, 'r') as file:
                return file.read()
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
    def read_file_into_df(self, path, type, **kwargs):
        try:
            if type == "vcf":
                return self.read_vcf_file_into_df(path)
            return pd.read_csv(path, **kwargs)
        except Exception as e:
            logging.error(f"Error reading local file into DataFrame {path}: {e}")
            return None
