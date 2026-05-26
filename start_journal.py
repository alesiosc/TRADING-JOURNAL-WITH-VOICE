"""
Trading Journal With Voice — Master Launcher

Starts all components:
  1. Backend (FastAPI on port 8000)
  2. Frontend (React/Vite dev server on port 5173) — if available
  3. Broker CSV watcher (if configured)

Usage:
    python start_journal.py            # Start everything
    python start_journal.py --no-ui    # Start without frontend
    python start_journal.py --no-watch # Start without CSV watcher
    python start_journal.py --port 8000  # Custom backend port

Press Ctrl+C to stop all components gracefully.
"""

import argparse
import logging
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent


def setup_logging():
    """Configure logging."""
    log_dir = PROJECT_ROOT / "logs"
    log_dir.mkdir(exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        handlers=[
            logging.FileHandler(log_dir / "journal.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def start_backend(port: int) -> subprocess.Popen:
    """Start the FastAPI backend server."""
    logging.info("Starting backend on port %d...", port)
    env = os.environ.copy()
    env["CORS_ORIGINS"] = f"http://localhost:5173,http://localhost:{port}"

    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app",
         "--host", "0.0.0.0", "--port", str(port),
         "--reload", "--log-level", "info"],
        cwd=str(PROJECT_ROOT / "backend"),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    return proc


def start_frontend() -> subprocess.Popen:
    """Start the React/Vite frontend dev server."""
    frontend_dir = PROJECT_ROOT / "frontend"
    if not (frontend_dir / "package.json").exists():
        logging.warning("Frontend not found at %s", frontend_dir)
        return None

    logging.info("Starting frontend on port 5173...")
    proc = subprocess.Popen(
        ["npx", "vite", "--port", "5173"],
        cwd=str(frontend_dir),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    return proc


def start_csv_watcher() -> subprocess.Popen:
    """Start the broker CSV watcher."""
    watcher_dir = PROJECT_ROOT / "broker_watcher"
    if not (watcher_dir / "__main__.py").exists():
        logging.warning("Broker watcher not found at %s", watcher_dir)
        return None

    logging.info("Starting CSV watcher...")
    proc = subprocess.Popen(
        [sys.executable, "-m", "broker_watcher"],
        cwd=str(PROJECT_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    return proc


def tail_output(proc: subprocess.Popen, name: str):
    """Print output from a process."""
    try:
        for line in iter(proc.stdout.readline, ""):
            if line:
                print(f"[{name}] {line.rstrip()}")
    except (ValueError, OSError):
        pass


def check_ollama():
    """Check if Ollama is running."""
    import urllib.request
    import json

    try:
        req = urllib.request.Request(
            "http://localhost:11434/api/tags",
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read())
            models = [m["name"] for m in data.get("models", [])]
            logging.info("Ollama running with models: %s", ", ".join(models[:5]) + ("..." if len(models) > 5 else ""))
            return True
    except Exception:
        logging.warning(
            "Ollama not detected. AI features (trade debrief, auto-tag) will not work.\n"
            "  Install: https://ollama.com\n"
            "  Then: ollama pull qwen3:8b"
        )
        return False


def check_whisper():
    """Check if whisper-cli is available."""
    whisper = subprocess.run(
        ["which", "whisper-cli"] if os.name != "nt" else ["where", "whisper-cli.exe"],
        capture_output=True, text=True, timeout=5,
    )
    if whisper.returncode == 0:
        logging.info("Whisper.cpp found: %s", whisper.stdout.strip().split("\n")[0])
        return True
    else:
        logging.info("Whisper.cpp not in PATH. Voice transcription requires manual setup.")
        return False


def main():
    parser = argparse.ArgumentParser(description="Trading Journal With Voice — Master Launcher")
    parser.add_argument("--no-ui", action="store_true", help="Skip frontend")
    parser.add_argument("--no-watch", action="store_true", help="Skip CSV watcher")
    parser.add_argument("--no-browser", action="store_true", help="Don't open browser")
    parser.add_argument("--port", type=int, default=8000, help="Backend port")
    args = parser.parse_args()

    setup_logging()

    print("""
  ╔══════════════════════════════════════════════╗
  ║    Trading Journal With Voice — Launcher     ║
  ║    Free · Local-first · AI-powered           ║
  ╚══════════════════════════════════════════════╝
    """)

    # Check prerequisites
    check_ollama()
    check_whisper()

    procs = []
    threads = []

    # Start backend
    try:
        backend = start_backend(args.port)
        procs.append(("backend", backend))
        t = threading.Thread(target=tail_output, args=(backend, "backend"), daemon=True)
        t.start()
        threads.append(t)
        time.sleep(2)
    except Exception as e:
        logging.error("Failed to start backend: %s", e)

    # Start frontend (optional)
    if not args.no_ui:
        try:
            frontend = start_frontend()
            if frontend:
                procs.append(("frontend", frontend))
                t = threading.Thread(target=tail_output, args=(frontend, "frontend"), daemon=True)
                t.start()
                threads.append(t)
        except Exception as e:
            logging.warning("Could not start frontend: %s", e)

    # Start CSV watcher (optional)
    if not args.no_watch:
        try:
            watcher = start_csv_watcher()
            if watcher:
                procs.append(("watcher", watcher))
                t = threading.Thread(target=tail_output, args=(watcher, "watcher"), daemon=True)
                t.start()
                threads.append(t)
        except Exception as e:
            logging.warning("Could not start CSV watcher: %s", e)

    print(f"""
  ┌──────────────────────────────────────────────┐
  │  ✅ System Running                           │
  │                                              │
  │  Backend API:   http://localhost:{args.port}         │
  │  Frontend:      http://localhost:5173        │
  │  API Docs:      http://localhost:{args.port}/docs   │
  │  Health Check:  http://localhost:{args.port}/api/health │
  │                                              │
  │  Press Ctrl+C to stop all components         │
  └──────────────────────────────────────────────┘
    """)

    # Open browser (optional)
    if not args.no_browser:
        import webbrowser
        try:
            webbrowser.open(f"http://localhost:{args.port}")
        except Exception:
            pass

    # Wait for Ctrl+C
    try:
        while True:
            time.sleep(1)
            # Check if any process died
            for name, proc in procs:
                if proc.poll() is not None:
                    logging.error("%s stopped unexpectedly (exit code %d)", name, proc.returncode)
                    raise SystemExit(1)
    except KeyboardInterrupt:
        print("\n\nShutting down...")
    except SystemExit:
        pass
    finally:
        # Stop all processes
        for name, proc in procs:
            if proc.poll() is None:
                logging.info("Stopping %s...", name)
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()

    print("All components stopped. Goodbye.")


if __name__ == "__main__":
    main()
