import pytest

from docker0s.app.names import normalise_name, pascal_to_snake


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


@pytest.mark.parametrize(
    "src, out",
    [
        ("One", "one"),
        ("TwoWords", "two_words"),
        ("HasThreeWords", "has_three_words"),
    ],
)
def test_pascal_to_snake__pascal_in__snake_out(src, out):
    assert pascal_to_snake(src) == out


@pytest.mark.parametrize(
    "src, out",
    [
        ("one ", "one "),
        ("one !", "one !"),
        ("two words", "two words"),
        ("two 123 Words", "two 123 _words"),
        ("has-three_words", "has-three_words"),
        ("this has-Four_words", "this has-_four_words"),
    ],
)
def test_pascal_to_snake__rubbish_in__rubbish_out(src, out):
    assert pascal_to_snake(src) == out
