"""Re-export the FastAPI app so `uvicorn backend.main:app` still works."""

from app.main import APP_ENV, PORT, app

__all__ = ["APP_ENV", "PORT", "app"]


if __name__ == "__main__":
    import sys
    from pathlib import Path

    import uvicorn

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=PORT,
        reload=(APP_ENV == "development"),
    )
