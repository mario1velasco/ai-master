import app


def test_importa_y_tiene_version() -> None:
    assert app.__version__ == "0.1.0"
