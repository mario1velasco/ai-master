import contracts


def test_importa_y_tiene_version() -> None:
    assert contracts.__version__ == "0.1.0"
