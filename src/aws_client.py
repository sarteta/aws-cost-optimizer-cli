"""Thin wrapper around boto3 + a mock driver for offline runs.

The mock driver returns synthetic data shaped like boto3 responses, so
the findings modules don't need to know which one they're talking to.
"""

from __future__ import annotations

from typing import Any, Protocol


class AWSClient(Protocol):
    account_id: str | None

    def ec2(self, region: str) -> Any: ...
    def rds(self, region: str) -> Any: ...
    def s3(self, region: str) -> Any: ...
    def cloudwatch(self, region: str) -> Any: ...


class BotoClient:
    """Real AWS client. Lazy-initialises per-service clients per region."""

    def __init__(self, profile: str | None = None):
        import boto3  # local import so `--mock` works without boto installed

        self.session = boto3.Session(profile_name=profile) if profile else boto3.Session()
        self._cache: dict[tuple[str, str], Any] = {}
        try:
            sts = self.session.client("sts")
            self.account_id = sts.get_caller_identity()["Account"]
        except Exception:
            self.account_id = None

    def _client(self, service: str, region: str) -> Any:
        key = (service, region)
        if key not in self._cache:
            self._cache[key] = self.session.client(service, region_name=region)
        return self._cache[key]

    def ec2(self, region: str) -> Any:
        return self._client("ec2", region)

    def rds(self, region: str) -> Any:
        return self._client("rds", region)

    def s3(self, region: str) -> Any:
        return self._client("s3", region)

    def cloudwatch(self, region: str) -> Any:
        return self._client("cloudwatch", region)


class MockClient:
    """Synthetic AWS account with a known set of leaks.

    Used for `--mock` runs and for unit tests. The data is deterministic:
    same call → same response, so reports are reproducible.
    """

    account_id = "123456789012"

    def __init__(self) -> None:
        from .mock_data import build_mock_account

        self._data = build_mock_account()

    def _service(self, name: str, region: str) -> Any:
        return _MockService(self._data, name, region)

    def ec2(self, region: str) -> Any:
        return self._service("ec2", region)

    def rds(self, region: str) -> Any:
        return self._service("rds", region)

    def s3(self, region: str) -> Any:
        return self._service("s3", region)

    def cloudwatch(self, region: str) -> Any:
        return self._service("cloudwatch", region)


class _MockService:
    """Dispatches attribute access to mock_data handlers."""

    def __init__(self, data: dict, service: str, region: str):
        self._data = data
        self._service = service
        self._region = region

    def __getattr__(self, method: str):
        def _call(**kwargs):
            return self._data[self._service][method](self._region, **kwargs)
        return _call


def build_client(*, mock: bool, profile: str | None = None) -> AWSClient:
    return MockClient() if mock else BotoClient(profile=profile)
