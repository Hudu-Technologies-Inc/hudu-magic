"""Request body shaping for the Hudu API."""

from hudu_magic.endpoints import HuduEndpoint
from hudu_magic.payloads import maybe_wrap_payload


def test_maybe_wrap_procedures_create_is_flat():
    """Hudu 2.39.6+ expects flat JSON for procedures create/update, not a ``procedure`` root."""
    payload = {"name": "Test", "company_id": 1}
    assert maybe_wrap_payload(HuduEndpoint.PROCEDURES, payload) == payload


def test_maybe_wrap_procedures_id_update_is_flat():
    payload = {"name": "Renamed"}
    assert maybe_wrap_payload(HuduEndpoint.PROCEDURES_ID, payload) == payload


def test_maybe_wrap_procedure_tasks_still_nested():
    payload = {"name": "Step", "procedure_id": 1}
    assert maybe_wrap_payload(HuduEndpoint.PROCEDURE_TASKS, payload) == {
        "procedure_task": payload,
    }


def test_maybe_wrap_exports_create_nested():
    payload = {
        "format": "pdf",
        "company_id": 1,
        "include_passwords": True,
        "include_websites": True,
    }
    assert maybe_wrap_payload(HuduEndpoint.EXPORTS, payload) == {"export": payload}


def test_maybe_wrap_exports_idempotent_when_already_wrapped():
    payload = {"export": {"format": "csv", "company_id": 2}}
    assert maybe_wrap_payload(HuduEndpoint.EXPORTS, payload) == payload
