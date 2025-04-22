import pandas as pd
from io import BytesIO

def get_doc(content):
    """
    Opens a PDF using PyMuPDF (fitz).

    :param content: File path (str) or binary stream (bytes).
    :type content: str | bytes

    :return: A PyMuPDF Document object.
    :rtype: fitz.Document

    :raises ValueError: If content is neither a valid path nor a binary stream.
    """
    import pymupdf  # PyMuPDF is imported here to avoid unnecessary dependency

    if isinstance(content, (bytes, bytearray)):
        return pymupdf.open(stream=content, filetype="pdf")
    elif isinstance(content, str):
        return pymupdf.open(content)
    else:
        raise ValueError("Invalid content type. Expected a file path or binary stream.")


def read_pdf_to_dataframe(content):
    """
    Extracts structured data from a PDF and loads it into a DataFrame.

    Each row includes:
        - Page number
        - Text content
        - List of extracted images (as bytes)

    :param content: Path to PDF or binary content.
    :type content: str | bytes

    :return: DataFrame with columns ['Page', 'Content', 'Images'].
    :rtype: pd.DataFrame
    """
    doc = get_doc(content)
    data = []

    for i, page in enumerate(doc):
        text = page.get_text("text")
        images = page.get_images(full=True)

        extracted_images = []
        for _, img in enumerate(images):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            extracted_images.append(image_bytes)

        data.append({
            "Page": i + 1,
            "Content": text,
            "Images": extracted_images
        })

    return pd.DataFrame(data)


def read_pdf_as_text(content):
    """
    Extracts plain text from all pages of a PDF.

    Uses PyPDF for simple, reliable text extraction.

    :param content: Binary PDF content.
    :type content: bytes

    :return: Full text content concatenated from all pages.
    :rtype: str
    """
    from pypdf import PdfReader

    pdf_file = BytesIO(content)
    reader = PdfReader(pdf_file)

    return "\n".join(
        page.extract_text() for page in reader.pages if page.extract_text()
    )
