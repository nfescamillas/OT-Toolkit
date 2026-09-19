import pytest
from fastapi.testclient import TestClient


def test_seeded_reference_and_search_routes(api_client: TestClient):
    technologies = api_client.get("/api/v1/technologies")
    assert technologies.status_code == 200
    assert len(technologies.json()) == 28
    assert api_client.get("/api/v1/technologies/rs485").json()["classification"] == "Physical / Electrical Interface"
    assert api_client.get("/api/v1/technologies/missing").status_code == 404
    assert api_client.get("/api/v1/search", params={"q": "GSDML"}).json()[0]["id"] == "profinet"
    assert api_client.get("/api/v1/ports", params={"q": "502"}).json()[0]["name"] == "Modbus TCP"
    assert len(api_client.get("/api/v1/glossary").json()) == 111


def test_hierarchy_and_comparison_routes(api_client: TestClient):
    hierarchy = api_client.get("/api/v1/technologies/canopen/hierarchy")
    assert hierarchy.status_code == 200
    assert [item["id"] for item in hierarchy.json()["runs_over"]] == ["can"]

    comparison = api_client.post(
        "/api/v1/comparisons",
        json={"left_id": "profinet", "right_id": "ethernet-ip"},
    )
    assert comparison.status_code == 200
    assert comparison.json()["left"]["name"] == "PROFINET"
    assert any(row["label"] == "Configuration files" for row in comparison.json()["rows"])


@pytest.mark.parametrize(
    ("path", "payload", "assertion"),
    [
        ("/api/v1/tools/numbers/convert", {"value": "16#8401", "numeric_format": "UInt16"}, lambda body: body["hex"] == "8401"),
        ("/api/v1/tools/ieee754/encode", {"value": 123.0, "precision": 32}, lambda body: body["hex"] == "42F60000"),
        ("/api/v1/tools/endianness/decode", {"hex": "12 34 56 78"}, lambda body: body["DCBA"]["hex"] == "78563412"),
        ("/api/v1/tools/modbus/address", {"reference": "40001"}, lambda body: body["zero_based_offset"] == 0),
        ("/api/v1/tools/modbus/registers/decode", {"registers": [17142, 0]}, lambda body: body["ABCD"]["float32"] == 123.0),
        ("/api/v1/tools/modbus/crc", {"hex": "01 03 00 00 00 02"}, lambda body: body["transmission_order"] == "C4 0B"),
        ("/api/v1/tools/modbus/frame/decode", {"hex": "01 03 00 00 00 02 C4 0B"}, lambda body: body["crc_valid"] is True),
        ("/api/v1/tools/network/subnet", {"ip": "192.168.1.20", "mask_or_cidr": "24"}, lambda body: body["network"] == "192.168.1.0"),
        ("/api/v1/tools/network/same-subnet", {"ip_a": "10.0.0.1", "ip_b": "10.0.0.2", "mask_or_cidr": "24"}, lambda body: body["same"] is True),
        ("/api/v1/tools/network/validate-ips", {"values": ["10.0.0.1", "bad"]}, lambda body: body[1]["valid"] is False),
        ("/api/v1/tools/network/commands", {"host": "192.168.1.20", "port": 502}, lambda body: body["windows"][-1].endswith("-Port 502")),
    ],
)
def test_calculation_routes(api_client: TestClient, path, payload, assertion):
    response = api_client.post(path, json=payload)
    assert response.status_code == 200, response.text
    assert assertion(response.json())


def test_invalid_calculator_input_returns_documented_error(api_client: TestClient):
    response = api_client.post(
        "/api/v1/tools/numbers/convert",
        json={"value": "256", "numeric_format": "UInt8"},
    )
    assert response.status_code == 400
    assert response.json()["code"] == "invalid_input"


def test_fastapi_schema_exposes_bearer_only_for_favorites(api_client: TestClient):
    schema = api_client.get("/api/v1/openapi.json").json()
    assert "bearerAuth" in schema["components"]["securitySchemes"]
    assert schema["paths"]["/api/v1/favorites"]["get"]["security"] == [{"bearerAuth": []}]
    assert schema["paths"]["/api/v1/technologies"]["get"].get("security") in (None, [])


def test_backend_serves_built_frontend_without_shadowing_api(api_store, tmp_path):
    from ot_toolkit_backend.api.main import create_app

    static_dir = tmp_path / "static"
    static_dir.mkdir()
    (static_dir / "index.html").write_text("<h1>OT Toolkit Web</h1>", encoding="utf-8")
    (static_dir / "app.js").write_text("console.log('ot-toolkit')", encoding="utf-8")

    with TestClient(create_app(api_store, static_dir=static_dir)) as client:
        assert "OT Toolkit Web" in client.get("/").text
        assert "ot-toolkit" in client.get("/app.js").text
        assert len(client.get("/api/v1/technologies").json()) == 28


def test_explicit_missing_frontend_build_fails_fast(api_store, tmp_path):
    from ot_toolkit_backend.api.main import create_app

    with pytest.raises(RuntimeError, match="Frontend build not found"):
        create_app(api_store, static_dir=tmp_path / "missing")
    api_store.close()
