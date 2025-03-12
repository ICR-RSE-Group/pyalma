import pandas as pd
from pypdf import PdfReader
from io import BytesIO

def read_pdf_to_dataframe(path):
    """Reads a PDF file and returns a DataFrame with Page and Content columns."""
    with open(path, "rb") as pdf_file:
        reader = PdfReader(pdf_file) 
        data = [{"Page": i + 1, "Content": page.extract_text()} for i, page in enumerate(reader.pages)]
    return pd.DataFrame(data)

def read_pdf_as_text(content):
    """Reads PDF content from bytes and returns extracted text."""
    pdf_file = BytesIO(content)
    reader = PdfReader(pdf_file)
    return "\n".join([page.extract_text() for page in reader.pages])
