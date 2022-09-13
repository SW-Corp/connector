from dataclasses import dataclass

@dataclass
class Status:
    status_code: int
    content: str

@dataclass
class StatusHandler:
    current_status: Status

    def setStatus(self, stat: Status):
        self.current_status = stat

    def getCode(self):
        return self.current_status.status_code

    def getContent(self):
        return self.current_status.content