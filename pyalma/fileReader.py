import pysam
import pandas as pd
from io import StringIO
import os
class FileReader:
    """Base class for reading files."""
    # def __init__(self, arg): #later use
    #     self.arg = arg
    
    def read_file(self, path):
        raise NotImplementedError("Subclasses must implement read_file")
    
    def listdir(self, path):
        raise NotImplementedError("Subclasses must implement listdir")

    def read_file_into_df(self, path, type, **kwargs):
        raise NotImplementedError("Subclasses must implement read_file_into_df")
        
    def decode_file_by_type(self, content, type, **kwargs):
        """Decodes file content based on type. Accepts either a file path or a string."""
        # Check if content is a file path or string
        is_path = isinstance(content, str) and os.path.isfile(content)
        if not is_path:
            content = StringIO(content.decode('utf-8'))
            
        if type in ['csv', 'tsv', 'bed']:
            # If it's a string (either file content or path), decode it
            return pd.read_csv(content, **kwargs)
        # elif type == 'vcf':
        #     return pd.read_csv(content, comment='#', delimiter='\t')
        
        return content

    def read_vcf_file_into_df(path):
        vcf_in = pysam.VariantFile(path)
        return vcf_in