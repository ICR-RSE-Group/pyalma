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
    # Mock the 'run_cmd' method of SshClient class
    mock_run_cmd = mocker.patch.object(SshClient, 'run_cmd', return_value="mocked output")

    # Create an instance of SshClient
    ssh_conn = SshClient('host', 'username', 'password')
    
    result = ssh_conn.run_cmd('ls -l')

    assert result == "mocked output"
    
    mock_run_cmd.assert_called_once_with('ls -l')

def test_connection_ssh_exception():
    # Mocking to raise an SSHException
    with mock.patch.object(paramiko.SSHClient, 'connect', side_effect=paramiko.SSHException("SSH error")):
        ssh_connection = SshClient(server='example.com', username='user', password='password')
        
        with pytest.raises(ConnectionError, match="SSH connection error: SSH error"):
            ssh_connection._connect()

def test_connection_authentication_exception():
    # Mocking to raise an AuthenticationException
    with mock.patch.object(paramiko.SSHClient, 'connect', side_effect=paramiko.AuthenticationException):
        ssh_connection = SshClient(server='example.com', username='user', password='wrong_password')
        
        with pytest.raises(ConnectionError, match="Authentication failed for user@example.com"):
            ssh_connection._connect()


