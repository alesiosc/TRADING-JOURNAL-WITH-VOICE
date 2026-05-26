"""
Trading Journal With Voice — Backend Server Entry Point.

Starts the FastAPI server with uvicorn. Run from the backend/ directory:

    python run.py                      # default: port 8000, reload
    python run.py --port 8080          # custom port
    python run.py --no-reload          # production mode
    python run.py --host 127.0.0.1     # local-only
"""
import argparse
import os
import sys
import uvicorn


def main():
    parser = argparse.ArgumentParser(description="Trading Journal Backend")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Bind address")
    parser.add_argument("--port", type=int, default=8000, help="Port number")
    parser.add_argument("--no-reload", action="store_true", help="Disable auto-reload")
    parser.add_argument("--log-level", type=str, default="info",
                        choices=["debug", "info", "warning", "error", "critical"])
    args = parser.parse_args()

    # Ensure the backend directory is in sys.path so brokers/ etc. are importable
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)

    # Also add the project root so app can import brokers/
    project_root = os.path.dirname(backend_dir)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    print(f"""
  ╔══════════════════════════════════════════════╗
  ║    Trading Journal Backend Server            ║
  ╚══════════════════════════════════════════════╝
  Host: {args.host}
  Port: {args.port}
  Reload: {not args.no_reload}
  Log level: {args.log_level}
  API docs: http://{args.host if args.host != '0.0.0.0' else 'localhost'}:{args.port}/docs
    """)

    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=not args.no_reload,
        log_level=args.log_level,
    )


if __name__ == "__main__":
    main()
