import pytest

from docker0s.app.names import normalise_name


@pytest.mark.parametrize(
    "src, out",
    [
        ("One", "One"),
        ("TwoWords", "TwoWords"),
        ("HasThreeWords", "HasThreeWords"),
    ],
)
def test_normalise_name__pascal_case_in__pascal_case_out(src, out):
    assert normalise_name(src) == out


@pytest.mark.parametrize(
    "src, out",
    [
        ("one", "One"),
        ("twoWords", "TwoWords"),
        ("hasThreeWords", "HasThreeWords"),
    ],
)
def test_normalise_name__camel_case_in__pascal_case_out(src, out):
    assert normalise_name(src) == out


@pytest.mark.parametrize(
    "src, out",
    [
        ("one", "One"),
        ("two_words", "TwoWords"),
        ("has_three_words", "HasThreeWords"),
    ],
)
def test_normalise_name__snake_case_in__pascal_case_out(src, out):
    assert normalise_name(src) == out


@pytest.mark.parametrize(
    "src, out",
    [
        ("one", "One"),
        ("two-words", "TwoWords"),
        ("has-three-words", "HasThreeWords"),
    ],
)
def test_normalise_name__kebab_case_in__pascal_case_out(src, out):
    assert normalise_name(src) == out


@pytest.mark.parametrize(
    "src, out",
    [
        ("one ", "One"),
        ("one !", "One"),
        ("two words", "TwoWords"),
        ("two 123 words", "TwoWords"),
        ("has-three_words", "HasThreeWords"),
        ("this has-four_words", "ThisHasFourWords"),
    ],
)
def test_normalise_name__rubbish_in__pascal_case_out(src, out):
    assert normalise_name(src) == out
