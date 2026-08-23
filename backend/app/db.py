"""boto3 DynamoDB resource factory. Same code targets dynamodb-local (tests,
local dev) or real AWS (EC2) purely via DYNAMODB_ENDPOINT_URL — see config.py.

Note for any future writer of numeric attributes (e.g. alignment_score from
the deferred LLM-orchestration phase): boto3's DynamoDB resource rejects
Python floats outright ("Float types are not supported. Use Decimal types
instead.") — use decimal.Decimal for anything written to an N attribute."""

import boto3

from app.config import get_settings


def get_dynamodb_resource():
    settings = get_settings()
    kwargs: dict[str, str] = {"region_name": settings.aws_region}
    if settings.dynamodb_endpoint_url:
        kwargs["endpoint_url"] = settings.dynamodb_endpoint_url
    return boto3.resource("dynamodb", **kwargs)
