import json
import logging as logger
from dataclasses import dataclass
from distutils.command.config import config
from http.client import HTTPConnection
from typing import List
from abc import ABC, abstractmethod

from pydantic import BaseModel

from .exceptions import PushMetricsFailed


@dataclass
class BackendConfig:
    addr: str
    port: int
    workstation_name: str


class MetricsData(BaseModel):
    measurement: str
    field: str
    value: float


class MetricsList(BaseModel):
    workstation_name: str
    metrics: List[MetricsData]

@dataclass
class BackendConnectorBase(ABC):
    config: BackendConfig

    @abstractmethod
    def push_metrics(self, metrics: List[MetricsData]) -> None:
        pass

@dataclass
class BackendConnector(BackendConnectorBase):
    config: BackendConfig

    def __post_init__(self):
        self.httpConnection: HTTPConnection = HTTPConnection(
            self.config.addr, self.config.port
        )

    def push_metrics(self, metrics: List[MetricsData]) -> None:
        body = MetricsList(
            workstation_name=self.config.workstation_name, metrics=metrics
        )
        body = body.json()
        try:
            self.httpConnection.request("POST", "/metrics", body)
        except Exception as e:
            print(f"Error pushing metrics {e}")
            raise PushMetricsFailed(e)
        response = self.httpConnection.getresponse()
        data = response.read()
        if response.status != 200:
            print(f"Error pushingn metrics")
            raise PushMetricsFailed(f"code: {response.status}, detail: {data}")


@dataclass
class MockBackendConnector(BackendConnectorBase):

    def push_metrics(self, metrics: List[MetricsData]) -> None:
        logger.debug("Pushing metrics to the backend right now.")
