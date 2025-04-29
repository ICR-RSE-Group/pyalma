from pyalma import SshClient, LocalFileReader

def test_read_file(file_reader, base_path):
    pdf_file = base_path + "article.pdf"
    pdf_df = file_reader.read_file_into_df(pdf_file,'pdf')
    print(pdf_df)

    csv_file = base_path + "test.csv"
    csv_df = file_reader.read_file_into_df(csv_file,'csv')
    print(csv_df)

    tsv_file = base_path + "test.tsv"
    tsv_df = file_reader.read_file_into_df(tsv_file,'tsv')
    print(tsv_df)
    
    txt_file = base_path + "test.txt"
    txt_content = file_reader.read_file(txt_file,'txt', as_binary=False)
    print(txt_content)

    img_file = base_path + "image.png"
    res_img= file_reader.read_file(img_file,'png', as_binary=True)
    print(res_img)

remote_path = "/data/scratch/DCO/DIGOPS/SCIENCOM/msarkis/pyalma_test_folder/"
local_path = "/Users/msarkis/Documents/pyalma/pyalma_test_folder/"

local = LocalFileReader()
test_read_file(local, local_path)

remote = SshClient("alma.icr.ac.uk", "msarkis", "lol")
test_read_file(remote, remote_path)