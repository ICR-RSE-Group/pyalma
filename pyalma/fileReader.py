import pysam
import pandas as pd
import os
from io import StringIO
from .pdfreader import read_pdf_to_dataframe
from .anndatareader import read_adata
class FileReader:
    """Base class for reading files."""
    def __init__(self): 
         self.files_to_clean = []

    def __del__(self):
        for path in self.files_to_clean:
            self.clean_tmp_files(path)
        print('Resource cleaned.')
        
    def read_file(self, path, type=None):
        raise NotImplementedError("Subclasses must implement read_file")

    def listdir(self, path):
        raise NotImplementedError("Subclasses must implement listdir")

    def read_file_into_df(self, path, type, **kwargs):
        raise NotImplementedError("Subclasses must implement read_file_into_df")
    
    def download_remote_file(self, remote_path, local_path):
        raise NotImplementedError("Subclasses doesnt implement download_remote_file")
    
    def write_to_remote_file(self, data, remote_path, file_format="csv"):
        raise NotImplementedError("Subclasses doesnt write_to_remote_file")
    
    def get_file_extension(self, file_path):
        """Extracts and returns the file extension without the leading dot."""
        return os.path.splitext(file_path)[1].lstrip('.') 

    def decode_file_by_type(self, content, type, **kwargs):
        """Decodes file content based on type. Returns a DataFrame or text depending on the type."""
        is_path = isinstance(content, str) and os.path.isfile(content)
        if not is_path and type != "pdf":
            content = StringIO(content.decode('utf-8'))

        if type in ['csv', 'tsv', 'bed']:
            return pd.read_csv(content, **kwargs)

        if type == "pdf":
            return read_pdf_to_dataframe(content)  # Uses the external module
        return content

    def read_vcf_file_into_df(self, path):
        """Reads a VCF file using pysam and returns a VariantFile object."""
        return pysam.VariantFile(path)
    
    def read_h5ad(self, path):
        print("reading h5ad file", path)
        adata = read_adata(path)
        ##accessing a subset of the data
        #subset = adata[:1000, :].X[:]
        return adata
    
    #this is to clean local h5ad files after finish using them
    def clean_tmp_files(self, path):
        os.remove(path)

    def load_h5ad_file(self, path, local_path):
        return path

    def isfile(self, path):
        if not os.path.exists(path):
            return False
        if os.path.isfile(path):
            return True
        return False
