from dataclasses import dataclass
from enum import Enum
from typing import List

from fastapi import FastAPI, Request
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

from connector.communication import HardwareCommunicator

from .status_handler import StatusHandler


class Operator(str, Enum):
    AND = "and"
    OR = "or"


class ConditionType(str, Enum):
    TIMEOUT = "timeout"
    EQUAL = "equal"
    LESS = "less"
    MORE = "more"
    MOREEQUAL = "moreequal"
    LESSEQUAL = "lessequal"


class Condition(BaseModel):
    type: ConditionType
    measurement: str
    field: str
    value: float


class Conditions(BaseModel):
    operator: Operator
    conditionlist: List[Condition]


class Task(BaseModel):
    action: str  # is_open (valve) or is_on (pump)
    target: str  # Px, Vx
    value: float # 1.0 or 0.0


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
            if task.action not in ["is_open", "is_on"] or task.target[0] not in ["P", "V"]:
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
