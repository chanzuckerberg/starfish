import os
import sys

import numpy as np
import pandas as pd

from starfish import IntensityTable
from starfish.types import Features
from starfish.test.full_pipelines.cli._base_cli_test import CLITest


class TestAllenData(CLITest):
    __test__ = True

    SUBDIRS = (
        "registered",
        "filtered",
        "results"
    )

    STAGES = (
        [
            sys.executable,
            "examples/get_cli_test_data.py",
            "https://dmf0bdeheu4zf.cloudfront.net/20180828/allen_smFISH-TEST/allen_smFISH_test_data.zip",
            lambda tempdir, *args, **kwargs: os.path.join(tempdir, "registered")
        ],
        [
            "starfish", "filter",
            "--input", lambda tempdir, *args, **kwargs: os.path.join(
            tempdir, "registered/fov_001", "hybridization.json"),
            "--output", lambda tempdir, *args, **kwargs: os.path.join(
            tempdir, "filtered", "hybridization.json"),
            "Clip",
            "--p-min", "10",
            "--p-max", "100"
        ],
        [
            "starfish", "filter",
            "--input", lambda tempdir, *args, **kwargs: os.path.join(
            tempdir, "filtered", "hybridization.json"),
            "--output", lambda tempdir, *args, **kwargs: os.path.join(
            tempdir, "filtered", "filtered.json"),
            "Bandpass",
            "--lshort", ".5",
            "--llong", "7",
            "--truncate", "4"
        ],
        [
            "starfish", "filter",
            "--input", lambda tempdir, *args, **kwargs: os.path.join(
            tempdir, "filtered", "filtered.json"),
            "--output", lambda tempdir, *args, **kwargs: os.path.join(
            tempdir, "filtered", "filtered1.json"),
            "Clip",
            "--p-min", "10",
            "--p-max", "100"
        ],
        [
            "starfish", "filter",
            "--input", lambda tempdir, *args, **kwargs: os.path.join(
            tempdir, "filtered", "filtered1.json"),
            "--output", lambda tempdir, *args, **kwargs: os.path.join(
            tempdir, "filtered", "filtered2.json"),
            "GaussianLowPass",
            "--sigma", "1"
        ],
        [
            "starfish", "detect_spots",
            "--input", lambda tempdir, *args, **kwargs: os.path.join(
            tempdir, "filtered", "filtered1.json"),
            "--output", lambda tempdir, *args, **kwargs: os.path.join(tempdir, "results"),
            "LocalMaxPeakFinder",
            "--spot-diameter", "3",
            "--min-mass", "300",
            "--max-size", "3",
            "--separation", "5",
            # "--noise-size", ".65",
            "--percentile", "10",
            "--is-volume"
        ],

    )

    def verify_results(self, intensities):
        #TODO
        pass




