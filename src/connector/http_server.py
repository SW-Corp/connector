from fastapi import FastAPI
from dataclasses import dataclass

@dataclass
class HTTPServer:
        
    def build_app(self) -> FastAPI:  # noqa: C901
        app = FastAPI(title="HTTP keyserver", version="0.1")

        @app.get("/test")
        async def test():
            return "Hello world"

        return app