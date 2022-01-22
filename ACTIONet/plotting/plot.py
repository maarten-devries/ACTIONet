from typing import Optional, Union
import plotly as pl
import plotly.io as pio
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import plotly.express as px
import numpy as np
from adjustText import adjust_text
from anndata import AnnData
from scipy import sparse
import pandas as pd
from random import sample
from .color import *
from .palettes import palette_default
from ..tools import utils_public as ut
from . import utils as pu
import _ACTIONet as _an

pio.orca.config.use_xvfb = True
pio.orca.config.save()


def validate_plot_params(adata, coordinate_key, label_key, transparency_key):
    if coordinate_key not in adata.obsm.keys():
        raise ValueError(
            f"Did not find adata.obsm['{coordinate_key}']. "
            "Please run nt.layoutNetwork() first."
        )
    if label_key is not None and label_key not in adata.obs.columns:
        raise ValueError(f"Did not find adata.obs['{label_key}'].")
    if transparency_key is not None and transparency_key not in adata.obs.columns:
        raise ValueError(f"Did not find adata.obs['{transparency_key}'].")
    if (
        transparency_key is not None
        and pd.api.types.is_numeric_dtype(adata.obs[transparency_key].dtype) is False
    ):
        raise ValueError(
            f"transparency_key must refer to a numeric values, which is not the case for['{transparency_key}']."
        )


