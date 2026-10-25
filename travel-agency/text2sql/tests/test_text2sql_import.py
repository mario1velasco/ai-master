import text2sql


def test_importa_y_tiene_version() -> None:
    assert text2sql.__version__ == "0.1.0"
