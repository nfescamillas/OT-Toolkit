from __future__ import annotations

import math

import httpx
import pytest
from fastapi.testclient import TestClient

from ot_toolkit_backend.api.main import create_app
from ot_toolkit_backend.services import (
    HttpToolkitService,
    ToolkitAuthenticationError,
    ToolkitConnectionError,
)


@pytest.fixture
def http_service():
    app = create_app()
    with TestClient(app, base_url="http://testserver/api/v1/") as client:
        yield HttpToolkitService(client=client), app


def test_reference_discovery_and_preferences_use_the_api(http_service):
    service, app = http_service

    assert len(service.list_technologies()) == 28
    assert service.list_technologies("Power")[0].category == "Power"
    assert service.get_technology("rs485").runs_over == ()
    assert "Industrial Ethernet" in service.list_categories()
    assert service.list_ports("502")[0].name == "Modbus TCP"
    assert service.list_glossary("Object Identifier")[0].term == "OID"
    assert "rs485" in service.list_troubleshooting()
    assert service.search("") == []
    assert service.search("GSDML")[0].id == "profinet"

    hierarchy = service.hierarchy("canopen")
    assert [item.id for item in hierarchy["runs_over"]] == ["can"]
    comparison = service.compare("profinet", "ethernet-ip")
    assert comparison.left.name == "PROFINET"
    assert any(row[0] == "Configuration files" for row in comparison.rows)

    assert service.favorites() == set()
    assert service._access_token in app.state.store._tokens
    first_token = service._access_token
    service.set_favorite("profinet", True)
    assert service.favorites() == {"profinet"}

    app.state.store._tokens.clear()
    assert service.favorites() == {"profinet"}
    assert service._access_token != first_token
    service.set_favorite("profinet", False)
    assert service.favorites() == set()


def test_all_calculator_methods_use_the_api(http_service):
    service, _ = http_service

    assert service.number_conversion("16#8401", "UInt16")["hex"] == "8401"
    assert service.ieee_to_hex(123.0, 32) == "42F60000"
    assert service.ieee_from_hex("42F60000", 32) == 123.0
    assert math.isinf(service.ieee_from_hex("7F800000", 32))
    assert service.endian_decode("12 34 56 78")["DCBA"]["hex"] == "78563412"

    assert service.modbus_address("40001")["zero_based_offset"] == 0
    assert service.modbus_registers([17142, 0])["ABCD"]["float32"] == 123.0
    assert service.modbus_crc("01 03 00 00 00 02")["transmission_order"] == "C4 0B"
    assert service.modbus_frame("01 03 00 00 00 02 C4 0B").crc_valid is True

    assert service.subnet("192.168.1.20", "24").network == "192.168.1.0"
    assert service.same_subnet("10.0.0.1", "10.0.0.2", "24")["same"] is True
    assert service.validate_ips(["10.0.0.1", "bad"])[1]["valid"] is False
    assert service.commands("192.168.1.20", 502)["windows"][-1].endswith("-Port 502")


def test_http_service_translates_documented_errors(http_service):
    service, _ = http_service

    with pytest.raises(KeyError, match="Unknown technology"):
        service.get_technology("missing")
    with pytest.raises(ValueError, match="between 0 and 255"):
        service.number_conversion("256", "UInt8")


def test_http_service_reports_bad_credentials():
    app = create_app()
    with TestClient(app, base_url="http://testserver/api/v1/") as client:
        service = HttpToolkitService(username="demo", password="wrong-password", client=client)
        with pytest.raises(ToolkitAuthenticationError, match="Incorrect username or password"):
            service.favorites()


def test_http_service_reports_connection_failures():
    def unavailable(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    client = httpx.Client(
        base_url="http://127.0.0.1:8000/api/v1/",
        transport=httpx.MockTransport(unavailable),
    )
    service = HttpToolkitService(client=client)
    with pytest.raises(ToolkitConnectionError, match="make api"):
        service.list_categories()
    client.close()


def test_http_service_reads_runtime_configuration(monkeypatch):
    monkeypatch.setenv("OT_TOOLKIT_API_URL", "http://localhost:9000/custom")
    monkeypatch.setenv("OT_TOOLKIT_USERNAME", "engineer")
    monkeypatch.setenv("OT_TOOLKIT_PASSWORD", "field-password")

    service = HttpToolkitService.from_environment()
    assert service.base_url == "http://localhost:9000/custom"
    assert service._username == "engineer"
    assert service._password == "field-password"
    service.close()
