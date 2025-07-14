from contextvars import ContextVar

call_id_var: ContextVar[str] = ContextVar("call_id", default="N/A")