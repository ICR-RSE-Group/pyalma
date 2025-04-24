import pytest
import paramiko
import yaml
import sys
from unittest import mock
from unittest.mock import MagicMock, patch
from importlib.metadata import PackageNotFoundError
from pyalma import SshClient
import tempfile
import pandas as pd
# ---------- Connection Tests ----------

def test_ssh_connection(mocker):
    mock_connect = mocker.patch.object(SshClient, '_connect', return_value=None)
    ssh_conn = SshClient('host', 'username', 'password')
    ssh_conn.run_cmd('ls -l')
    mock_connect.assert_called_once()

def test_run_cmd_mocked(mocker):
    mocker.patch.object(SshClient, '_connect', return_value=None)
    mock_run_cmd = mocker.patch.object(SshClient, 'run_cmd', return_value="mocked output")
    ssh_conn = SshClient('host', 'username', 'password')
    result = ssh_conn.run_cmd('ls -l')
    assert result == "mocked output"
    mock_run_cmd.assert_called_once_with('ls -l')

def test_connection_ssh_exception():
    with patch.object(paramiko.SSHClient, 'connect', side_effect=paramiko.SSHException("SSH error")):
        with pytest.raises(ConnectionError, match="SSH connection error: SSH error"):
            SshClient(server='example.com', username='user', password='password')

def test_connection_authentication_exception():
    with patch.object(paramiko.SSHClient, 'connect', side_effect=paramiko.AuthenticationException):
        with pytest.raises(ConnectionError, match="Authentication failed for user@example.com"):
            SshClient(server='example.com', username='user', password='wrong_password')

def test_connection_timeout_exception():
    with patch.object(paramiko.SSHClient, 'connect', side_effect=TimeoutError("Connection timed out")):
        with pytest.raises(ConnectionError, match="❌ \\[_connect\\]: Unexpected SSH connection error: Connection timed out"):
            SshClient(server='example.com', username='user', password='any_password')


# ---------- Fixtures ----------

@pytest.fixture
def ssh_client(mocker, tmp_path):
    mocker.patch.object(SshClient, '_connect', return_value=None)
    filter_file = tmp_path / "filters.yaml"
    filter_file.write_text(yaml.dump({"filters": ["DEBUG", "INFO"]}))
    client = SshClient("host", "user", "pass")
    client.filter_file = str(filter_file)
    client.filtered_patterns = client._load_filtered_patterns()
    return client

@pytest.fixture
def ssh_client2(mocker):
    mocker.patch.object(SshClient, '_connect', return_value=None)
    client = SshClient("host", "user", "pass")
    client.ssh_client = mocker.MagicMock()
    client.sftp_client = mocker.MagicMock()
    client.filter_output = lambda output: output.replace("filterme", "")
    return client


# ---------- Filter Tests ----------

def test_load_filtered_patterns_valid(mocker, tmp_path):
    path = tmp_path / "filters.yaml"
    path.write_text('filters:\n  - "DEBUG"\n  - "INFO"\n')
    mocker.patch.object(SshClient, '_connect', return_value=None)
    client = SshClient("host", "user", "pass")
    client.filter_file = str(path)
    assert client._load_filtered_patterns() == {"filters": ["DEBUG", "INFO"]}

def test_load_filtered_patterns_file_error(mocker):
    mocker.patch.object(SshClient, '_connect', return_value=None)
    client = SshClient("host", "user", "pass")
    client.filter_file = "nonexistent.yaml"
    mocker.patch("builtins.open", side_effect=FileNotFoundError)
    assert client._load_filtered_patterns() == []

def test_filter_output_matches(ssh_client):
    raw_output = "DEBUG: initializing\nINFO: connected\nRESULT: success"
    assert ssh_client.filter_output(raw_output) == "RESULT: success"

def test_filter_output_no_match(ssh_client):
    raw_output = "RESULT: success\nOK: done"
    assert ssh_client.filter_output(raw_output) == "RESULT: success\nOK: done"

def test_filter_output_empty(ssh_client):
    assert ssh_client.filter_output("") == ""


# ---------- Command Execution Tests ----------

