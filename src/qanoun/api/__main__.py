"""uv run python -m qanoun.api [--host 127.0.0.1] [--port 8000]"""

import argparse

import uvicorn

from qanoun.api.app import create_app
from qanoun.generation.llm import configure_logging


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Qanoun AI web service.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    configure_logging()
    print(f"Qanoun AI on http://{args.host}:{args.port}  (API docs: /docs)")
    uvicorn.run(create_app(), host=args.host, port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
