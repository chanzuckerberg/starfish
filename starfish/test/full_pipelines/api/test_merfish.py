import numpy as np
import pandas as pd

from starfish import Experiment
from starfish.image._filter.gaussian_high_pass import GaussianHighPass
from starfish.image._filter.gaussian_low_pass import GaussianLowPass
from starfish.image._filter.richardson_lucy_deconvolution import DeconvolvePSF
from starfish.image._filter.scale_by_percentile import ScaleByPercentile
from starfish.spots._detector.pixel_spot_detector import PixelSpotDetector
from starfish.types import Features


def test_merfish_pipeline_cropped_data():

    # set random seed to errors provoked by optimization functions
    np.random.seed(777)

    # load the experiment
    experiment_json = (
        "https://dmf0bdeheu4zf.cloudfront.net/20180911/MERFISH-TEST/experiment.json"
    )
    experiment = Experiment.from_json(experiment_json)
    primary_image = experiment.fov().primary_image

    expected_primary_image = np.array(
        [[0.09593347, 0.09794766, 0.10089265, 0.10231174, 0.10133516,
          0.10002289, 0.1035172, 0.10647745, 0.10809491, 0.10769818],
         [0.09840543, 0.09710842, 0.09787137, 0.10025177, 0.10017548,
          0.10102998, 0.10756085, 0.10952926, 0.10888838, 0.10472267],
         [0.09965667, 0.09999237, 0.10307469, 0.10264744, 0.10170138,
          0.10417334, 0.10580606, 0.10658427, 0.10473793, 0.10211337],
         [0.10383764, 0.10521096, 0.10623331, 0.10525673, 0.10400549,
          0.10115206, 0.10203708, 0.10415808, 0.10347143, 0.10434119],
         [0.10539406, 0.10548562, 0.10464637, 0.10547036, 0.10615702,
          0.10554665, 0.10327306, 0.09990082, 0.09980926, 0.10301366],
         [0.1085069, 0.10649271, 0.10342565, 0.10406653, 0.10771344,
          0.10740826, 0.10659953, 0.10327306, 0.10269322, 0.10246433],
         [0.11427481, 0.11221485, 0.10957504, 0.10734722, 0.10701152,
          0.10782025, 0.10749981, 0.10347143, 0.10150301, 0.10322728],
         [0.11642634, 0.11441215, 0.11172656, 0.1098497, 0.11038376,
          0.1097734, 0.1085832, 0.10276951, 0.10251011, 0.1017319],
         [0.11627375, 0.11638056, 0.11581598, 0.11468681, 0.11187915,
          0.11042954, 0.10994125, 0.10493629, 0.10205234, 0.10099947],
         [0.11708248, 0.11792172, 0.1163653, 0.11743343, 0.11384756,
          0.11157397, 0.10919356, 0.10666056, 0.10330358, 0.1016556]],
        dtype=np.float32
    )
    assert np.allclose(
        expected_primary_image,
        primary_image.numpy_array[5, 0, 0, 40:50, 45:55]
    )

    # high pass filter
    ghp = GaussianHighPass(sigma=3)
    high_passed = ghp.run(primary_image, in_place=False)

    expected_high_passed = np.array(
        [[0.00000000e+00, 0.00000000e+00, 1.09633317e-03, 1.99840278e-03,
          5.83776810e-04, 0.00000000e+00, 2.04111132e-03, 4.65832430e-03,
          5.91536953e-03, 5.13293567e-03],
         [0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00,
          0.00000000e+00, 0.00000000e+00, 5.06116677e-03, 6.75149438e-03,
          5.81014126e-03, 1.30867042e-03],
         [0.00000000e+00, 0.00000000e+00, 4.04353003e-04, 0.00000000e+00,
          0.00000000e+00, 9.50735832e-04, 2.44306756e-03, 3.06733356e-03,
          1.02676533e-03, 0.00000000e+00],
         [0.00000000e+00, 9.25681404e-04, 1.93746323e-03, 9.78471914e-04,
          0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 6.93379398e-05,
          0.00000000e+00, 6.96662127e-05],
         [0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00,
          7.19601658e-04, 4.23542969e-04, 0.00000000e+00, 0.00000000e+00,
          0.00000000e+00, 0.00000000e+00],
         [0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00,
          1.03922332e-03, 1.31504616e-03, 1.06819853e-03, 0.00000000e+00,
          0.00000000e+00, 0.00000000e+00],
         [3.29251956e-03, 1.94998653e-03, 6.55281453e-05, 0.00000000e+00,
          0.00000000e+00, 7.41835209e-04, 1.23043721e-03, 0.00000000e+00,
          0.00000000e+00, 0.00000000e+00],
         [3.54986487e-03, 2.41864172e-03, 6.62828987e-04, 0.00000000e+00,
          1.30568280e-03, 1.73368034e-03, 1.55901266e-03, 0.00000000e+00,
          0.00000000e+00, 0.00000000e+00],
         [1.86399753e-03, 2.96097458e-03, 3.44559705e-03, 3.42158093e-03,
          1.77239523e-03, 1.51152371e-03, 2.18335022e-03, 0.00000000e+00,
          0.00000000e+00, 0.00000000e+00],
         [1.52147513e-03, 3.41107862e-03, 2.98134040e-03, 5.24483122e-03,
          2.91270155e-03, 1.91782816e-03, 7.70164461e-04, 0.00000000e+00,
          0.00000000e+00, 0.00000000e+00]],
        dtype=np.float32
    )

    assert np.allclose(
        expected_high_passed,
        high_passed.numpy_array[5, 0, 0, 40:50, 45:55]
    )

    # deconvolve the point spread function
    num_iter = 9  # largest number that does not clobber whole tiles
    dpsf = DeconvolvePSF(num_iter=num_iter, sigma=2)
    deconvolved = dpsf.run(high_passed, in_place=False)

    # assert that the deconvolved data is correct
    expected_deconvolved_values = np.array(
        [[2.25230572e-06, 2.96607498e-05, 1.53939817e-04, 3.77729459e-04,
          6.43046257e-04, 1.14180995e-03, 2.44962152e-03, 4.31401404e-03,
          5.38020977e-03, 5.06525156e-03],
         [3.25562511e-07, 5.86793669e-06, 4.27855826e-05, 1.52829611e-04,
          4.11558028e-04, 1.12412805e-03, 3.08942581e-03, 5.47848803e-03,
          5.89954105e-03, 4.35198979e-03],
         [5.51991907e-07, 5.40061300e-06, 3.02247603e-05, 9.93946013e-05,
          2.62755334e-04, 6.61335326e-04, 1.47410476e-03, 1.93622068e-03,
          1.55223356e-03, 8.69370830e-04],
         [3.05144601e-06, 1.07733526e-05, 3.26414895e-05, 7.54637731e-05,
          1.51409581e-04, 2.59930319e-04, 3.42956704e-04, 2.50781105e-04,
          1.21473737e-04, 4.63213087e-05],
         [2.42861986e-05, 3.25026739e-05, 5.10666404e-05, 7.76175794e-05,
          1.12473280e-04, 1.22562872e-04, 8.44116871e-05, 2.82440730e-05,
          6.44358358e-06, 1.34921938e-06],
         [2.05825103e-04, 1.30751854e-04, 1.14205628e-04, 1.17051075e-04,
          1.27967461e-04, 9.45178093e-05, 3.57154712e-05, 5.27942713e-06,
          4.54088650e-07, 3.85001238e-08],
         [1.03961789e-03, 4.98777133e-04, 3.39467046e-04, 2.85098541e-04,
          2.64193867e-04, 1.53627556e-04, 3.97770187e-05, 3.40617552e-06,
          1.31290507e-07, 4.20585900e-09],
         [2.61053780e-03, 1.49914144e-03, 1.21700650e-03, 1.10990299e-03,
          9.95470329e-04, 5.06902855e-04, 1.03297733e-04, 6.40046383e-06,
          1.44418613e-07, 2.26699680e-09],
         [2.37529546e-03, 2.09275130e-03, 2.69876568e-03, 3.43918296e-03,
          3.57924280e-03, 1.82036331e-03, 3.21651003e-04, 1.60297930e-05,
          2.65115088e-07, 3.88158929e-09],
         [9.99903305e-04, 1.61879312e-03, 3.86601263e-03, 7.53386941e-03,
          9.54075614e-03, 5.00072604e-03, 7.98692089e-04, 3.43009332e-05,
          5.45006845e-07, 1.50291884e-08]],
        dtype=np.float32
    )

    assert np.allclose(
        expected_deconvolved_values,
        deconvolved.numpy_array[5, 0, 0, 40:50, 45:55]
    )

    # low pass filter
    glp = GaussianLowPass(sigma=1)
    low_passed = glp.run(deconvolved, in_place=False)

    expected_low_passed = np.array(
        [[8.71804086e-05, 2.32075104e-04, 4.38601618e-04, 6.30121651e-04,
          8.40211391e-04, 1.29578831e-03, 2.13624425e-03, 3.06111369e-03,
          3.55098017e-03, 3.52711615e-03],
         [1.72758549e-05, 5.91057528e-05, 1.48400447e-04, 3.07144277e-04,
          6.19356195e-04, 1.26784887e-03, 2.29825192e-03, 3.28041418e-03,
          3.62323870e-03, 3.33753583e-03],
         [8.45484857e-06, 2.49027211e-05, 7.04137878e-05, 1.74936928e-04,
          4.05155025e-04, 8.61777853e-04, 1.51646176e-03, 2.04277623e-03,
          2.10067384e-03, 1.78643932e-03],
         [3.05343973e-05, 3.35903504e-05, 5.81408794e-05, 1.15715747e-04,
          2.27931042e-04, 4.14869116e-04, 6.34726771e-04, 7.57573398e-04,
          6.99905305e-04, 5.40509494e-04],
         [1.62070579e-04, 1.04881526e-04, 9.45028285e-05, 1.13263192e-04,
          1.46951118e-04, 1.81279888e-04, 1.99059998e-04, 1.84298556e-04,
          1.41107586e-04, 9.48772271e-05],
         [6.21816390e-04, 3.54575697e-04, 2.49490378e-04, 2.18788072e-04,
          1.96448905e-04, 1.49855028e-04, 9.07269150e-05, 4.56028471e-05,
          2.13102024e-05, 1.04826123e-05],
         [1.52749998e-03, 9.18222219e-04, 6.88085287e-04, 6.17466904e-04,
          5.23993032e-04, 3.40554980e-04, 1.50441467e-04, 4.31491425e-05,
          8.31826219e-06, 1.39600253e-06],
         [2.34337442e-03, 1.65975535e-03, 1.55700289e-03, 1.65839094e-03,
          1.52463762e-03, 1.00136413e-03, 4.23720954e-04, 1.09360979e-04,
          1.67927553e-05, 1.53663716e-06],
         [2.28150292e-03, 2.11539234e-03, 2.69104730e-03, 3.49484459e-03,
          3.55044879e-03, 2.43071385e-03, 1.03576482e-03, 2.62576091e-04,
          3.88100231e-05, 3.41624714e-06],
         [1.48679575e-03, 1.96269962e-03, 3.37493576e-03, 5.19915860e-03,
          5.78267517e-03, 4.15057690e-03, 1.80804349e-03, 4.60562185e-04,
          6.77878588e-05, 7.27396431e-06]],
        dtype=np.float32
    )
    assert np.allclose(
        expected_low_passed,
        low_passed.numpy_array[5, 0, 0, 40:50, 45:55]
    )

    sc_filt = ScaleByPercentile(p=90)
    scaled_image = sc_filt.run(low_passed, in_place=False)

    # assert that the scaled data is correct
    expected_scaled_low_passed = np.array(
        [[2.36151423e-02, 6.28637671e-02, 1.18807055e-01, 1.70685455e-01,
            2.27593824e-01, 3.50998789e-01, 5.78658342e-01, 8.29183519e-01,
            9.61876750e-01, 9.55412626e-01],
         [4.67962492e-03, 1.60103776e-02, 4.01982553e-02, 8.31982940e-02,
            1.67769194e-01, 3.43430549e-01, 6.22542262e-01, 8.88586640e-01,
            9.81449664e-01, 9.04059589e-01],
         [2.29021232e-03, 6.74555730e-03, 1.90734547e-02, 4.73863631e-02,
            1.09747060e-01, 2.33435377e-01, 4.10773665e-01, 5.53339660e-01,
            5.69022715e-01, 4.83904064e-01],
         [8.27101339e-03, 9.09881108e-03, 1.57489982e-02, 3.13447155e-02,
            6.17412329e-02, 1.12378329e-01, 1.71932489e-01, 2.05208659e-01,
            1.89587697e-01, 1.46411166e-01],
         [4.39009629e-02, 2.84098629e-02, 2.55985856e-02, 3.06803901e-02,
            3.98056917e-02, 4.91045304e-02, 5.39206900e-02, 4.99221161e-02,
            3.82226892e-02, 2.56999806e-02],
         [1.68435052e-01, 9.60460454e-02, 6.75810724e-02, 5.92646487e-02,
            5.32135367e-02, 4.05923128e-02, 2.45758332e-02, 1.23527460e-02,
            5.77242952e-03, 2.83948984e-03],
         [4.13763195e-01, 2.48724550e-01, 1.86386168e-01, 1.67257488e-01,
            1.41937658e-01, 9.22485143e-02, 4.07511257e-02, 1.16881039e-02,
            2.25322321e-03, 3.78144148e-04],
         [6.34764552e-01, 4.49588507e-01, 4.21755642e-01, 4.49219465e-01,
            4.12988871e-01, 2.71246254e-01, 1.14776127e-01, 2.96233352e-02,
            4.54876432e-03, 4.16238996e-04],
         [6.18005455e-01, 5.73010147e-01, 7.28941679e-01, 9.46671605e-01,
            9.61733460e-01, 6.58423424e-01, 2.80564368e-01, 7.11256936e-02,
            1.05127227e-02, 9.25380969e-04],
         [4.02738214e-01, 5.31649411e-01, 9.14191008e-01, 1.40832996e+00,
            1.56639075e+00, 1.12429368e+00, 4.89756435e-01, 1.24755450e-01,
            1.83621347e-02, 1.97034585e-03]],
        dtype=np.float32
    )

    assert np.allclose(
        expected_scaled_low_passed,
        scaled_image.numpy_array[5, 0, 0, 40:50, 45:55]
    )

    # detect and decode spots
    psd = PixelSpotDetector(
        codebook=experiment.codebook,
        metric='euclidean',
        distance_threshold=0.5176,
        magnitude_threshold=5e-5,
        min_area=2,
        max_area=np.inf,
        norm_order=2,
        crop_size=(0, 40, 40)
    )
    spot_intensities, prop_results = psd.run(scaled_image)

    # verify that the number of spots are correct
    spots_passing_filters = spot_intensities[Features.PASSES_THRESHOLDS].sum()
    assert spots_passing_filters == 1493

    # compare to paper results
    bench = pd.read_csv('https://dmf0bdeheu4zf.cloudfront.net/MERFISH/benchmark_results.csv',
                        dtype={'barcode': object})
    benchmark_counts = bench.groupby('gene')['gene'].count()

    spot_intensities_passing_filters = spot_intensities.where(
        spot_intensities[Features.PASSES_THRESHOLDS], drop=True
    )
    genes, counts = np.unique(spot_intensities_passing_filters[Features.TARGET], return_counts=True)
    result_counts = pd.Series(counts, index=genes).sort_values(ascending=False)[:5]

    # assert that number of high-expression detected genes are correct
    expected_counts = pd.Series(
        [120, 90, 56, 49, 37],
        index=('nan', 'MALAT1', 'SRRM2', 'FASN', 'IGF2R')
    )
    assert np.array_equal(
        expected_counts.values,
        result_counts.values
    )
    assert np.array_equal(
        expected_counts.index,
        result_counts.index
    )

    tmp = pd.concat([result_counts, benchmark_counts], join='inner', axis=1).values

    corrcoef = np.corrcoef(tmp[:, 1], tmp[:, 0])[0, 1]

    assert np.round(corrcoef, 4) == 0.894
