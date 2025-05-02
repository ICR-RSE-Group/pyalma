from pyalma import SshClient, LocalFileReader
import pytest
def test_read_file():
    # Simulated SSH container credentials (Docker Compose setup)
    host = "localhost"
    user = "root"
    password = "password"
    port = 2222

    file_reader = SshClient(host, user, password, None, port)
    base_path = "~/remote_files/"

    pdf_file = base_path + "article.pdf"
    pdf_df = file_reader.read_file_into_df(pdf_file, 'pdf')
    print(pdf_df)

    csv_file = base_path + "test.csv"
    csv_df = file_reader.read_file_into_df(csv_file, 'csv')
    print(csv_df)

    tsv_file = base_path + "test.tsv"
    tsv_df = file_reader.read_file_into_df(tsv_file, 'tsv')
    print(tsv_df)

    txt_file = base_path + "test.txt"
    txt_content = file_reader.read_file(txt_file, 'txt', as_binary=False)
    print(txt_content)

    img_file = base_path + "image.png"
    res_img = file_reader.read_file(img_file, 'png', as_binary=True)
    print(res_img)


def test_integration_remote():
    test_read_file()

def test_testuser1_can_run_script():
    ssh = SshClient("localhost", "testuser1", "password1", None, port=2222)
    result = ssh.run_cmd("bash ~/test_data/hello.sh")
    assert "Hello from testuser1" in result["output"]

def test_restricted_user_cannot_run_script():
    ssh = SshClient("localhost", "restricted", "password2", None, port=2222)
    result = ssh.run_cmd("bash ~/test_data/hello.sh")
    print(result)
    assert result["output"] is None

# local_path = "/Users/msarkis/Documents/pyalma/pyalma_test_folder/"
# local = LocalFileReader()
# test_read_file(local, local_path)