from __future__ import annotations

import math
import os
from dataclasses import fields
from typing import Any
from urllib.parse import quote

import httpx

from ..models import (
    Comparison,
    FrameDecode,
    GlossaryEntry,
    PortEntry,
    SearchResult,
    SubnetResult,
    Technology,
)
from .base import ToolkitService


class ToolkitApiError(RuntimeError):
    """The backend returned an unexpected or unsuccessful response."""


class ToolkitConnectionError(ToolkitApiError):
    """The configured backend could not be reached."""


class ToolkitAuthenticationError(ToolkitApiError):
    """The backend rejected the configured credentials."""


class HttpToolkitService(ToolkitService):
    """Synchronous HTTP implementation of the frontend service boundary."""

    DEFAULT_BASE_URL = "http://127.0.0.1:8000/api/v1"
    _TECHNOLOGY_TUPLES = {
        field.name
        for field in fields(Technology)
        if field.name
        in {
            "runs_over",
            "related",
            "ports",
            "files",
            "typical_devices",
            "applications",
            "key_concepts",
            "advantages",
            "limitations",
            "faults",
            "troubleshooting",
            "sources",
        }
    }

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        *,
        username: str = "demo",
        password: str = "demo-password",
        timeout: float = 10.0,
        client: Any | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._username = username
        self._password = password
        self._access_token: str | None = None
        self._owns_client = client is None
        self._client = client or httpx.Client(
            base_url=f"{self.base_url}/",
            timeout=timeout,
            transport=httpx.HTTPTransport(retries=2),
        )

    @classmethod
    def from_environment(cls) -> HttpToolkitService:
        """Build a client from runtime configuration without persisting secrets."""
        return cls(
            os.environ.get("OT_TOOLKIT_API_URL", cls.DEFAULT_BASE_URL),
            username=os.environ.get("OT_TOOLKIT_USERNAME", "demo"),
            password=os.environ.get("OT_TOOLKIT_PASSWORD", "demo-password"),
        )

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def _authenticate(self) -> str:
        data = self._request(
            "POST",
            "auth/token",
            json={"username": self._username, "password": self._password},
        )
        token = data.get("access_token") if isinstance(data, dict) else None
        if not token:
            raise ToolkitAuthenticationError("The backend returned no bearer token.")
        self._access_token = str(token)
        return self._access_token

    def _request(
        self,
        method: str,
        path: str,
        *,
        authenticated: bool = False,
        **kwargs: Any,
    ) -> Any:
        attempts = 2 if authenticated else 1
        base_headers = dict(kwargs.pop("headers", {}))
        for attempt in range(attempts):
            headers = dict(base_headers)
            if authenticated:
                headers["Authorization"] = f"Bearer {self._access_token or self._authenticate()}"
            try:
                response = self._client.request(method, path, headers=headers, **kwargs)
            except httpx.RequestError as exc:
                raise ToolkitConnectionError(
                    f"Cannot reach the OT Toolkit backend at {self.base_url}. "
                    "Start it with 'make api' or run both services with 'make dev'."
                ) from exc
            if authenticated and response.status_code == 401 and attempt == 0:
                self._access_token = None
                continue
            if response.is_error:
                self._raise_api_error(response)
            try:
                return response.json()
            except ValueError as exc:
                raise ToolkitApiError("The backend returned an invalid JSON response.") from exc
        raise ToolkitAuthenticationError("The backend rejected the configured credentials.")

    @staticmethod
    def _raise_api_error(response: httpx.Response) -> None:
        try:
            payload = response.json()
        except ValueError:
            payload = {}
        message = payload.get("message") if isinstance(payload, dict) else None
        message = str(message or f"Backend request failed with HTTP {response.status_code}.")
        if response.status_code == 400:
            raise ValueError(message)
        if response.status_code == 404:
            raise KeyError(message)
        if response.status_code == 401:
            raise ToolkitAuthenticationError(message)
        raise ToolkitApiError(message)

    @classmethod
    def _technology(cls, payload: dict[str, Any]) -> Technology:
        values = dict(payload)
        for name in cls._TECHNOLOGY_TUPLES:
            values[name] = tuple(values.get(name, ()))
        return Technology(**values)

    @staticmethod
    def _restore_nonfinite(value: Any) -> Any:
        if isinstance(value, dict):
            return {key: HttpToolkitService._restore_nonfinite(item) for key, item in value.items()}
        if isinstance(value, list):
            return [HttpToolkitService._restore_nonfinite(item) for item in value]
        if value == "nan":
            return math.nan
        if value == "inf":
            return math.inf
        if value == "-inf":
            return -math.inf
        return value

    def list_technologies(self, category: str | None = None) -> list[Technology]:
        params = {"category": category} if category is not None else None
        return [self._technology(item) for item in self._request("GET", "technologies", params=params)]

    def get_technology(self, technology_id: str) -> Technology:
        return self._technology(self._request("GET", f"technologies/{quote(technology_id, safe='')}"))

    def list_categories(self) -> list[str]:
        return list(self._request("GET", "categories"))

    def search(self, query: str) -> list[SearchResult]:
        if not query.strip():
            return []
        return [SearchResult(**item) for item in self._request("GET", "search", params={"q": query})]

    def compare(self, left_id: str, right_id: str) -> Comparison:
        data = self._request("POST", "comparisons", json={"left_id": left_id, "right_id": right_id})
        return Comparison(
            left=self._technology(data["left"]),
            right=self._technology(data["right"]),
            rows=tuple((row["label"], row["left"], row["right"]) for row in data["rows"]),
        )

    def hierarchy(self, technology_id: str) -> dict[str, Any]:
        data = self._request("GET", f"technologies/{quote(technology_id, safe='')}/hierarchy")
        return {
            "technology": self._technology(data["technology"]),
            "runs_over": [self._technology(item) for item in data["runs_over"]],
            "used_by": [self._technology(item) for item in data["used_by"]],
            "related": [self._technology(item) for item in data["related"]],
        }

    def list_ports(self, query: str = "") -> list[PortEntry]:
        return [PortEntry(**item) for item in self._request("GET", "ports", params={"q": query})]

    def list_glossary(self, query: str = "") -> list[GlossaryEntry]:
        output = []
        for item in self._request("GET", "glossary", params={"q": query}):
            values = dict(item)
            values["related"] = tuple(values.get("related", ()))
            output.append(GlossaryEntry(**values))
        return output

    def list_troubleshooting(self) -> dict[str, list[str]]:
        return self._request("GET", "troubleshooting")

    def favorites(self) -> set[str]:
        return set(self._request("GET", "favorites", authenticated=True)["items"])

    def set_favorite(self, item_id: str, enabled: bool) -> None:
        self._request(
            "PUT",
            f"favorites/{quote(item_id, safe='')}",
            authenticated=True,
            json={"enabled": enabled},
        )

    def number_conversion(self, value: str, numeric_format: str) -> dict[str, Any]:
        return self._request("POST", "tools/numbers/convert", json={"value": value, "numeric_format": numeric_format})

    def ieee_to_hex(self, value: float, precision: int) -> str:
        return self._request("POST", "tools/ieee754/encode", json={"value": value, "precision": precision})["hex"]

    def ieee_from_hex(self, value: str, precision: int) -> float:
        result = self._request("POST", "tools/ieee754/decode", json={"hex": value, "precision": precision})["value"]
        return float(self._restore_nonfinite(result))

    def endian_decode(self, value: str) -> dict[str, Any]:
        return self._restore_nonfinite(self._request("POST", "tools/endianness/decode", json={"hex": value}))

    def modbus_address(self, reference: str) -> dict[str, Any]:
        return self._request("POST", "tools/modbus/address", json={"reference": reference})

    def modbus_registers(self, registers: list[int]) -> dict[str, Any]:
        return self._restore_nonfinite(self._request("POST", "tools/modbus/registers/decode", json={"registers": registers}))

    def modbus_crc(self, value: str) -> dict[str, str]:
        return self._request("POST", "tools/modbus/crc", json={"hex": value})

    def modbus_frame(self, value: str) -> FrameDecode:
        return FrameDecode(**self._request("POST", "tools/modbus/frame/decode", json={"hex": value}))

    def subnet(self, ip: str, mask_or_cidr: str) -> SubnetResult:
        return SubnetResult(**self._request("POST", "tools/network/subnet", json={"ip": ip, "mask_or_cidr": mask_or_cidr}))

    def same_subnet(self, ip_a: str, ip_b: str, mask_or_cidr: str) -> dict[str, Any]:
        return self._request(
            "POST",
            "tools/network/same-subnet",
            json={"ip_a": ip_a, "ip_b": ip_b, "mask_or_cidr": mask_or_cidr},
        )

    def validate_ips(self, values: list[str], mask_or_cidr: str | None = None) -> list[dict[str, Any]]:
        return self._request(
            "POST",
            "tools/network/validate-ips",
            json={"values": values, "mask_or_cidr": mask_or_cidr},
        )

    def commands(self, host: str, port: int | None = None) -> dict[str, list[str]]:
        return self._request("POST", "tools/network/commands", json={"host": host, "port": port})
