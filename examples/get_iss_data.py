from __future__ import division

import io
import json
import zipfile

import click
import requests
from skimage.io import imread, imsave


def download(input_dir, url):
    print("Downloading data ...")
    r = requests.get(url)
    z = zipfile.ZipFile(io.BytesIO(r.content))
    z.extractall(input_dir)


def load_tiff_stack(path):
    stack = imread(path)
    return stack


def load_hyb_chan(input_dir, hyb, chan):
    res = load_tiff_stack(input_dir + '{}/c{}.TIF'.format(hyb, chan))
    return res


def load_and_write_data(input_dir, output_dir):
    prefix = 'fov_0'

    hyb1 = [load_hyb_chan(input_dir, 1, c) for c in [2, 3, 4, 5]]
    hyb2 = [load_hyb_chan(input_dir, 2, c) for c in [2, 3, 4, 5]]
    hyb3 = [load_hyb_chan(input_dir, 3, c) for c in [2, 3, 4, 5]]
    hyb4 = [load_hyb_chan(input_dir, 4, c) for c in [2, 3, 4, 5]]

    dapi = load_tiff_stack(input_dir + 'DO/c1.TIF')
    dots = load_tiff_stack(input_dir + 'DO/c2.TIF')

    hyb_list = [hyb1, hyb2, hyb3, hyb4]

    res = dict()
    res['data'] = []
    res['aux'] = []
    res['metadata'] = dict()

    for h, hyb in enumerate(hyb_list):
        for c, img in enumerate(hyb):
            fname = '{}_H_{}_C_{}.tiff'.format(prefix, h, c)
            path = output_dir + fname
            d = {'hyb': h,
                 'ch': c,
                 'file': fname}
            res['data'].append(d)
            imsave(path, img)

    dapi_fname = '{}_{}.tiff'.format(prefix, 'dapi')
    imsave(output_dir + dapi_fname, dapi)
    res['aux'].append({'type': 'dapi', 'file': dapi_fname, 'format': "TIFF"})

    dots_fname = '{}_{}.tiff'.format(prefix, 'dots')
    imsave(output_dir + dots_fname, dots)
    res['aux'].append({'type': 'dots', 'file': dots_fname, 'format': "TIFF"})

    res['metadata']['num_hybs'] = 4
    res['metadata']['num_chs'] = 4
    res['metadata']['shape'] = img.shape
    res['metadata']['format'] = "TIFF"

    return res


def write_json(res, output_dir):
    org_json = json.dumps(res, indent=4)
    print(org_json)
    fname = output_dir + 'org.json'
    print("Writing org.json to: {}".format(fname))
    with open(fname, 'w') as outfile:
        json.dump(res, outfile, indent=4)


@click.command()
@click.argument('input_dir', type=click.Path(exists=True))
@click.argument('output_dir', type=click.Path(exists=True))
@click.option('--d', default=False, help='Download data', type=bool)
def format_data(input_dir, output_dir, d):
    if not input_dir.endswith('/'):
        input_dir += '/'

    if not output_dir.endswith('/'):
        output_dir += '/'

    if d:
        url = "http://d1zymp9ayga15t.cloudfront.net/content/Examplezips/ExampleInSituSequencing.zip"
        download(input_dir, url)
        input_dir += 'ExampleInSituSequencing/'
        print("Data downloaded to: {}".format(input_dir))

    res = load_and_write_data(input_dir, output_dir)
    write_json(res, output_dir)


if __name__ == '__main__':
    format_data()
