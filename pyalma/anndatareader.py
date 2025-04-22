import scanpy as sc

def read_adata(path):
    """
    Reads an AnnData object from an H5AD file using Scanpy.

    :param path: Path to the `.h5ad` file.
    :type path: str
    :return: The loaded AnnData object.
    :rtype: anndata.AnnData

    :Example:

        >>> adata = read_adata("dataset.h5ad")
        >>> print(adata.shape)  # e.g., (10000, 2000)

    :Notes:

        - If you want to access data without loading it all into memory, 
          consider using ``backed='r'`` with ``sc.read_h5ad(path, backed='r')``.
        - AnnData is a popular format for storing single-cell data.
    """
    adata = sc.read_h5ad(path)
    return adata

