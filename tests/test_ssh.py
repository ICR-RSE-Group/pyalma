import pytest
import paramiko
from pyalma import SshClient
from unittest import mock

# Test case to check if SSH connection is established (mocked)
def test_ssh_connection(mocker):
    # Mock the 'connect' method in your SshClient class
    mock_connect = mocker.patch.object(SshClient, '_connect', return_value=None)
    
    # Create an instance of SshClient
    ssh_conn = SshClient('host', 'username', 'password')
    result = ssh_conn.run_cmd('ls -l')
    # Assert that the connect method was called once
    mock_connect.assert_called_once()

    
# Test case to mock command execution
def test_run_cmd(mocker):
    # Mock the '_connect' method to prevent actual connection attempts
    mocker.patch.object(SshClient, '_connect', return_value=None)

    # mock 'run_cmd'
    mock_run_cmd = mocker.patch.object(SshClient, 'run_cmd', return_value="mocked output")

    ssh_conn = SshClient('host', 'username', 'password')
    
    result = ssh_conn.run_cmd('ls -l')

    assert result == "mocked output"
    mock_run_cmd.assert_called_once_with('ls -l')

def test_connection_ssh_exception():
    # Mocking to raise an SSHException
    with mock.patch.object(paramiko.SSHClient, 'connect', side_effect=paramiko.SSHException("SSH error")):        
        with pytest.raises(ConnectionError, match="SSH connection error: SSH error"):
            SshClient(server='example.com', username='user', password='password')


def test_connection_authentication_exception():
    # Mocking to raise an AuthenticationException
    with mock.patch.object(paramiko.SSHClient, 'connect', side_effect=paramiko.AuthenticationException):
        with pytest.raises(ConnectionError, match="Authentication failed for user@example.com"):
            SshClient(server='example.com', username='user', password='wrong_password')


