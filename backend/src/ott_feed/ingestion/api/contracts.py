"""Versioned U04 operator and validation-rule API contracts."""

from pydantic import BaseModel, ConfigDict, Field


class RuleContractResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    contract_version: str
    rule_version: str
    required_evidence_fields: list[str]
    allowed_content_types: list[str]
    max_runtime_minutes: int = Field(gt=0)


class JobStatusResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    job_id: str
    provider_id: str
    status: str
    durable_cursor_present: bool
    succeeded_count: int = Field(ge=0)
    quarantined_count: int = Field(ge=0)
    failed_count: int = Field(ge=0)


class RetryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    target_rule_version: str = Field(min_length=1, max_length=80)


class RetryResponse(BaseModel):
    attempt_key: str
    status: str = "scheduled"
