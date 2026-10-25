import agent


def test_importa_y_tiene_version() -> None:
    assert agent.__version__ == "0.1.0"
