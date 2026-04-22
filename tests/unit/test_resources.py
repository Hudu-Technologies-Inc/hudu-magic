"""BaseResource helpers."""

from pathlib import Path
from unittest.mock import MagicMock

from hudu_magic.endpoints import HuduEndpoint
from hudu_magic.resources import (
    ExportsResource,
    ProcedureTasksResource,
    S3ExportsResource,
)


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


def test_exports_start_delegates_to_create():
    client = MagicMock()
    client.create = MagicMock(return_value={"id": 1})
    res = ExportsResource(client)

    res.start({"format": "csv", "company_id": 1, "include_passwords": False, "include_websites": True})

    client.create.assert_called_once_with(
        HuduEndpoint.EXPORTS,
        {
            "format": "csv",
            "company_id": 1,
            "include_passwords": False,
            "include_websites": True,
        },
    )


def test_s3_exports_start_delegates_to_create():
    client = MagicMock()
    client.create = MagicMock(return_value={"id": 9})
    res = S3ExportsResource(client)

    res.start({"company_id": 2})

    client.create.assert_called_once_with(
        HuduEndpoint.S3_EXPORTS,
        {"company_id": 2},
    )


def test_exports_download_uses_download_url_when_present(tmp_path: Path):
    client = MagicMock()
    client.timeout = 30
    client.session = MagicMock()
    client.session.get = MagicMock()
    client.session.get.return_value.content = b"pdf-bytes"
    client.session.get.return_value.raise_for_status = MagicMock()

    export = MagicMock()
    export.id = 5
    export.get = MagicMock(
        side_effect=lambda k, d=None: {
            "file_name": "co.pdf",
            "is_pdf": True,
            "download_url": "https://cdn.example/x",
        }.get(k, d)
    )

    res = ExportsResource(client)
    out = res.download(export, tmp_path)

    assert out.read_bytes() == b"pdf-bytes"
    client.session.get.assert_called_once()
    args, kwargs = client.session.get.call_args
    assert args[0] == "https://cdn.example/x"
    assert kwargs["timeout"] == 30
    assert kwargs["allow_redirects"] is True


def test_exports_download_without_download_url_builds_api_path(tmp_path: Path):
    client = MagicMock()
    client.timeout = 15
    client.build_url = MagicMock(return_value="https://hudu/api/v1/exports/3?download=true")
    client.session = MagicMock()
    client.session.get = MagicMock()
    client.session.get.return_value.content = b"csv-data"
    client.session.get.return_value.raise_for_status = MagicMock()

    export = MagicMock()
    export.id = 3
    export.get = MagicMock(
        side_effect=lambda k, d=None: {
            "file_name": None,
            "is_pdf": False,
            "download_url": None,
        }.get(k, d)
    )

    res = ExportsResource(client)
    out = res.download(export, tmp_path)

    assert out.name == "export-3.csv"
    assert out.read_bytes() == b"csv-data"
    client.build_url.assert_called_once_with("exports/3?download=true")
    client.session.get.assert_called_once_with(
        "https://hudu/api/v1/exports/3?download=true",
        timeout=15,
        allow_redirects=True,
    )
