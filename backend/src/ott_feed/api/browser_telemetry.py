"""Privacy-bounded browser telemetry ingestion."""

from typing import Annotated, Literal

from fastapi import APIRouter, Header, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field, ValidationError

_event_counts: dict[tuple[str, str], int] = {}
_dropped_count = 0


class BrowserEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: Literal["web_vital", "route_outcome", "api_outcome", "ui_error"]
    route: str = Field(max_length=80, pattern=r"^/[a-z:/_-]*$")
    outcome: str = Field(max_length=24, pattern=r"^[a-z_]+$")
    value: float | None = Field(default=None, ge=0, le=1_000_000)


def create_browser_telemetry_router() -> APIRouter:
    router = APIRouter(prefix="/api/v1/telemetry", tags=["telemetry"])

    @router.post("/browser", status_code=204)
    async def ingest_browser_events(
        request: Request,
        content_length: Annotated[int | None, Header(le=16_384)] = None,
    ) -> Response:
        global _dropped_count
        if content_length is not None and content_length > 16_384:
            _dropped_count += 1
            raise HTTPException(status_code=413, detail="telemetry batch too large")
        body = await request.json()
        if not isinstance(body, list) or len(body) > 50:
            _dropped_count += 1
            raise HTTPException(status_code=422, detail="invalid telemetry batch")
        try:
            events = [BrowserEvent.model_validate(item) for item in body]
        except ValidationError as error:
            _dropped_count += 1
            raise HTTPException(status_code=422, detail="invalid telemetry event") from error
        for item in events:
            key = (item.name, item.outcome)
            _event_counts[key] = _event_counts.get(key, 0) + 1
        return Response(status_code=204)

    return router


def browser_metrics() -> str:
    lines = ["# TYPE ott_browser_events_total counter"]
    lines.extend(
        f'ott_browser_events_total{{name="{name}",outcome="{outcome}"}} {count}'
        for (name, outcome), count in sorted(_event_counts.items())
    )
    lines.extend(
        [
            "# TYPE ott_browser_telemetry_dropped_total counter",
            f"ott_browser_telemetry_dropped_total {_dropped_count}",
        ]
    )
    return "\n".join(lines) + "\n"
