from PIL import Image
from io import BytesIO
 
                
def read_image(content):
    return Image.open(BytesIO(content)) if isinstance(content, bytes) else Image.open(content)
