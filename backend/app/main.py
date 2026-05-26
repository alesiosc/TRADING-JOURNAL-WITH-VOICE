import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Ensure project root is on sys.path for brokers/ and other top-level packages
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from app.config import settings
from app.database import engine, Base
from app.routers import trades, journal, screenshots, stats, import_csv, instruments, ai, analytics, voice, active_trade, broker_sync
from app.services.websocket_manager import manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # -----------------------------------------------------------------------
    # Startup: create all tables
    # -----------------------------------------------------------------------
    Base.metadata.create_all(bind=engine)

    # -----------------------------------------------------------------------
    # Startup: initialize the screenshot module
    # -----------------------------------------------------------------------
    screenshot_mod = None
    try:
        from screenshot_module import ScreenshotModule

        # Path to config.yaml inside the screenshot_module directory
        module_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "screenshot_module")
        config_path = os.path.join(module_dir, "config.yaml")

        screenshot_mod = ScreenshotModule(config_path=config_path)
        screenshot_mod.start()

        # Inject into the screenshots router so API endpoints can use it
        from app.routers.screenshots import configure_screenshot_module
        configure_screenshot_module(screenshot_mod)

        print(f"📸 Screenshot module loaded from {config_path}")
    except Exception as e:
        print(f"⚠️  Screenshot module not available: {e}")
        print("   API capture endpoints will return 503. Install mss/pynput to enable.")

    yield

    # -----------------------------------------------------------------------
    # Shutdown
    # -----------------------------------------------------------------------
    if screenshot_mod:
        try:
            screenshot_mod.stop()
        except Exception:
            pass


app = FastAPI(title="Trading Journal API", version="2.0.0", lifespan=lifespan)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Static files (serving uploaded screenshots)
# ---------------------------------------------------------------------------
uploads_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "uploads")
os.makedirs(uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(trades.router)
app.include_router(journal.router)
app.include_router(screenshots.router)
app.include_router(stats.router)
app.include_router(import_csv.router)
app.include_router(instruments.router)
app.include_router(ai.router)
app.include_router(analytics.router)
app.include_router(broker_sync.router)
app.include_router(voice.router)
app.include_router(active_trade.router)


# ---------------------------------------------------------------------------
# WebSocket endpoint
# ---------------------------------------------------------------------------
@app.websocket("/api/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Keep the connection alive; handle incoming messages if needed
        while True:
            data = await websocket.receive_text()
            # Could echo or handle client messages here if needed
            # For now, just keep-alive by receiving
            pass
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------
@app.get("/api/health")
def health_check():
    return {"status": "ok"}
