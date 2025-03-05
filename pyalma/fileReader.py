import pysam
import pandas as pd
from io import StringIO

class FileReader:
    """Base class for reading files."""
    # def __init__(self, arg): #later use
    #     self.arg = arg
    
    def read_file(self, path):
        raise NotImplementedError("Subclasses must implement read_file")
    
    def listdir(self, path):
        raise NotImplementedError("Subclasses must implement listdir")

    def read_file_into_df(self, path, type, sep=",", header=None, colnames=[], on_bad_lines='skip'):
        raise NotImplementedError("Subclasses must implement read_file_into_df")
    
    #below two are common functions (i might move them elsewhere later)
    def decode_file_by_type(content, type, sep=",", header='infer', colnames=[], on_bad_lines='skip'):
        """Decodes file content based on type."""
        if len(colnames)>0:
            header = 0
        if type in ['csv', 'tsv', 'bed']:
            return pd.read_csv(StringIO(content.decode('utf-8')), sep=sep, header=header, names=colnames, on_bad_lines=on_bad_lines)
            #elif type == 'vcf':
            #    return pd.read_csv(StringIO(content), comment='#', delimiter='\t')
        else:
            return content
    def read_vcf_file_into_df(path):
        vcf_in = pysam.VariantFile(path)
        return vcf_in