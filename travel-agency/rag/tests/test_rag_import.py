import rag


def test_importa_y_tiene_version() -> None:
    assert rag.__version__ == "0.1.0"
