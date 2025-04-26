# pyalma/__init__.py
from .cli import main 
from .local import LocalFileReader
from .ssh import SshClient
from .ssh_closed import SshClientClosed
from .pdfreader import read_pdf_to_dataframe,read_pdf_as_text
from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("pyalma")
except PackageNotFoundError:
    __version__ = "unknown"