import pysam
import pandas as pd
import os
from io import StringIO
from .pdfreader import read_pdf_to_dataframe
from .anndatareader import read_adata
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
        if self.clean_on_destruction:
            for path in self.files_to_clean:
                self.clean_tmp_files(path)
            print("Resource cleaned.")

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

    def read_file(self, path, type=None):
        """
        Abstract method. Should be implemented by subclasses to read a file.

        :raises NotImplementedError: Always.
        """
        raise NotImplementedError("Subclasses must implement read_file")

    def listdir(self, path):
        """
        Abstract method. Should be implemented by subclasses to list directory contents.

        :raises NotImplementedError: Always.
        """
        raise NotImplementedError("Subclasses must implement listdir")

    def read_file_into_df(self, path, type, **kwargs):
        """
        Abstract method. Should be implemented by subclasses to read a file into a DataFrame.

        :raises NotImplementedError: Always.
        """
        raise NotImplementedError("Subclasses must implement read_file_into_df")

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

    def decode_file_by_type(self, content, type, **kwargs):
        """
        Decodes content based on file type, returning a DataFrame or raw text.

        :param content: Raw content (str or bytes) or file path.
        :type content: str | bytes
        :param type: File type (csv, tsv, pdf, bed).
        :type type: str
        :param kwargs: Extra arguments for `pandas.read_csv`.
        :return: Parsed content.
        :rtype: pd.DataFrame | str
        """
        is_path = isinstance(content, str) and os.path.isfile(content)
        if not is_path and type != "pdf":
            content = StringIO(content.decode( "utf-8"))

        if type in ["csv", "tsv", "bed"]:
            return pd.read_csv(content, **kwargs)

        if type == "pdf":
            return read_pdf_to_dataframe(content)  # Uses the external module
        
        return content.getvalue()

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