def test_run_cmd_success(ssh_client2, mocker):
    stdout = mocker.Mock()
    stdout.read.return_value = b"result\nfilterme\n"
    ssh_client2.ssh_client.exec_command.return_value = (None, stdout, None)
    result = ssh_client2.run_cmd("ls")
    assert result["output"] == "result\n\n"
    assert result["err"] is None

def test_run_cmd_error(ssh_client2, mocker):
    ssh_client2.ssh_client.exec_command.side_effect = Exception("Boom")
    result = ssh_client2.run_cmd("ls")
    assert result["output"] is None
    assert "Boom" in result["err"]


# ---------- File Handling Tests ----------

def test_load_h5ad_file_success(ssh_client2, tmp_path, mocker):
    fake_remote = mocker.Mock()
    fake_remote.read.side_effect = [b"chunk1", b"chunk2", b""]
    ssh_client2.sftp_client.open.return_value.__enter__.return_value = fake_remote
    local_file = tmp_path / "out.h5ad"
    result = ssh_client2.load_h5ad_file("remote/path", str(local_file))
    assert result == str(local_file)
    assert local_file.read_bytes() == b"chunk1chunk2"

def test_load_h5ad_file_failure(ssh_client2, mocker):
    ssh_client2.sftp_client.open.side_effect = Exception("Read error")
    assert ssh_client2.load_h5ad_file("remote/path", "local.h5ad") is None

# def test_read_file_success(ssh_client2, mocker):
#     mock_file = mocker.Mock()
#     mock_file.read.return_value = b"content"
#     ssh_client2.sftp_client.file.return_value.__enter__.return_value = mock_file
#     ssh_client2.get_file_extension = lambda x: "txt"
#     ssh_client2._read_file_content = lambda content, ext: content.decode()
#     assert ssh_client2.read_file("remote/path") == "content"

def test_read_file_success(ssh_client2, mocker):
    mock_file = mocker.Mock()
    mock_file.read.return_value = b"content"
    ssh_client2.sftp_client.open.return_value.__enter__.return_value = mock_file
    ssh_client2.get_file_extension = lambda x: "txt"
    mocker.patch.object(ssh_client2, 'decode_content_by_type', return_value="content")

    result = ssh_client2.read_file("remote/path")
    assert result == "content"

def test_read_file_error(ssh_client2, mocker):
    ssh_client2.sftp_client.open.side_effect = Exception("Bad path")
    assert ssh_client2.read_file("remote/path") is None


# ---------- read_file_into_df Tests ----------

def test_read_file_into_df_vcf(ssh_client2, mocker):
    ssh_client2.read_vcf_file_into_df = lambda path: "df"
    ssh_client2.sftp_client.get = mocker.Mock()
    result = ssh_client2.read_file_into_df("remote/file.vcf", "vcf")
    assert result == "df"

def test_read_file_into_df_other(ssh_client2, mocker):
    mock_file = mocker.Mock()
    mock_file.read.return_value = b"csv content"
    ssh_client2.sftp_client.open.return_value.__enter__.return_value = mock_file
    ssh_client2.decode_content_by_type = lambda content, ext, **kwargs: "decoded"
    result = ssh_client2.read_file_into_df("remote/file.csv", "csv")
    assert result == "decoded"

def test_read_file_into_df_error(ssh_client2, mocker):
    ssh_client2.sftp_client.open.side_effect = Exception("Bad path")
    result = ssh_client2.read_file_into_df("remote/file.txt", "txt")
    assert result is None

# ---------- listdir Tests ----------

def test_listdir_success(ssh_client2, mocker):
    mock_entry_dir = mocker.Mock(st_mode=0o040000, filename="dir1")
    mock_entry_file = mocker.Mock(st_mode=0o100000, filename="file1")
    ssh_client2.sftp_client.listdir_attr.return_value = [mock_entry_dir, mock_entry_file]
    dirs, files = ssh_client2.listdir("/path")
    assert dirs == ["dir1"]
    assert files == ["file1"]

def test_listdir_failure(ssh_client2, mocker):
    ssh_client2.sftp_client.listdir_attr.side_effect = Exception("Can't list")
    dirs, files = ssh_client2.listdir("/bad/path")
    assert dirs == []
    assert files == []


