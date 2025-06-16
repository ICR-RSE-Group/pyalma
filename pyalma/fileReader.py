import pysam
import pandas as pd
import os
from io import StringIO, BytesIO
from .pdfreader import read_pdf_to_dataframe
from .anndatareader import read_adata
from .imageReader import read_image
import logging

class FileReader:
    """
    Abstract base class for reading and managing different file types, both locally and remotely.

    This class is designed to be subclassed by specific implementations (e.g., local or SSH).
    """

    def __init__(self):
        """
        Initializes the FileReader with default configurations.

            - `files_to_clean`: Tracks temporary files that may need deletion.
            - `remote`: Flag indicating remote operation.
            - `clean_on_destruction`: Determines whether to delete files on object destruction.
        """
        self.files_to_clean = []
        self.remote = False
        self.clean_on_destruction = True

    def __del__(self):
        """
        Destructor to clean up temporary files if clean_on_destruction is enabled.
        """
        try:
            if getattr(self, "clean_on_destruction", False):
                for path in getattr(self, "files_to_clean", []):
                    self.clean_tmp_files(path)
                print("Resource cleaned.")
        except Exception:
            pass

    def is_remote(self):
        """
        Checks if the reader is set to remote mode.

        :return: True if remote, False otherwise.
        :rtype: bool
        """
        return self.remote

    def set_clean_on_dest(self, value):
        """
        Sets the `clean_on_destruction` flag.

        :param value: Enable or disable automatic cleanup.
        :type value: bool
        """
        self.clean_on_destruction = value

    def read_file_into_df(self, path, type=None, as_binary=False, **kwargs):
        """
        File reader into a dataframe for local and remote paths
        :param path: File path.
        :param type: Optional file type override (generic types: pdf, image, text, csv, zip).
        :param as_dataframe: Force a parsing into a DataFrame.
        :param as_binary: Force raw binary return.
        """
        return self.read_file(path, type, as_dataframe=True, as_binary=as_binary, **kwargs)        
    def _is_binary_type(self, type):
        binary_types = {"pdf", "image", "zip", "png", "jpg", "jpeg", "gz"} #list not exhaustive
        return type in binary_types

    def _is_text_type(self, type):
        text_types = {"txt", "text", "out", "log", "err", "json"}
        return type in text_types

    def _is_auto_dataframe_type(self, type):
        #force the below types to be read as dataframe
        dataframe_types = {"csv", "tsv", "bed", "pdf", "vcf"}
        return type in dataframe_types

    def read_file(self, path, type=None, as_dataframe=False, as_binary=False, **kwargs):
        """
        Unified file reader for local or remote paths.
        :param path: File path.
        :param type: Optional file type override (generic types: pdf, image, text, csv, zip).
        :param as_dataframe: Whether to parse into a DataFrame.
        :param as_binary: Force raw binary return.
        """
        type = type or self.get_file_extension(path)
        is_binary = as_binary or self._is_binary_type(type)
        mode = "rb" if is_binary else "r"
        as_dataframe = self._is_auto_dataframe_type(type) or as_dataframe
        try:
            if as_dataframe and type == "vcf":
                return self._read_vcf_as_dataframe(path)
            content = self._read_file_content(path, mode, self._is_text_type(type))
            return self.decode_content_by_type(content, type, as_dataframe, as_binary, **kwargs)

        except Exception as e:
            logging.error(f"❌ [read_file]: Error reading file {path}: {e}")
            return None

    def listdir(self, path):
        """
        Abstract method. Should be implemented by subclasses to list directory contents.

        :raises NotImplementedError: Always.
        """
        raise NotImplementedError("Subclasses must implement listdir")

    def download_remote_file(self, remote_path, local_path):
        """
        Abstract method. Downloads a file from a remote location.

        :raises NotImplementedError: Always.
        """
        raise NotImplementedError("Subclasses must implement download_remote_file")

    def write_to_remote_file(self, data, remote_path, file_format="csv"):
        """
        Abstract method. Writes data to a remote file.

        :param data: Data to write.
        :param remote_path: Path on remote server.
        :param file_format: File format, default is 'csv'.
        :raises NotImplementedError: Always.
        """
        raise NotImplementedError("Subclasses must implement write_to_remote_file")

    def get_file_extension(self, file_path):
        """
        Extracts the file extension from a given path.

        :param file_path: Full path to the file.
        :type file_path: str

        :return: File extension without the dot.
        :rtype: str
        """
        return os.path.splitext(file_path)[1].lstrip('.')

    def decode_content_by_type(self, content, type, as_dataframe = False, as_binary=False, **kwargs):
        """
        Decodes content based on file type, returning a DataFrame or raw string.

        :param content: Raw content (str, bytes, or file path).
        :param type: File type (file extension generic types: pdf, image, text, csv, zip).
        :param kwargs: Extra arguments for `pandas.read_csv`.
        :return: Decoded content (DataFrame, str, or bytes).
        """
        if type in ["csv", "tsv", "bed"]:
            # Accepts both string/bytes or file-like
            is_path = isinstance(content, str) and os.path.isfile(content)
            if not is_path:
                content = StringIO(content.decode( "utf-8"))
            #sep = kwargs.get('sep', "\t" if type in ["tsv", "bed"] else ",")
            return pd.read_csv(content, **kwargs)

        if type == "pdf":
            return read_pdf_to_dataframe(BytesIO(content) if isinstance(content, bytes) else content)
        
        if type in ["png", "jpg", "jpeg"]:
            try:
                return read_image(content)
            except Exception as e:
                logging.error(f"❌ [decode_content_by_type]: Failed to decode image: {e}")
                return content
            
        # Fallbacks, mainly for images or zipped files
        if isinstance(content, bytes) and not as_binary:
            try:
                return content.decode("utf-8")
            except UnicodeDecodeError:
                return content  # binary fallback
        return content

    def read_vcf_file_into_df(self, path):
        """
        Reads a VCF (Variant Call Format) file using `pysam`.

        :param path: Path to the VCF file.
        :type path: str

        :return: VCF file as a `pysam.VariantFile` object.
        :rtype: pysam.VariantFile
        """
        return pysam.VariantFile(path)

    def read_h5ad(self, path):
        """
        Reads an H5AD file using `anndatareader`.

        :param path: Path to the `.h5ad` file.
        :type path: str

        :return: Loaded `AnnData` object.
        :rtype: AnnData
        """
        print("reading h5ad file", path)
        adata = read_adata(path)
        return adata

    def clean_tmp_files(self, path):
        """
        Deletes a temporary file.

        :param path: Path to the file to delete.
        :type path: str
        """
        os.remove(path)

    def clean_tmp_files(self, path):
        """
        Deletes a temporary file if it exists.

        :param path: Path to the file to delete.
        :type path: str
        """

        if os.path.isfile(path):
            os.remove(path)
            logging.info(f"✅ [clean_tmp_files]: Deleted file {path}")
        else:
            logging.warning(f"⚠️ [clean_tmp_files]: Path does not exist or is not a file: {path}")

    def load_h5ad_file(self, path, local_path):
        """
        Placeholder for remote/local logic in loading H5AD files.

        :param path: Path to the file.
        :param local_path: Local destination path.
        :type path: str
        :type local_path: str

        :return: Path to use.
        :rtype: str
        """
        return path

    def isfile(self, path):
        """
        Checks if a given path exists and is a file.

        :param path: Path to check.
        :type path: str

        :return: True if path exists and is a file.
        :rtype: bool
        """
        return os.path.exists(path) and os.path.isfile(path)

    def get_file_size(self, path):
        """
        Placeholder to get file size.

        :param path: Path to the file.
        :type path: str

        :return: File size (to be implemented).
        :rtype: None
        """
        pass
