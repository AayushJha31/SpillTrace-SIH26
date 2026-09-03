import uuid
from fastapi import Header


def get_run_id(x_run_id: str | None = Header(default=None)) -> str:
    return x_run_id or str(uuid.uuid4())