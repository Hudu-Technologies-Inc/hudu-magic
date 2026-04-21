"""BaseResource helpers."""

from unittest.mock import MagicMock

from hudu_magic.endpoints import HuduEndpoint
from hudu_magic.resources import ProcedureTasksResource


def test_procedure_tasks_create_accepts_kwargs_only():
    client = MagicMock()
    client.create = MagicMock(return_value={"id": 1, "name": "t"})
    res = ProcedureTasksResource(client)

    res.create(name="newtask", procedure_id=99)

    client.create.assert_called_once()
    ep, payload = client.create.call_args[0]
    assert ep == HuduEndpoint.PROCEDURE_TASKS
    assert payload == {"name": "newtask", "procedure_id": 99}


def test_procedure_tasks_create_splits_validate_kwarg():
    client = MagicMock()
    client.create = MagicMock(return_value={})
    res = ProcedureTasksResource(client)

    res.create({"name": "a"}, procedure_id=1, validate=False)

    client.create.assert_called_once_with(
        HuduEndpoint.PROCEDURE_TASKS,
        {"name": "a", "procedure_id": 1},
        validate=False,
    )
