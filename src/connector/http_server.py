from dataclasses import dataclass
from fastapi import FastAPI, Request
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, Response
from .communication import HardwareCommunicator
from .status_handler import StatusHandler
from .task_models import (Task)


@dataclass
class HTTPServerConfig:
    backend_address: str
    backend_port: int


@dataclass
class HTTPServer:
    config: HTTPServerConfig
    statusHandler: StatusHandler
    hardwareCommunicator: HardwareCommunicator

    def build_app(self) -> FastAPI:  # noqa: C901
        app = FastAPI(title="HTTP keyserver", version="0.1")

        # idk
        # app.add_middleware(
        #     TrustedHostMiddleware, allowed_hosts=[self.config.backend_address]
        # )

        @app.post("/task")
        def receiveTask(task: Task, request: Request):
            # validation
            if task.action not in ["is_open", "is_on", "stop"] or task.target[0] not in ["P", "V", "s"]:
                return Response(status_code=400, content="Invalid request.")

            try:  # try except because int() may fail in some cases
                if int(task.value) not in [1, 0]:
                    raise Exception
            except Exception:
                return Response(status_code=400, content="Invalid value.")

            self.hardwareCommunicator.processTask(task)
            return Response(content="Task accepted.")

        @app.get("/status")
        def reportStatus():
            return JSONResponse(
                status_code=self.statusHandler.getCode(),
                content=self.statusHandler.getContent(),
            )

        @app.get("/sendtest")
        def sendtest():
            self.hardwareCommunicator.send("?")
            return JSONResponse(status_code=200, content="sent '?' char")

        return app
