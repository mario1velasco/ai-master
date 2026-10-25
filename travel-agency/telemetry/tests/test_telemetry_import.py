import telemetry


def test_importa_y_tiene_version() -> None:
    assert telemetry.__version__ == "0.1.0"
