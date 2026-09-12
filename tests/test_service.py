import json


def test_reference_data_loads_and_relationships_are_resolved(service):
    technologies = service.list_technologies()
    assert len(technologies) >= 27
    assert {"Physical & Serial", "Industrial Ethernet", "Power"} <= set(service.list_categories())
    assert service.get_technology("rs485").classification == "Physical / Electrical Interface"
    hierarchy = service.hierarchy("canopen")
    assert [item.id for item in hierarchy["runs_over"]] == ["can"]


def test_port_lookup(service):
    assert service.list_ports("502")[0].name == "Modbus TCP"
    assert {item.name for item in service.list_ports("CIP")} == {"EtherNet/IP I/O", "EtherNet/IP"}


def test_global_search_across_sources(service):
    assert service.search("GSDML")[0].id == "profinet"
    assert any(item.title.startswith("44818") for item in service.search("44818"))
    assert any(item.title == "PDO" for item in service.search("PDO"))


def test_generic_comparison_engine(service):
    comparison = service.compare("profinet", "ethernet-ip")
    assert comparison.left.name == "PROFINET"
    assert comparison.right.name == "EtherNet/IP"
    rows = {label: (left, right) for label, left, right in comparison.rows}
    assert "GSDML" in rows["Configuration files"][0]
    assert "EDS" in rows["Configuration files"][1]


def test_glossary_schema_and_search(service):
    entries = service.list_glossary()
    assert len(entries) >= 30
    assert service.list_glossary("Object Identifier")[0].term == "OID"
    assert all(item.term and item.definition and item.category for item in entries)


def test_favorites_are_local_and_persistent(service):
    service.set_favorite("profinet", True)
    assert service.favorites() == {"profinet"}
    service.set_favorite("profinet", False)
    assert service.favorites() == set()


def test_service_calculators_reach_the_common_engine(service):
    assert service.number_conversion("255", "UInt8")["hex"] == "FF"
    assert service.modbus_crc("01 03 00 00 00 02")["transmission_order"] == "C4 0B"
    assert service.subnet("172.16.4.20", "255.255.255.0").network == "172.16.4.0"

