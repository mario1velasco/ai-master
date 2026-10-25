import database


def test_importa_y_tiene_version() -> None:
    assert database.__version__ == "0.1.0"
