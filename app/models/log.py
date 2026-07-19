from datetime import datetime
from pydantic import BaseModel

class RequestLogData(BaseModel):
    level: str = "INFO"
    timestamp: datetime
    request_id: str
    method: str
    path: str
    status_code: int
    process_time_ms: float
    client_ip: str | None = None
    user_agent: str | None = None
    exception: str | None = None
