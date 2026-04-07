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


def test_procedure_task_create_payload_is_flat_not_wrapped():
    body = maybe_wrap_payload(
        HuduEndpoint.PROCEDURE_TASKS,
        {"name": "x", "procedure_id": 1},
    )
    assert body == {"name": "x", "procedure_id": 1}
    assert "procedure_task" not in body


def test_procedure_tasks_property_alias():
    client = HuduClient(api_key="x", instance_url="https://example.hudu.app")
    p = Procedure(client, HuduEndpoint.PROCEDURES, {"id": 1, "name": "n"})
    assert p.tasks is p.procedure_tasks


def test_procedure_add_task_forwards_procedure_id():
    from unittest.mock import MagicMock

    client = MagicMock()
    fake_task = ProcedureTasks(
        client, HuduEndpoint.PROCEDURE_TASKS, {"id": 99, "name": "t", "procedure_id": 1}
    )
    client.procedure_tasks.create.return_value = fake_task

    p = Procedure(client, HuduEndpoint.PROCEDURES, {"id": 1, "name": "proc"})
    out = p.add_task(name="Step one", for_run=True)

    client.procedure_tasks.create.assert_called_once_with(
        None, procedure_id=1, name="Step one", for_run=True
    )
    assert out is fake_task
    assert len(p.procedure_tasks) == 1


def test_procedure_task_create_requires_procedure_id_and_name():
    from unittest.mock import MagicMock

    from hudu_magic.resources import ProcedureTasksResource

    r = ProcedureTasksResource(MagicMock())
    try:
        r.create(name="only name")
    except ValueError as e:
        assert "procedure_id" in str(e).lower()
    else:
        raise AssertionError("expected ValueError")

    try:
        r.create(procedure_id=1)
    except ValueError as e:
        assert "name" in str(e).lower()
    else:
        raise AssertionError("expected ValueError")


def test_procedure_task_create_strips_run_only_fields_for_template():
    from unittest.mock import MagicMock

    from hudu_magic.resources import ProcedureTasksResource

    client = MagicMock()
    client.procedures.get.return_value = Procedure(
        client,
        HuduEndpoint.PROCEDURES,
        {"id": 10, "name": "T", "company_template": True},
    )
    inner = MagicMock(return_value=object())
    client.create = inner

    r = ProcedureTasksResource(client)
    r.create(name="job", procedure_id=10, priority="high", user_id=3)

    inner.assert_called_once()
    endpoint, body = inner.call_args[0][0], inner.call_args[0][1]
    assert endpoint == HuduEndpoint.PROCEDURE_TASKS
    assert body["name"] == "job"
    assert body["procedure_id"] == 10
    assert "priority" not in body
    assert "user_id" not in body


def test_procedure_task_create_keeps_run_fields_when_for_run_true():
    from unittest.mock import MagicMock

    from hudu_magic.resources import ProcedureTasksResource

    client = MagicMock()
    inner = MagicMock(return_value=object())
    client.create = inner

    r = ProcedureTasksResource(client)
    r.create(name="job", procedure_id=10, priority="high", for_run=True)

    client.procedures.get.assert_not_called()
    body = inner.call_args[0][1]
    assert body["priority"] == "high"


def test_hudu_collection_rejects_add_tasks():
    col = HuduCollection(
        [
            Procedure(
                HuduClient(api_key="x", instance_url="https://example.hudu.app"),
                HuduEndpoint.PROCEDURES,
                {"id": 1, "name": "a"},
            )
        ]
    )
    try:
        col.add_tasks(["x"])
    except TypeError as e:
        assert "Procedure" in str(e)
    else:
        raise AssertionError("expected TypeError")
