import pytest
from pyalma import LocalFileReader

@pytest.fixture
def local_file_reader():
    """Fixture to create an instance of LocalFileReader."""
    return LocalFileReader()
def test_read_file_csv_text(local_file_reader, mocker):
    mocker.patch.object(local_file_reader, 'get_file_extension', return_value="csv")
    mocker.patch.object(local_file_reader, '_read_file_content', return_value="a,b\n1,2")
    mocker.patch.object(local_file_reader, 'decode_content_by_type', return_value="decoded_csv")

    result = local_file_reader.read_file("file.csv", as_dataframe=False)
    assert result == "decoded_csv"


def test_read_file_binary_pdf(local_file_reader, mocker):
    mocker.patch.object(local_file_reader, 'get_file_extension', return_value="pdf")
    mocker.patch.object(local_file_reader, '_read_file_content', return_value=b"%PDF-sample")
    mocker.patch.object(local_file_reader, 'decode_content_by_type', return_value="decoded_pdf")

    result = local_file_reader.read_file("file.pdf")
    assert result == "decoded_pdf"


def test_read_file_as_binary_force(local_file_reader, mocker):
    mocker.patch.object(local_file_reader, 'get_file_extension', return_value="csv")
    mocker.patch.object(local_file_reader, '_read_file_content', return_value=b"raw-binary")
    mocker.patch.object(local_file_reader, 'decode_content_by_type', return_value=b"raw-binary")

    result = local_file_reader.read_file("file.csv", as_binary=True)
    assert result == b"raw-binary"


def test_read_file_vcf_as_dataframe(local_file_reader, mocker):
    mock_read_vcf = mocker.patch.object(local_file_reader, '_read_vcf_as_dataframe', return_value="vcf_df")
    result = local_file_reader.read_file("file.vcf", type="vcf", as_dataframe=True)
    mock_read_vcf.assert_called_once_with("file.vcf")
    assert result == "vcf_df"


def test_read_file_error_handling(local_file_reader, mocker):
    mocker.patch.object(local_file_reader, 'get_file_extension', return_value="csv")
    mocker.patch.object(local_file_reader, '_read_file_content', side_effect=Exception("read error"))

    result = local_file_reader.read_file("file.csv")
    assert result is None


def test_read_file_into_df_csv(local_file_reader, mocker):
    mock_read = mocker.patch.object(local_file_reader, 'read_file', return_value="df_result")

    result = local_file_reader.read_file_into_df("file.csv")
    mock_read.assert_called_once_with("file.csv", None, as_dataframe=True, as_binary=False)
    assert result == "df_result"