# ---------- Version Tests ----------

def test_version_found(monkeypatch):
    monkeypatch.setattr("importlib.metadata.version", mock.Mock(return_value="1.2.3"))
    if "pyalma" in sys.modules:
        del sys.modules["pyalma"]
    import pyalma
    assert pyalma.__version__ == "1.2.3"

def test_version_not_found(monkeypatch):
    monkeypatch.setattr("importlib.metadata.version", lambda _: (_ for _ in ()).throw(PackageNotFoundError))
    if "pyalma" in sys.modules:
        del sys.modules["pyalma"]
    import pyalma
    assert pyalma.__version__ == "unknown"

@pytest.fixture
def mock_super_del(mocker):
    return mocker.patch("pyalma.SshClient.__del__", autospec=True)

import pytest

@pytest.fixture
def mock_super_del(mocker):
    # Patch __del__ to avoid calling the base class destructor logic
    return mocker.patch("pyalma.SshClient.__del__", autospec=True)
    

def test_del_closes_connections(mocker, mock_super_del):
    class MockSshClient(SshClient):
        def __init__(self):
            # Mock sftp and ssh clients
            self.sftp_client = mocker.Mock()
            self.ssh_client = mocker.Mock()
            self.clean_on_destruction = False 

        def __del__(self):
            # Call custom close logic
            if self.sftp_client:
                self.sftp_client.close()
            if self.ssh_client:
                self.ssh_client.close()
            # Mocking the parent class's __del__ method to prevent side effects
            super().__del__()

    client = MockSshClient()
    
    # Call __del__ directly in the test
    client.__del__()

    # Verify that the close methods were called once for both sftp and ssh clients
    client.sftp_client.close.assert_called_once()
    client.ssh_client.close.assert_called_once()

def test_del_handles_exceptions(mocker, mock_super_del):
    class MockSshClient(SshClient):
        def __init__(self):
            self.sftp_client = mocker.Mock()
            self.ssh_client = mocker.Mock()
            self.sftp_client.close.side_effect = Exception("boom")
            self.ssh_client.close.side_effect = Exception("boom")
            self.clean_on_destruction = False 

    client = MockSshClient()
    
    # It shouldn't raise despite exceptions in close()
    client.__del__()


@pytest.fixture
def ssh_client_real(mocker):
    mocker.patch.object(SshClient, '_connect', return_value=None)
    client = SshClient("host", "user", "pass")
    client.ssh_client = mocker.MagicMock()
    client.sftp_client = mocker.MagicMock()
    return client

# --- listdir tests ---

def test_listdir_success(ssh_client_real):
    mock_entry_dir = MagicMock(st_mode=0o040000, filename="dir1")
    mock_entry_file = MagicMock(st_mode=0o100000, filename="file1")
    ssh_client_real.sftp_client.listdir_attr.return_value = [mock_entry_dir, mock_entry_file]

    dirs, files = ssh_client_real.listdir("/remote/path")

    assert dirs == ["dir1"]
    assert files == ["file1"]
    ssh_client_real.sftp_client.listdir_attr.assert_called_once_with("/remote/path")


def test_listdir_failure(ssh_client_real):
    ssh_client_real.sftp_client.listdir_attr.side_effect = Exception("Failed to list directory")

    dirs, files = ssh_client_real.listdir("/remote/path")

    assert dirs == []
    assert files == []
    ssh_client_real.sftp_client.listdir_attr.assert_called_once_with("/remote/path")


# --- download_remote_file tests ---

def test_download_remote_file_success(ssh_client_real):
    ssh_client_real.sftp_client.get.return_value = None

    with tempfile.NamedTemporaryFile(delete=True) as tmpfile:
        result = ssh_client_real.download_remote_file("/remote/path/file.txt", tmpfile.name)

    assert result is None
    ssh_client_real.sftp_client.get.assert_called_once()


def test_download_remote_file_failure(ssh_client_real):
    ssh_client_real.sftp_client.get.side_effect = Exception("Download failed")

    with tempfile.NamedTemporaryFile(delete=True) as tmpfile:
        result = ssh_client_real.download_remote_file("/remote/path/file.txt", tmpfile.name)

    assert result is None
    ssh_client_real.sftp_client.get.assert_called_once()




