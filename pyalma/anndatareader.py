import scanpy as sc

def read_adata(path):
    adata = sc.read_h5ad(path)#, backed='r')
    ## For example, accessing a subset of the data
    #subset = adata[:1000, :].X[:]
    return adata



