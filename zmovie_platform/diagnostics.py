from .health import health_report
from .metrics import snapshot


def diagnostics() -> dict[str, object]:
    return {"health": health_report(), "metrics": snapshot()}
