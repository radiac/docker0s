from docker0s.env import read_env
from docker0s.path import ManifestPath


FILE1 = """# File 1
ONE=1
TWO="two"
"""

FILE2 = """# File 2
ONE="one"
THREE="three"
FOUR=4
"""


def test_paths_values_merged(tmp_path):
    file1 = tmp_path / "file1.env"
    file1.write_text(FILE1)
    file2 = tmp_path / "file2.env"
    file2.write_text(FILE2)

    data = read_env(
        ManifestPath("file1.env", manifest_dir=tmp_path),
        ManifestPath("file2.env", manifest_dir=tmp_path),
        FOUR="four",
    )
    assert data == {
        "ONE": "one",
        "TWO": "two",
        "THREE": "three",
        "FOUR": "four",
    }
