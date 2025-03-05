import pytest
from unittest import mock
from pyalma import LocalFileReader
import pandas as pd
import tempfile
import os

@pytest.fixture
def csv_file():
    """Fixture to create a temporary CSV file."""
    temp_file = tempfile.NamedTemporaryFile(delete=False, mode='w', newline='', suffix='.csv')
    temp_file.write("col1,col2\n1,2\n3,4\n5,6\n")
    temp_file.close()
    yield temp_file.name
    os.remove(temp_file.name)  # Clean up after test

@pytest.fixture
def tsv_file():
    """Fixture to create a temporary TSV file."""
    temp_file = tempfile.NamedTemporaryFile(delete=False, mode='w', newline='', suffix='.tsv')
    temp_file.write("col1\tcol2\n1\t2\n3\t4\n5\t6\n")
    temp_file.close()
    yield temp_file.name
    os.remove(temp_file.name)  # Clean up after test

def test_read_file_into_df_csv(csv_file):
    reader = LocalFileReader()
    df = reader.read_file_into_df(path=csv_file, type="csv", sep=",", colnames=['col1', 'col2'])
    assert df.shape == (3, 2)  # 3 rows and 2 columns
    assert df.columns.tolist() == ['col1', 'col2']
    assert df.iloc[0, 0] == 1  # First row, first column should be 1
    assert df.iloc[2, 1] == 6  # Last row, last column should be 6

def test_read_file_into_df_tsv(tsv_file):
    reader = LocalFileReader()
    df = reader.read_file_into_df(path=tsv_file, type="csv", sep="\t", colnames=['col1', 'col2'])
    assert df.shape == (3, 2)  # 3 rows and 2 columns
    assert df.columns.tolist() == ['col1', 'col2']
    assert df.iloc[0, 0] == 1  # First row, first column should be 1
    assert df.iloc[2, 1] == 6  # Last row, last column should be 6


@pytest.fixture
def local_file_reader():
    """Fixture to create an instance of LocalFileReader."""
    return LocalFileReader()

def test_run_cmd_success(local_file_reader):
    """Test run_cmd with a successful command."""   
    # Running the command
    result = local_file_reader.run_cmd("echo Hello")
    
    # Checking if the mocked output is correct
    assert result["output"] == "Hello\n"
    assert result["err"] is None

# def test_run_cmd_failure(local_file_reader):
#     """Test run_cmd with a failed command."""
#     reader = LocalFileReader()
#     result = reader.run_cmd("cat dummy")
    
#     # Checking if the error is handled properly
#     assert result["output"] is None
#     assert result["err"] == "dummy: No such file or directory"



