from hudu_magic.client import HuduClient
from hudu_magic.endpoints import HuduEndpoint
from hudu_magic.models import HuduCollection, Procedure, ProcedureTasks
from hudu_magic.payloads import maybe_wrap_payload


def test_wrap_procedure_prefers_nested_procedure_body():
    client = HuduClient(api_key="x", instance_url="https://example.hudu.app")
    raw = {
        "id": 9,
        "procedure_tasks": [{"id": 1, "name": "Task A", "procedure_id": 9}],
        "procedure": {
            "id": 9,
            "name": "myprocedure",
            "description": "d",
            "company_id": 1,
        },
    }
    p = client._wrap_result(HuduEndpoint.PROCEDURES, raw)
    assert isinstance(p, Procedure)
    assert p.name == "myprocedure"
    assert isinstance(p.procedure_tasks, HuduCollection)
    assert isinstance(p.procedure_tasks[0], ProcedureTasks)


def test_wrap_procedure_by_id_registered_in_model_map():
    client = HuduClient(api_key="x", instance_url="https://example.hudu.app")
    raw = {"procedure": {"id": 5, "name": "G"}, "procedure_tasks": []}
    p = client._wrap_result(HuduEndpoint.PROCEDURES_ID, raw)
    assert isinstance(p, Procedure)
    assert p.name == "G"
    assert isinstance(p.procedure_tasks, HuduCollection)
    assert len(p.procedure_tasks) == 0


def test_procedure_create_payload_is_flat_not_wrapped():
    body = maybe_wrap_payload(
        HuduEndpoint.PROCEDURES,
        {"name": "Onboarding", "description": "x", "company_id": 1},
    )
    assert body == {"name": "Onboarding", "description": "x", "company_id": 1}
    assert "procedure" not in body


def test_procedure_tasks_default_to_empty_collection():
    client = HuduClient(api_key="x", instance_url="https://example.hudu.app")
    p = Procedure(client, HuduEndpoint.PROCEDURES, {"id": 1, "name": "n"})
    assert isinstance(p.procedure_tasks, HuduCollection)
    assert len(p.procedure_tasks) == 0
