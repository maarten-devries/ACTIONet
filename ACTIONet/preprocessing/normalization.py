from typing import Optional, Union

from anndata import AnnData

from .. import tools as tl


def normalize(
        adata: AnnData,
        layer_key: Optional[str] = None,
        layer_key_out: Optional[str] = None,
        log_transform: Optional[bool] = True,
        scale_factor: Union[str, float, int, None] = "median",
        copy: Optional[bool] = False,
        ) -> Optional[AnnData]:
    adata = adata.copy() if copy else adata

    # if layer_key is not None:
    #     S = tl.normalize_matrix(adata.layers[layer_key], log_transform=log_transform, scale_factor=scale_factor)
    # else:
    #     S = tl.normalize_matrix(adata.X, log_transform=log_transform, scale_factor=scale_factor)

    if layer_key is not None:
        X = adata.layers[layer_key]
    else:
        X = adata.X

    S = tl.normalize_matrix(X, log_transform=log_transform, scale_factor=scale_factor)

    if layer_key_out is not None:
        adata.layers[layer_key_out] = S
    else:
        adata.X = S

    return adata if copy else None