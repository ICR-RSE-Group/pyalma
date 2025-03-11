import pysam
import pandas as pd
import os
from io import StringIO
from .pdfreader import read_pdf_to_dataframe

class FileReader:
    """Base class for reading files."""
    # def __init__(self, arg): #later use
    #     self.arg = arg
    def read_file(self, path, type=None):
        raise NotImplementedError("Subclasses must implement read_file")

    def listdir(self, path):
        raise NotImplementedError("Subclasses must implement listdir")

    def read_file_into_df(self, path, type, **kwargs):
        raise NotImplementedError("Subclasses must implement read_file_into_df")

    def get_file_extension(self, file_path):
        """Extracts and returns the file extension without the leading dot."""
        return os.path.splitext(file_path)[1].lstrip('.') 

    def decode_file_by_type(self, content, type, **kwargs):
        """Decodes file content based on type. Returns a DataFrame or text depending on the type."""
        is_path = isinstance(content, str) and os.path.isfile(content)
        if not is_path and type is not "pdf":
            content = StringIO(content.decode('utf-8'))

        if type in ['csv', 'tsv', 'bed']:
            return pd.read_csv(content, **kwargs)

        if type == "pdf":
            return read_pdf_to_dataframe(content)  # Uses the external module

        return content

    def read_vcf_file_into_df(self, path):
        """Reads a VCF file using pysam and returns a VariantFile object."""
        return pysam.VariantFile(path)
