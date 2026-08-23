"""boto3 DynamoDB resource factory. Same code targets dynamodb-local (tests,
local dev) or real AWS (EC2) purely via DYNAMODB_ENDPOINT_URL — see config.py.

Note for any future writer of numeric attributes (e.g. alignment_score from
the deferred LLM-orchestration phase): boto3's DynamoDB resource rejects
Python floats outright ("Float types are not supported. Use Decimal types
instead.") — use decimal.Decimal for anything written to an N attribute."""

from decimal import Decimal
from typing import Any

import boto3

from app.config import get_settings


def get_dynamodb_resource():
    settings = get_settings()
    kwargs: dict[str, str] = {"region_name": settings.aws_region}
    if settings.dynamodb_endpoint_url:
        kwargs["endpoint_url"] = settings.dynamodb_endpoint_url
    return boto3.resource("dynamodb", **kwargs)


def floats_to_decimal(value: Any) -> Any:
    """Recursively convert every float in a dict/list tree to Decimal — see
    the module note above. Orchestration results (alignment_score, etc.)
    come back from openexec as plain Python floats."""
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, dict):
        return {k: floats_to_decimal(v) for k, v in value.items()}
    if isinstance(value, list):
        return [floats_to_decimal(v) for v in value]
    return value
