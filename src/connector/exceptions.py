from dataclasses import dataclass


@dataclass
class PushMetricsFailed(Exception):
    detail: str
