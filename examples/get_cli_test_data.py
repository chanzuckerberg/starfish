import argparse
import json
import os

import requests

from starfish import Experiment
from starfish.util.argparse import FsExistsType


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("experiment_url")
    parser.add_argument("output_dir", type=FsExistsType())
    args = parser.parse_args()

    # save image stacks locally
    exp = Experiment.from_json(args.experiment_url + 'experiment.json')

    for fov in exp.fovs():
        fov_dir = args.output_dir + "/" + fov.name + "/"
        os.mkdir(fov_dir)
        fov.primary_image.write(fov_dir + 'hybridization.json')
        for image_type in fov.auxiliary_image_types:
            fov[image_type].write(fov_dir + (image_type + '.json'))

    # get codebook from url and save locally to tmp dir
    codebook = requests.get(args.experiment_url + 'codebook.json')
    data = codebook.json()
    with open(args.output_dir + '/codebook.json', 'w') as f:
        json.dump(data, f)

    # TODO save exp.json
