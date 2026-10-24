"""Punto de arranque de EBIS Calendar API."""

import uvicorn


def main() -> None:
    uvicorn.run("api:app", host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
