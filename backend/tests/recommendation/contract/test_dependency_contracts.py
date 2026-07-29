from inspect import signature

import pytest

from ott_feed.catalog.ports import ApprovedCatalogReadPort
from ott_feed.identity.application.features import FeatureService
from ott_feed.ingestion.contracts import ValidationPredicateContract

pytestmark = pytest.mark.contract


def test_u02_feature_snapshot_contract_is_request_scoped() -> None:
    parameters = signature(FeatureService.snapshot).parameters
    assert tuple(parameters) == ("self", "user_id", "request_id")


def test_u03_approved_catalog_contract_requires_content_and_region() -> None:
    parameters = signature(ApprovedCatalogReadPort.get_approved).parameters
    assert tuple(parameters) == ("self", "content_id", "region")


def test_u04_validation_contract_is_versioned_and_bounded() -> None:
    contract = ValidationPredicateContract("1", "rules-1", ("title", "runtime"), ("movie",), 180)
    assert contract.public_dict() == {
        "contract_version": "1",
        "rule_version": "rules-1",
        "required_evidence_fields": ("title", "runtime"),
        "allowed_content_types": ("movie",),
        "max_runtime_minutes": 180,
    }


def test_u04_validation_contract_rejects_unbounded_runtime() -> None:
    with pytest.raises(ValueError, match="runtime bound"):
        ValidationPredicateContract("1", "rules-1", (), ("movie",), 0)
