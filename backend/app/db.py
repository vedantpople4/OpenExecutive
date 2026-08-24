"""boto3 DynamoDB resource factory. Same code targets dynamodb-local (tests,
local dev) or real AWS (EC2) purely via DYNAMODB_ENDPOINT_URL — see config.py.

Two boto3 constraints bite anything writing orchestration output (see
to_dynamodb_safe below, which handles both):
- Floats are rejected outright ("Float types are not supported. Use Decimal
  types instead.") — alignment_score and friends arrive as plain floats.
- Map keys must be strings. openexec keys deliberation_rounds by integer
  round number ({1: {...}, 2: {...}}), which fails validation unless
  stringified — matching the plan's "roundNumber (as string)" schema."""

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


def to_dynamodb_safe(value: Any) -> Any:
    """Recursively coerce a dict/list tree into something boto3 will accept:
    floats -> Decimal, and non-string map keys -> str. See the module note
    above for why both are needed."""
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, dict):
        return {str(k): to_dynamodb_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [to_dynamodb_safe(v) for v in value]
    return value
