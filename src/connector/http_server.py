from dataclasses import dataclass
from enum import Enum
from typing import List

from fastapi import FastAPI
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
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
    action: str
    target: str
    value: float
    conditions: Conditions


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

        app.add_middleware(
            TrustedHostMiddleware, allowed_hosts=[self.config.backend_address]
        )

        @app.get("/test")
        async def test():
            return "Hello world"

        @app.post("/task")
        def receiveTask(task: Task):
            print(f"received task!: {task}")

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