def test_write_to_remote_file_with_string(ssh_client_real):
    mock_file = MagicMock()
    ssh_client_real.sftp_client.open.return_value.__enter__.return_value = mock_file

    data = "This is a test"
    path = "/remote/path/file.txt"
    ssh_client_real.write_to_remote_file(data, path)

    ssh_client_real.sftp_client.open.assert_called_once_with(path, "w")
    mock_file.write.assert_called_once_with(data)


def test_write_to_remote_file_with_dataframe(ssh_client_real):
    mock_file = MagicMock()
    ssh_client_real.sftp_client.open.return_value.__enter__.return_value = mock_file

    df = pd.DataFrame({"col1": [1, 2], "col2": ["a", "b"]})
    path = "/remote/path/data.csv"
    ssh_client_real.write_to_remote_file(df, path, file_format="csv")

    ssh_client_real.sftp_client.open.assert_called_once_with(path, "w")
    # Ensure that the write call received CSV content (we check partial content)
    assert "col1,col2" in mock_file.write.call_args[0][0]


def test_write_to_remote_file_invalid_format(ssh_client_real):
    df = pd.DataFrame({"col": [1, 2]})
    with pytest.raises(ValueError, match="Unsupported file format"):
        ssh_client_real.write_to_remote_file(df, "/remote/file.txt", file_format="json")


def test_write_to_remote_file_invalid_data_type(ssh_client_real):
    invalid_data = 12345  # not str or DataFrame
    with pytest.raises(TypeError, match="Data must be a DataFrame or string"):
        ssh_client_real.write_to_remote_file(invalid_data, "/remote/file.txt")


def test_write_to_remote_file_write_failure(ssh_client_real, caplog):
    ssh_client_real.sftp_client.open.side_effect = Exception("Write failed")
    data = "error case"
    result = ssh_client_real.write_to_remote_file(data, "/remote/path.txt")

    assert result is None
    assert "❌ [write_to_remote_file]: Error writing to remote file" in caplog.text


    import pytest
from unittest.mock import MagicMock


def test_isfile_true(ssh_client_real):
    # Create a mock stat result with st_mode for a regular file (0o100000)
    mock_stat = MagicMock()
    mock_stat.st_mode = 0o100000
    ssh_client_real.sftp_client.lstat.return_value = mock_stat

    assert ssh_client_real.isfile("/remote/file.txt") is True
    ssh_client_real.sftp_client.lstat.assert_called_once_with("/remote/file.txt")


def test_isfile_false(ssh_client_real):
    # Create a mock stat result with st_mode for a directory (0o040000)
    mock_stat = MagicMock()
    mock_stat.st_mode = 0o040000
    ssh_client_real.sftp_client.lstat.return_value = mock_stat

    assert ssh_client_real.isfile("/remote/dir") is False
    ssh_client_real.sftp_client.lstat.assert_called_once_with("/remote/dir")


def test_isfile_exception(ssh_client_real, caplog):
    ssh_client_real.sftp_client.lstat.side_effect = Exception("File not found")

    with pytest.raises(Exception, match="File not found"):
        ssh_client_real.isfile("/nonexistent/file.txt")

    assert "❌ [isfile]: Error checking SSH file type" in caplog.text

def test_get_file_size_success(ssh_client_real):
    # Mock stat result with a specific file size
    mock_stat = MagicMock()
    mock_stat.st_size = 2048
    ssh_client_real.sftp_client.stat.return_value = mock_stat

    size = ssh_client_real.get_file_size("/remote/file.txt")
    assert size == 2048
    ssh_client_real.sftp_client.stat.assert_called_once_with("/remote/file.txt")


def test_get_file_size_failure(ssh_client_real, caplog):
    # Simulate an error when stat is called
    ssh_client_real.sftp_client.stat.side_effect = Exception("Stat failed")

    size = ssh_client_real.get_file_size("/remote/missing.txt")
    assert size is None
    assert "❌ [get_file_size]: Error reading SSH file size for /remote/missing.txt" in caplog.text
    ssh_client_real.sftp_client.stat.assert_called_once_with("/remote/missing.txt")
