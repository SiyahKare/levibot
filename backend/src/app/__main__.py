from __future__ import annotations

import os

import uvicorn

from .main import app


def main() -> None:
    host = os.getenv("LEVI_API_HOST", "0.0.0.0")
    port = int(os.getenv("LEVI_API_PORT", "8000"))
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
