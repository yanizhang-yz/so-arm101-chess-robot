import pytest

from chessbot.board import BoardGeometry, parse_square, square_name


def test_parse_square_roundtrip():
    for sq in ("a1", "e4", "h8", "d5"):
        f, r = parse_square(sq)
        assert square_name(f, r) == sq


def test_parse_square_is_case_insensitive():
    assert parse_square("E4") == parse_square("e4") == (4, 3)


@pytest.mark.parametrize("bad", ["", "e", "e9", "i1", "11", "e44"])
def test_parse_square_rejects_garbage(bad):
    with pytest.raises(ValueError):
        parse_square(bad)


def test_square_center_geometry():
    geo = BoardGeometry(square_size_m=0.04)
    assert geo.square_center("a1") == (0.0, 0.0)
    assert geo.square_center("b1") == (0.04, 0.0)   # one file over (+x)
    assert geo.square_center("a2") == (0.0, 0.04)   # one rank up (+y)
    x, y = geo.square_center("h8")
    assert x == pytest.approx(0.28) and y == pytest.approx(0.28)


def test_bad_square_size_rejected():
    with pytest.raises(ValueError):
        BoardGeometry(square_size_m=0.0)
