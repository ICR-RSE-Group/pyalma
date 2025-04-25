from .fileReader import FileReader
import logging
import os

# Enable basic logging for debugging
logging.basicConfig(level=logging.DEBUG)
class LocalFileReader(FileReader):
    """
    Local file system implementation of FileReader.

    This class provides functionality to:

        - Read files from the local filesystem
        - Load file contents into pandas DataFrames
        - List directory contents
        - Execute shell commands locally
    """

    def __init__(self):
        """
        Initializes an instance of LocalFileReader.
        """
        super().__init__()

    def listdir(self, path):
        """
        Lists directories and files in a given local directory path.

        :param path: Directory path to list contents from.
        :type path: str

        :return: A tuple containing a list of subdirectories and a list of files.
        :rtype: tuple[list[str], list[str]]
        """
        try:
            with os.scandir(path) as entries:
                files = [entry.name for entry in entries if entry.is_file()]

            with os.scandir(path) as entries:
                dirs = [entry.name for entry in entries if entry.is_dir()]
                print(dirs)

            return dirs, files
        except Exception as e:
            logging.error(f"❌ [listdir]: Error listing directory {path}: {e}")
            return []

    def run_cmd(self, command):
        """
        Executes a shell command locally and returns its output.

        :param command: Command string to execute.
        :type command: str

        :return: Dictionary with 'output' and 'err' keys.
        :rtype: dict
        """
        try:
            result = os.popen(command).read()
            print(result)
            return {"output": result, "err": None}
        except Exception as e:
            logging.error(f"❌ [run_cmd]: Error executing command {command}: {e}")
            return {"output": None, "err": str(e)}

    def _read_file_content(self, path, mode, is_text):
        """
        Smart file content reader.
        - For text files: reads and returns content.
        - For non-text (binary) files or for csv files: returns path to be handled later by decode_content_by_type.
        """
        if is_text:
            with open(path, mode) as f:
                return f.read()
        return path

    def _read_vcf_as_dataframe(self, path):
        return self.read_vcf_file_into_df(path)

    @staticmethod
    def get_local_file_size(file_path):
        """
        Returns the size of a local file in bytes.

        :param file_path: Path to the file.
        :type file_path: str

        :return: File size in bytes or None if the file doesn't exist.
        :rtype: int | None
        """
        if os.path.exists(file_path):
            return os.path.getsize(file_path)
        else:
            logging.error("❌ [get_local_file_size]: Error File not found.")
            return None