def plot_ACTIONet(
    data: Union[AnnData, pd.DataFrame, np.ndarray],
    label_attr: Union[str, list, pd.Series, None] = None,
    color_attr: Union[str, list, pd.Series, pd.DataFrame, np.ndarray, None] = None,
    trans_attr: Union[str, list, pd.Series, np.ndarray, None] = None,
    trans_fac: Optional[float] = 1.5,
    trans_th: Optional[float] = -0.5,
    point_size: Optional[float] = 3,
    stroke_size: Optional[float] = 0.3,
    stroke_contrast_fac: Optional[float] = 1.2,
    palette: Union[str, list, pd.Series, dict] = palette_default,
    show_legend: Optional[bool] = None,
    hover_text: Union[list, pd.Series, np.ndarray] = None,
    plot_3d: Optional[bool] = False,
    point_order: Union[list, pd.Series, np.ndarray] = None,
    coordinate_key: Optional[str] = None,
    color_key: Optional[str] = "denovo_color",
) -> go.Figure:
    """Creates an interactive ACTIONet plot with plotly
    :param data:AnnData object with coordinates in '.obsm[coordinate_key]' or numeric matrix of X-Y(-Z) coordinates. \
        If data is AnnData, 'coordinate_key' defaults to 'ACTIONet3D' if 'plot_3d=True' or 'ACTIONet2D' if otherwise.
    :param label_attr: list-like object of length data.shape[0] or key of '.obs' containing cell labels of interest (clusters, cell types, etc.).
    :param color_attr: list-like object of length data.shape[0], matrix-like object of RGB values, or key of '.obs' containing point-wise color mappings.
    :param trans_attr: list-like object of length data.shape[0] or key of '.obs' of relative numerical values for computing point transparency. \
        Smaller values are more transparent.
    :param trans_fac: Transparency modifier (default:1.5)
    :param trans_th:Minimum transparency Z-score under which points are masked (default:-0.5).
    :param point_size:Size of points in plotly figure (default:3).
    :param stroke_size: Size of points outline (stroke) in plotly figure (default:0.3).
    :param stroke_contrast_fac: Factor by which to lighten (if < 1) darken (if > 1) point outline for contrast (default:1.2).
    :param palette: color palette for labeled data. One of the following \
        list-like object of color values to assign to each plotly trace alphabetically by label. \
        dict of color values with keys corresponding to members of 'plot_labels'.
    :param show_legend: Show legend for labeled data. Ignored if 'label_attr=None'.
    :param hover_text: list-like object of length data.shape[0] pto use for plotly figure hover text. \
        If defaults to point values given by 'label_attr' or point index if 'label_attr=None'
    :param plot_3d: Visualize plot in 3D using 'scatter3D' (default:'FALSE'). \
        If data is AnnData and 'coordinate_key=None', 'coordinate_key' defaults to 'ACTIONet3D'. \
        If data is matrix-like, it must have at least 3 columns.
    :param point_order: Numeric list=like object specifying order in which to plot individual points (default:None). \
        If None, points are plotted in random order.
    :param coordinate_key: If 'data' is AnnData, key of '.obsm' pertaining to plot coordinates.
    :param color_key:If data is AnnData, key of '.obsm' containing point-wise RGB color mappings (default:'denovo_color'). \
    Used only if no other color mapping parameters are given.
    ...

    :return plotly figure
    """

    if plot_3d:
        coor_dims = 3
        if isinstance(data, AnnData) and coordinate_key is None:
            coordinate_key = "ACTIONet3D"
    else:
        coor_dims = 2
        if isinstance(data, AnnData) and coordinate_key is None:
            coordinate_key = "ACTIONet2D"

    plot_coors = pu.get_plot_coors(
        data=data, coordinate_key=coordinate_key, scale_coors=True, coor_dims=coor_dims
    )
    plot_labels = pu.get_plot_labels(label_attr=label_attr, data=data)

    if plot_labels is None:
        plot_labels = pd.Series(
            "NA", index=range(plot_coors.shape[0]), name="labels", dtype=str
        )
    else:
        plot_labels = pd.Series(plot_labels, name="labels", dtype=str)

    plot_data = pd.concat([plot_coors, plot_labels], axis=1)
    plot_data["idx"] = range(plot_data.shape[0])

    if hover_text is not None:
        plot_data["text"] = pd.Series(hover_text, dtype=str)
    else:
        if label_attr is None:
            plot_data["text"] = plot_data["idx"]
        else:
            plot_data["text"] = plot_data["labels"]

    if point_order is None:
        plot_data["pidx"] = sample(range(plot_data.shape[0]), plot_data.shape[0])
    else:
        plot_data["pidx"] = point_order

    if label_attr is None or any(elem is not None for elem in [color_attr, trans_attr]):
        # if hover_text is None:
        #     plot_data["text"] = plot_data["idx"]
        # else:
        #     plot_data["text"] = pd.Series(hover_text, dtype=str)

        plot_data["fill"] = pu.get_plot_colors(
            color_attr=color_attr,
            plot_labels=plot_labels,
            data=data,
            color_key=color_key,
            palette=palette,
            return_dict=False,
        )
        plot_data["color"] = [lighten_color(c, stroke_size) for c in plot_data["fill"]]

        plot_data["trans"] = pu.get_plot_transparency(
            trans_attr=trans_attr,
            adata=data,
            trans_fac=trans_fac,
            trans_th=trans_th,
            scale=True,
        )

        plot_data["fill"] = append_alpha_to_rgb(
            plot_data["fill"], plot_data["trans"], unzip_colors=True
        )
        plot_data["color"] = append_alpha_to_rgb(
            plot_data["color"], plot_data["trans"], unzip_colors=True
        )

        # if point_order is None:
        #     plot_data = plot_data.sample(frac=1).reset_index(drop=True)
        # else:
        #     plot_data["pidx"] = point_order
        #     plot_data = plot_data.sort_values(by="pidx").reset_index(drop=True)

        plot_data = plot_data.sort_values(by="pidx").reset_index(drop=True)

        if show_legend is None:
            show_legend = False

        p = pu.make_plotly_scatter_single_trace(
            x=plot_data["x"],
            y=plot_data["y"],
            z=plot_data["z"],
            label_attr=plot_data["labels"],
            cols_point=plot_data["fill"],
            cols_stroke=plot_data["color"],
            point_size=point_size,
            stroke_size=stroke_size,
            show_legend=show_legend,
            hover_text=plot_data["text"],
            plot_3d=plot_3d,
        )

    else:
        # if hover_text is None:
        #     plot_data["text"] = plot_data["labels"]
        # else:
        #     plot_data["text"] = pd.Series(hover_text, dtype=str)

        fill_dict = pu.get_plot_colors(
            color_attr=color_attr,
            plot_labels=plot_labels,
            data=data,
            color_key=color_key,
            palette=palette,
            return_dict=True,
        )

        stroke_dict = {
            k: lighten_color(v, stroke_contrast_fac) for (k, v) in fill_dict.items()
        }

        # if point_order is None:
        #     plot_data = plot_data.sample(frac=1).reset_index(drop=True)
        # else:
        #     plot_data["pidx"] = point_order
        #     plot_data = plot_data.sort_values(by="pidx").reset_index(drop=True)

        plot_data = plot_data.sort_values(by="pidx").reset_index(drop=True)

        if show_legend is None:
            show_legend = True

        p = pu.make_plotly_scatter_split_trace(
            x=plot_data["x"],
            y=plot_data["y"],
            z=plot_data["z"],
            label_attr=plot_data["labels"],
            fill_dict=fill_dict,
            stroke_dict=stroke_dict,
            show_legend=show_legend,
            hover_text=plot_data["text"],
            plot_3d=plot_3d,
        )

    return p


