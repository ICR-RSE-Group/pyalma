import pandas as pd
from io import BytesIO

def get_doc(content):
    import pymupdf

    if isinstance(content, (bytes, bytearray)):  # If it's a binary stream <> ssh reading
        doc = pymupdf.open(stream=content, filetype="pdf")
    elif isinstance(content, str):#<> local reading
        doc = pymupdf.open(content)
    else:
        raise ValueError("Invalid content type. Expected a file path or binary stream.")
    return doc

def read_pdf_to_dataframe(content):

    """Reads a PDF file and returns a DataFrame with Page, Content, and Images."""
    # Determine if content is a file path or a binary stream
    doc = get_doc(content)
    data = []

    for i, page in enumerate(doc):
        text = page.get_text("text")  # Extract text separately 
        images = page.get_images(full=True)  # Extract images
        
        extracted_images = []
        for img_index, img in enumerate(images):
            xref = img[0]  # create an image reference
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            extracted_images.append(image_bytes)
        
        data.append({"Page": i + 1, "Content": text, "Images": extracted_images})

    return pd.DataFrame(data)

def read_pdf_as_text(content):
    from pypdf import PdfReader
    """Reads PDF content from bytes and returns extracted text."""
    pdf_file = BytesIO(content)
    reader = PdfReader(pdf_file)
    return "\n".join([page.extract_text() for page in reader.pages])
