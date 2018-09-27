import warnings

import pytest
from pkg_resources import resource_filename

from .util import SpaceTxValidator
from .validate_sptx import validate

experiment_schema_path = resource_filename("validate_sptx", "schema/experiment.json")
validator = SpaceTxValidator(experiment_schema_path)
example = resource_filename("validate_sptx", "examples/experiment/experiment.json")


def test_fov():
    assert validator.validate_file(example)


def test_nuclei_must_be_present():
    wrong_nuclei = validator.load_json(example)
    wrong_nuclei['auxiliary_images'] = {'not_nuclei': 'nuclei.json'}
    with pytest.warns(UserWarning):
        assert not validator.validate_object(wrong_nuclei)


def test_version_must_be_semantic():
    wrong_version = validator.load_json(example)
    wrong_version['version'] = '10a'
    with pytest.warns(UserWarning):
        assert not validator.validate_object(wrong_version)


def test_dartfish_example_experiment():
    dartfish_example = resource_filename(
        "validate_sptx", "examples/experiment/dartfish_experiment.json")
    assert validator.validate_file(dartfish_example)


# see #614
def test_no_manifest_example_experiment():
    no_manifest_example = resource_filename(
        "validate_sptx", "examples/experiment/no_manifest.json")

    # SpaceTxValidator doesn't handle multiple files so this passes
    assert validator.validate_file(no_manifest_example)

    # But our tree walker *does* handle multiple files
    with warnings.catch_warnings(record=True) as warnings_:
        assert not validate(no_manifest_example)
        assert len(warnings_) == 1
