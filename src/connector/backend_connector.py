import json
import time
import logging as logger
import requests
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
    session: requests.Session = None
    addr: str = ''

    def __post_init__(self):
        self.addr = f'http://{self.config.addr}:{self.config.port}'
        self.login() 

    def login(self):
        self.session = requests.Session()
        logger.debug("Sending login request...")
        data = {"email": "connector", "password": "1qaz098"}
        try:
            req = self.session.post(f"{self.addr}/login", data=json.dumps(data))
            if req.status_code>=200 and req.status_code<300:
                print("Logged in successfully.")
        except:
            print("Major error. Retrying in 5 seconds...")
            time.sleep(5)
            self.login()


    def logout(self):
        self.session.get(f"{self.addr}/logout")
        self.login()

    def push_metrics(self, metrics: List[MetricsData]) -> None:
        body = MetricsList(
            workstation_name=self.config.workstation_name, metrics=metrics
        )
        body = body.json()
        try:
            response = self.session.post(f"{self.addr}/metrics", body)
            logger.debug(f"Response: {response}")
        except Exception as e:
            print(f"Error pushing metrics {e}")
            raise PushMetricsFailed(e)

        if response.status_code == 401:
            print("Reauth procedure...")
            self.logout()
        elif response.status_code > 299:
            print(f"Error pushing metrics")
            raise PushMetricsFailed(f"code: {response.status_code}")


@dataclass
class MockBackendConnector(BackendConnectorBase):

    def push_metrics(self, metrics: List[MetricsData]) -> None:
        logger.debug("Pushing metrics to the backend right now.")