def plot_ACTIONet_gradient(
    adata: AnnData,
    x: Union[list, pd.Series, np.ndarray],
    alpha_val: Optional[float] = 0,
    log_scale: Optional[bool] = False,
    use_rank: Optional[bool] = False,
    trans_attr: Union[str, list, pd.Series, np.ndarray, None] = None,
    trans_fac: Optional[float] = 1.5,
    trans_th: Optional[float] = -0.5,
    point_size: Optional[float] = 3,
    stroke_size: Optional[float] = 0.3,
    stroke_contrast_fac: Optional[float] = 1.2,
    grad_palette: Optional[str] = "magma",
    net_key: Optional[str] = "ACTIONet",
    coordinate_key: Optional[str] = "ACTIONet2D",
) -> go.Figure:
    """
    Projects a given continuous score on the ACTIONet plot
    Parameters
    ----------
    adata:
        ACTIONet output object
    x:
        score vector
    transparancey_key:
        additional continuous attribute to project onto the transparency of nodes
    transparency_z_threshold:
        controls the effect of transparency mapping
    transparancy_factor:
        controls the effect of transparancy mapping
    node_size:
        Size of nodes in the ACTIONet plot
    palette:
        Color palette (named vector or a name for a given known palette)
    coordinate_key:
       Entry in colMaps(ace) containing the plot coordinates (default:'ACTIONet2D')
    alpha_val:
        alpha_val Between [0, 1]. If it is greater than 0, smoothing of scores would be performed
    output_file:
        filename to save plot (optional)
    """

    G = G.astype(dtype=np.float64)

    np.amin(x)

    if log_scale:
        x = np.log1p(x)

    if alpha_val > 0:
        x = _an.compute_network_diffusion_fast(G=G, X0=sparse.csc_matrix(x))


# plot.ACTIONet.gradient <- function(ace,
#                                    x,
#                                    alpha_val = 0.85,
#                                    log_scale = FALSE,
#                                    nonparameteric = FALSE,
#                                    trans_attr = NULL,
#                                    trans_fac = 1.5,
#                                    trans_th = -0.5,
#                                    point_size = 1,
#                                    stroke_size = point_size * 0.1,
#                                    stroke_contrast_fac = 0.1,
#                                    grad_palette = "magma",
#                                    net_attr = "ACTIONet",
#                                    coordinate_key = "ACTIONet2D") {
#   NA_col <- "#eeeeee"
#
#   if (length(x) != ncol(ace)) {
#     warning("Length of input vector doesn't match the number of cells.")
#     return()
#   }
#   ## Create color gradient generator
#   if (grad_palette %in% c("greys", "inferno", "magma", "viridis", "BlGrRd", "RdYlBu", "Spectral")) {
#     grad_palette <- switch(grad_palette,
#       greys = grDevices::gray.colors(100),
#       inferno = viridis::inferno(500, alpha = 0.8),
#       magma = viridis::magma(500, alpha = 0.8),
#       viridis = viridis::viridis(500, alpha = 0.8),
#       BlGrRd = grDevices::colorRampPalette(c("blue", "grey", "red"))(500),
#       Spectral = (grDevices::colorRampPalette(rev(RColorBrewer::brewer.pal(n = 7, name = "Spectral"))))(100),
#       RdYlBu = (grDevices::colorRampPalette(rev(RColorBrewer::brewer.pal(n = 7, name = "RdYlBu"))))(100)
#     )
#   } else {
#     # grad_palette = grDevices::colorRampPalette(c(NA_col, grad_palette))(500)
#     grad_palette <- grDevices::colorRampPalette(grad_palette)(500)
#   }
#
#   if (log_scale == TRUE) {
#     x <- log1p(x)
#   }
#
#   if (alpha_val > 0) {
#     x <- as.numeric(propNetworkScores(
#       G = colNets(ace)[[net_attr]],
#       scores = as.matrix(x)
#     ))
#   }
#
#   col_func <- (scales::col_bin(
#     palette = grad_palette,
#     domain = NULL,
#     na.color = NA_col,
#     bins = 7
#   ))
#
#   if (nonparameteric == TRUE) {
#     plot_fill_col <- col_func(rank(x))
#   } else {
#     plot_fill_col <- col_func(x)
#   }
#
#   idx <- order(x, decreasing = FALSE)
#
#   p_out <- plot.ACTIONet(
#     ace = ace,
#     label_attr = NULL,
#     color_attr = plot_fill_col,
#     trans_attr = trans_attr,
#     trans_fac = trans_fac,
#     trans_th = trans_th,
#     point_size = point_size,
#     stroke_size = stroke_size,
#     stroke_contrast_fac = stroke_contrast_fac,
#     palette = NULL,
#     add_text_labels = FALSE,
#     point_order = idx,
#     coordinate_key = coordinate_key
#   )
#
#   return(p_out)
# }