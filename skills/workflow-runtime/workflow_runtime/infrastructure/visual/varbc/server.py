from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from workflow_runtime.application.visual.varbc.service import VARService


class FastAPIServer:
    """FastAPI HTTP Bridge wrapper enabling REST API control of Python VAR."""

    def __init__(self, service: VARService) -> None:
        """Initializes FastAPI server with VARService dependency."""
        self._service = service
        self._app = FastAPI(title="Python VAR Service Bridge", version="1.0.0")
        self._setup_routes()

    @property
    def app(self) -> FastAPI:
        """Returns underlying FastAPI instance."""
        return self._app

    def _setup_routes(self) -> None:
        """Registers REST API endpoints."""

        class RunRequest(BaseModel):
            url: str
            selector: str = "body"

        @self._app.get("/health")
        async def health_check():  # pyright: ignore[reportUnusedFunction]
            return {"status": "healthy", "service": "python-varbc"}

        @self._app.post("/var/capture")
        async def capture_endpoint(req: RunRequest):  # pyright: ignore[reportUnusedFunction]
            try:
                obs, _ = await self._service.capture_screenshot(req.url, req.selector)
                return obs.model_dump()
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
