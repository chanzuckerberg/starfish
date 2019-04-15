"""

BaristaSeq
==========

BaristaSeq is an assay that sequences padlock-probe initiated rolling circle
amplified spots using a one-hot codebook. The publication for this assay can be
found `here <baristaseq>`_

This example processes a single field of view extracted from a tissue slide that
measures gene expression in mouse primary visual cortex, created as part of the
SpaceTx project.

.. _baristaseq: https://www.ncbi.nlm.nih.gov/pubmed/29190363
"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import starfish
import starfish.data
from starfish.types import Axes, Clip
from starfish.util.plot import (
    imshow_plane, intensity_histogram, overlay_spot_calls
)

###############################################################################
# Load Data
# ---------
# Import starfish and extract a single field of view. The data from one field
# of view correspond to 476 images from 7 imaging rounds `(r)`, 4 channels,
# `(c)`, and 17 z-planes `(z)`. Each image is `1193 x 913` (y, x).

experiment_json = (
    "https://d2nhj9g34unfro.cloudfront.net/browse/formatted/20190319/baristaseq"
    "/experiment.json"
)
exp = starfish.Experiment.from_json(experiment_json)

nissl = exp['fov_000'].get_image('dots')
img = exp['fov_000'].get_image('primary')

###############################################################################
# starfish data are 5-dimensional, but to demonstrate what they look like in a
# non-interactive fashion, it's best to visualize the data in 2-d. There are
# better ways to look at these data using the :py:func:`starfish.display`
# method, which allows the user to page through each axis of the tensor
#
# for this vignette, we'll pick one plane and track it through the processing
# steps

# # Uncomment this block to use starfish.display
# %gui qt5
# starfish.display(img)
# starfish.display(nissl)

plane_selector = {Axes.CH: 0, Axes.ROUND: 0, Axes.ZPLANE: 8}

f, (ax1, ax2) = plt.subplots(ncols=2)
imshow_plane(img, sel=plane_selector, ax=ax1, title="primary image")
imshow_plane(nissl, sel=plane_selector, ax=ax2, title="nissl image")

###############################################################################
# Visualize codebook
# ------------------
# The BaristaSeq codebook maps pixel intensities across the rounds and channels
# to corresponding barcodes and genes that each pixel codes for. For this
# example dataset, the codebook specifies 79 possible gene targets.

###############################################################################
# Register the data
# -----------------
# The first step in BaristaSeq is to do some rough registration. For this data,
# the rough registration has been done for us by the authors, so it is omitted
# from this example.

###############################################################################
# Project into 2D
# ---------------
# BaristaSeq is typically processed in 2d. Starfish exposes
# :py:meth:`ImageStack.max_proj` to enable a user to max-project any axes. Here
# Z is max projected for both the nissl images and the primary images.

z_projected_image = img.max_proj(Axes.ZPLANE)
z_projected_nissl = nissl.max_proj(Axes.ZPLANE)

# show the projected data
f, (ax1, ax2) = plt.subplots(ncols=2)
imshow_plane(img, sel=plane_selector, ax=ax1, title="primary image")
imshow_plane(nissl, sel=plane_selector, ax=ax2, title="nissl image")

###############################################################################
# Correct Channel Misalignment
# ----------------------------
# There is a slight miss-alignment of the C channel in the microscope used to
# acquire the data. This has been corrected for this data, but here is how it
# could be transformed using python code for future datasets.

# from skimage.feature import register_translation
# from skimage.transform import warp
# from skimage.transform import SimilarityTransform
# from functools import partial

# # Define the translation
# transform = SimilarityTransform(translation=(1.9, -0.4))

# # C is channel 0
# channels = (0,)

# # The channel should be transformed in all rounds
# rounds = np.arange(img.num_rounds)

# # apply the transformation in place
# slice_indices = product(channels, rounds)
# for ch, round_, in slice_indices:
#     selector = {Axes.ROUND: round_, Axes.CH: ch, Axes.ZPLANE: 0}
#     tile = z_projected_image.get_slice(selector)[0]
#     transformed = warp(tile, transform)
#     z_projected_image.set_slice(
#         selector=selector,
#         data=transformed.astype(np.float32),
#     )

###############################################################################
# Remove Registration Artefacts
# -----------------------------
# There are some minor registration errors along the pixels for which y < 100
# and x < 50. Those pixels are dropped from this analysis

registration_corrected: starfish.ImageStack = z_projected_image.sel(
    {Axes.Y: (100, -1), Axes.X: (50, -1)}
)

###############################################################################
# Correct for bleed-through from Illumina SBS reagents
# ----------------------------------------------------
# The following matrix contains bleed correction factors for Illumina
# sequencing-by-synthesis reagents. Starfish provides a LinearUnmixing method
# that will unmix the fluorescence intensities. This matrix is read as a
# *correction* factor for each channel, where each column defines an implied
# mixing of the channels.
#
# For example, this should be read as implying that channel zero is mixed with
# 35% of the intensity of channel 1, which should be substracted. Similarly,
# channel 1 is mixed with 5% of channel 0 and 2% of channel 2.

data = np.array(
    [[1.   , -0.05,  0.  ,  0.  ],
     [-0.35,  1.  ,  0.  ,  0.  ],
     [0.   , -0.02,  1.  , -0.84],
     [0.   ,  0.  , -0.05,  1.  ]]
)
rows = pd.Index(np.arange(4), name='bleed_from')
cols = pd.Index(np.arange(4), name='bleed_to')
unmixing_coeff = pd.DataFrame(data, rows, cols)

lum = starfish.image.Filter.LinearUnmixing(
    unmixing_coeff, clip_method=Clip.CLIP
)
bleed_corrected = lum.run(registration_corrected, in_place=False)

###############################################################################
# the matrix shows that (zero-based!) channel 2 bleeds particularly heavily into
# channel 3. To demonstrate the effect of unmixing, we'll plot channels 2 and 3
# of round 0 before and after unmixing.
#
# Channel 2 should look relative unchanged, as it only receives a bleed through
# of 5% of channel 3. However, Channel 3 should look dramatically sparser after
# spots from Channel 2 have been subtracted

ch2_r0 = {Axes.CH: 2, Axes.ROUND: 0, Axes.X: (500, 700), Axes.Y: (500, 700)}
ch3_r0 = {Axes.CH: 3, Axes.ROUND: 0, Axes.X: (500, 700), Axes.Y: (500, 700)}
f, ((ax1, ax2), (ax3, ax4)) = plt.subplots(nrows=2, ncols=2)
imshow_plane(
    registration_corrected,
    sel=ch2_r0, ax=ax1, title="Channel 2\nBefore Unmixing"
)
imshow_plane(
    registration_corrected,
    sel=ch3_r0, ax=ax2, title="Channel 3\nBefore Unmixing"
)
imshow_plane(
    bleed_corrected,
    sel=ch2_r0, ax=ax3, title="Channel 2\nAfter Unmixing"
)
imshow_plane(
    bleed_corrected,
    sel=ch3_r0, ax=ax4, title="Channel 3\nAfter Unmixing"
)
f.tight_layout()

###############################################################################
# Remove image background
# -----------------------
# To remove image background, BaristaSeq uses a White Tophat filter, which
# measures the background with a rolling disk morphological element and
# subtracts it from the image.

from skimage.morphology import opening, dilation, disk
from functools import partial

# calculate the background
opening = partial(opening, selem=disk(5))

background = bleed_corrected.apply(
    opening,
    group_by={Axes.ROUND, Axes.CH, Axes.ZPLANE}, verbose=False, in_place=False
)

wth = starfish.image.Filter.WhiteTophat(masking_radius=5)
background_corrected = wth.run(bleed_corrected, in_place=False)

f, (ax1, ax2, ax3) = plt.subplots(ncols=3)
selector = {Axes.CH: 0, Axes.ROUND: 0, Axes.X: (500, 700), Axes.Y: (500, 700)}
imshow_plane(bleed_corrected, sel=selector, ax=ax1, title="template\nimage")
imshow_plane(background, sel=selector, ax=ax2, title="background")
imshow_plane(
    background_corrected, sel=selector, ax=ax3, title="background\ncorrected"
)
f.tight_layout()

###############################################################################
# Scale images to equalize spot intensities across channels
# ---------------------------------------------------------
# The number of peaks are not uniform across rounds and channels,
# which prevents histogram matching across channels. Instead, a percentile value
# is identified and set as the maximum across channels, and the dynamic range is
# extended to equalize the channel intensities. We first demonatrate what
# scaling by the max value does.
sbp = starfish.image.Filter.ScaleByPercentile(p=100)
scaled = sbp.run(background_corrected, n_processes=1, in_place=False)


###############################################################################
# The easiest way to visualize this is to calculate the intensity histograms
# before and after this scaling and plot their log-transformed values. This
# should see that the histograms are better aligned in terms of intensities.
# It gets most of what we want, but the histograms are still slightly shifted;
# a result of high-value outliers.


def plot_scaling_result(
    template: starfish.ImageStack, scaled: starfish.ImageStack
):
    f, (before, after) = plt.subplots(ncols=4, nrows=2)
    for channel, ax in enumerate(before):
        title = f'Before scaling\nChannel {channel}'
        intensity_histogram(
            template, sel={Axes.CH: channel, Axes.ROUND: 0}, ax=ax, title=title,
            log=True, bins=50,
        )
        ax.set_xlim(0, 0.007)
    for channel, ax in enumerate(after):
        title = f'After scaling\nChannel {channel}'
        intensity_histogram(
            scaled, sel={Axes.CH: channel, Axes.ROUND: 0}, ax=ax, title=title,
            log=True, bins=50,
        )
    f.tight_layout()
    return f

f = plot_scaling_result(background_corrected, scaled)

###############################################################################
# We repeat this scaling by the 99.8th percentile value, which does a better job
# of equalizing the intensity distributions.
#
# It should also be visible that exactly 0.1% of values take on the max value
# of 1. This is a result of setting any value above the 99.9th percentile to 1,
# and is a trade-off made to eliminate large-value outliers.

sbp = starfish.image.Filter.ScaleByPercentile(p=99.9)
scaled = sbp.run(background_corrected, in_place=False)

f = plot_scaling_result(background_corrected, scaled)

###############################################################################
# We use a pixel spot decoder to identify the gene target for each spot.
psd = starfish.spots.PixelSpotDecoder.PixelSpotDecoder(
    codebook=exp.codebook, metric='euclidean', distance_threshold=0.5,
    magnitude_threshold=0.1, min_area=7, max_area=50
)
pixel_decoded, ccdr = psd.run(scaled)

###############################################################################
# plot a mask that shows where pixels have decoded to genes. Note the lack of
# spots in the top left. this matches an illumination gradient which might be
# fixable with calibration. Perhaps the results could be improved if the
# illumination were flattened.
f, ax = plt.subplots()
# ax.imshow(np.squeeze(ccdr.label_image > 0), cmap=plt.cm.gray)
ax.imshow(np.squeeze(ccdr.decoded_image), cmap=plt.cm.nipy_spectral)
ax.set_title("Pixel Decoding Results")


###############################################################################
# Get the total counts for each gene from each spot detector.
# Do the below values make sense for this tissue and this probeset?

pixel_decoded_gene_counts = pd.Series(
    *np.unique(pixel_decoded['target'], return_counts=True)[::-1]
)

print(pixel_decoded_gene_counts.sort_values().drop("nan"))
