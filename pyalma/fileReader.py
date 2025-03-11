import pysam
import pandas as pd
from io import StringIO, BytesIO
import os
from pypdf import PdfReader

class FileReader:
    """Base class for reading files."""
    # def __init__(self, arg): #later use
    #     self.arg = arg
    
    def read_file(self, path, type = None):
        raise NotImplementedError("Subclasses must implement read_file")
    
    def listdir(self, path):
        raise NotImplementedError("Subclasses must implement listdir")

    def read_file_into_df(self, path, type, **kwargs):
        raise NotImplementedError("Subclasses must implement read_file_into_df")
    
    def get_file_extension(self, file_path):
        return os.path.splitext(file_path)[1].lstrip('.') 
    
    # def read_pdf_asText(content):
    #     pdf_file = BytesIO(content)
    #     reader = PyPDF2.PdfReader(pdf_file)
        
    #     text = ""
    #     for page in reader.pages:  # Iterate through all pages
    #         text += page.extract_text() + "\n"  
    #     return text 
    
    def read_pdf_to_dataframe(self, path):
        """Returns a DataFrame with Page and Content columns"""
        with open(path, "rb") as pdf_file:
            reader = PdfReader(pdf_file) 
            data = [] 
            for i, page in enumerate(reader.pages):  
                text = page.extract_text()
                data.append({"Page": i + 1, "Content": text})  
            df = pd.DataFrame(data)
            return df  
    
    def decode_file_by_type(self, content, type, **kwargs):
        """Decodes file content based on type. Accepts either a file path or a string.
        return a dataframe or text depending on the type.
        By default, it returns text
        """
        # Check if content is a file path or string
        is_path = isinstance(content, str) and os.path.isfile(content)
        if not is_path:
            content = StringIO(content.decode('utf-8'))
            
        if type in ['csv', 'tsv', 'bed']:
            # If it's a string (either file content or path), decode it
            return pd.read_csv(content, **kwargs)
        # if type == 'vcf':
        #     return pd.read_csv(content, comment='#', delimiter='\t')
        if type in ["pdf"]:
            return self.read_pdf_to_dataframe(content)
        
        return content

    def read_vcf_file_into_df(path):
        vcf_in = pysam.VariantFile(path)
        return vcf_in