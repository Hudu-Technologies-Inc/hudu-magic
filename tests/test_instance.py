from hudu_magic.instance import Instance


def test_instance_normalizes_url():
    inst = Instance(api_key="abc123", instance_url="myinstance.hudu.app")
    assert inst.instance_url == "https://myinstance.hudu.app/api/v1"


def test_instance_keeps_existing_api_v1():
    inst = Instance(api_key="abc123", instance_url="https://myinstance.hudu.app/api/v1")
    assert inst.instance_url == "https://myinstance.hudu.app/api/v1"


def test_instance_builds_headers():
    inst = Instance(api_key="abc123", instance_url="myinstance.hudu.app")
    assert inst.get_request_headers["x-api-key"] == "abc123"
    assert inst.get_request_headers["Accept"] == "application/json"