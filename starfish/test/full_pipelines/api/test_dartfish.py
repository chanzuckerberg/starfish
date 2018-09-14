import numpy as np
import pandas as pd

from starfish import IntensityTable

from starfish.types import Features
import sys
import os
os.environ["USE_TEST_DATA"] = "1"
sys.path.append('../../../../notebooks/py/')
dartfish = __import__('DARTFISH_Pipeline_-_Human_Occipital_Cortex_-_1_FOV')


def test_dartfish_pipeline_cropped_data():

    # set random seed to errors provoked by optimization functions
    np.random.seed(777)

    primary_image = dartfish.stack

    expected_primary_image = np.array(
        [[1.52590219e-05, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00,
          0.00000000e+00, 0.00000000e+00, 4.57770657e-05, 0.00000000e+00,
          0.00000000e+00, 3.05180438e-05],
         [0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00,
          1.52590219e-05, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00,
          0.00000000e+00, 0.00000000e+00],
         [0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00,
          1.52590219e-05, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00,
          3.05180438e-05, 0.00000000e+00],
         [0.00000000e+00, 0.00000000e+00, 1.52590219e-05, 0.00000000e+00,
          0.00000000e+00, 1.52590219e-05, 0.00000000e+00, 1.52590219e-05,
          0.00000000e+00, 0.00000000e+00],
         [0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00,
          0.00000000e+00, 0.00000000e+00, 3.05180438e-05, 0.00000000e+00,
          1.52590219e-05, 0.00000000e+00],
         [0.00000000e+00, 0.00000000e+00, 1.52590219e-05, 0.00000000e+00,
          3.05180438e-05, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00,
          0.00000000e+00, 1.52590219e-05],
         [0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00,
          0.00000000e+00, 1.52590219e-05, 0.00000000e+00, 0.00000000e+00,
          0.00000000e+00, 0.00000000e+00],
         [0.00000000e+00, 1.52590219e-05, 0.00000000e+00, 0.00000000e+00,
          1.52590219e-05, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00,
          0.00000000e+00, 0.00000000e+00],
         [1.52590219e-05, 1.52590219e-05, 0.00000000e+00, 0.00000000e+00,
          0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00,
          0.00000000e+00, 0.00000000e+00],
         [0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00,
          0.00000000e+00, 1.52590219e-05, 1.52590219e-05, 0.00000000e+00,
          0.00000000e+00, 0.00000000e+00]],
        dtype=np.float32
    )

    assert np.allclose(
        primary_image.numpy_array[0, 0, 0, 50:60, 60:70],
        expected_primary_image
    )

    normalized_image = dartfish.norm_stack

    expected_normalized_image = np.array(
        [[0.01960784, 0., 0., 0., 0.,
          0., 0.05882353, 0., 0., 0.03921569],
         [0., 0., 0., 0., 0.01960784,
          0., 0., 0., 0., 0.],
         [0., 0., 0., 0., 0.01960784,
          0., 0., 0., 0.03921569, 0.],
         [0., 0., 0.01960784, 0., 0.,
          0.01960784, 0., 0.01960784, 0., 0.],
         [0., 0., 0., 0., 0.,
          0., 0.03921569, 0., 0.01960784, 0.],
         [0., 0., 0.01960784, 0., 0.03921569,
          0., 0., 0., 0., 0.01960784],
         [0., 0., 0., 0., 0.,
          0.01960784, 0., 0., 0., 0.],
         [0., 0.01960784, 0., 0., 0.01960784,
          0., 0., 0., 0., 0.],
         [0.01960784, 0.01960784, 0., 0., 0.,
          0., 0., 0., 0., 0.],
         [0., 0., 0., 0., 0.,
          0.01960784, 0.01960784, 0., 0., 0.]],
        dtype=np.float32,
    )

    assert np.allclose(
        normalized_image.numpy_array[0, 0, 0, 50:60, 60:70],
        expected_normalized_image
    )

    zero_norm_stack = dartfish.zero_norm_stack

    expected_zero_normalized_image = np.array(
        [[0.01960784, 0., 0., 0., 0.,
          0., 0.05882353, 0., 0., 0.03921569],
         [0., 0., 0., 0., 0.01960784,
          0., 0., 0., 0., 0.],
         [0., 0., 0., 0., 0.01960784,
          0., 0., 0., 0., 0.],
         [0., 0., 0.01960784, 0., 0.,
          0., 0., 0.01960784, 0., 0.],
         [0., 0., 0., 0., 0.,
          0., 0.03921569, 0., 0.01960784, 0.],
         [0., 0., 0.01960784, 0., 0.,
          0., 0., 0., 0., 0.01960784],
         [0., 0., 0., 0., 0.,
          0.01960784, 0., 0., 0., 0.],
         [0., 0.01960784, 0., 0., 0.,
          0., 0., 0., 0., 0.],
         [0.01960784, 0., 0., 0., 0.,
          0., 0., 0., 0., 0.],
         [0., 0., 0., 0., 0.,
          0., 0.01960784, 0., 0., 0.]],
        dtype=np.float32
    )

    assert np.allclose(
        expected_zero_normalized_image,
        zero_norm_stack.numpy_array[0, 0, 0, 50:60, 60:70]
    )


    spot_intensities, results = dartfish.spot_intensities, dartfish.results
    spots_df = IntensityTable(
        spot_intensities.where(spot_intensities[Features.PASSES_THRESHOLDS], drop=True)
    ).to_features_dataframe()
    spots_df['area'] = np.pi * spots_df['radius'] ** 2

    # verify number of spots detected
    spots_passing_filters = spot_intensities[Features.PASSES_THRESHOLDS].sum()
    assert spots_passing_filters == 53

    # compare to benchmark data -- note that this particular part of the dataset appears completely
    # uncorrelated
    cnts_benchmark = pd.read_csv(
        'https://dmf0bdeheu4zf.cloudfront.net/20180905/DARTFISH/fov_001/counts.csv')

    min_dist = 0.6
    cnts_starfish = spots_df[spots_df.distance <= min_dist].groupby('target').count()['area']
    cnts_starfish = cnts_starfish.reset_index(level=0)
    cnts_starfish.rename(columns={'target': 'gene', 'area': 'cnt_starfish'}, inplace=True)

    # get top 5 genes and verify they are correct
    high_expression_genes = cnts_starfish.sort_values('cnt_starfish', ascending=False).head(5)

    assert np.array_equal(
        high_expression_genes['cnt_starfish'].values,
        [7, 3, 2, 2, 2]
    )
    assert np.array_equal(
        high_expression_genes['gene'].values,
        ['MBP', 'MOBP', 'ADCY8', 'TRIM66', 'SYT6']
    )

    # verify correlation is accurate for this subset of the image
    benchmark_comparison = pd.merge(cnts_benchmark, cnts_starfish, on='gene', how='left')
    benchmark_comparison.head(20)

    x = benchmark_comparison.dropna().cnt.values
    y = benchmark_comparison.dropna().cnt_starfish.values
    corrcoef = np.corrcoef(x, y)
    corrcoef = corrcoef[0, 1]

    assert np.round(corrcoef, 5) == 0.04422
