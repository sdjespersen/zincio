import zincio
from pathlib import Path


def get_abspath(relpath):
    return Path(__file__).parent / relpath


SINGLE_SERIES_FILE = get_abspath("single_series_grid.zinc")


def test_grid_to_zinc_string():
    with open(SINGLE_SERIES_FILE, encoding="utf-8") as f:
        expected = f.read()
    actual = zincio.read(SINGLE_SERIES_FILE).to_zinc()
    assert actual == expected


def test_grid_to_zinc_file(tmp_path):
    with open(SINGLE_SERIES_FILE, encoding="utf-8") as f:
        expected = f.read()
    output_file = tmp_path / "output.zinc"
    zincio.read(SINGLE_SERIES_FILE).to_zinc(output_file)
    with open(output_file, encoding="utf-8") as f:
        actual = f.read()
    assert actual == expected
