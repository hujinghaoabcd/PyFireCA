from importlib.metadata import version

import pyfireca


def test_runtime_version_matches_distribution_metadata() -> None:
    assert pyfireca.__version__ == version("pyfireca")
