"""BaseResource helpers."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from hudu_magic.endpoints import HuduEndpoint
from hudu_magic.models import Article, Asset
from hudu_magic.resources import (
    ArticlesResource,
    ExportsResource,
    ProcedureTasksResource,
    RelationsResource,
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
    client.asset_layouts.list = MagicMock(return_value=[])
    res = ExportsResource(client)

    res.start({"format": "csv", "company_id": 1, "include_passwords": False, "include_websites": True})

    client.create.assert_called_once_with(
        HuduEndpoint.EXPORTS,
        {
            "format": "csv",
            "company_id": 1,
            "include_passwords": False,
            "include_websites": True,
            "include_articles": True,
            "include_archived_articles": True,
            "include_archived_passwords": True,
            "include_archived_websites": True,
            "include_archived_assets": True,
        },
    )


def test_exports_start_populates_asset_layout_ids_when_missing():
    client = MagicMock()
    client.create = MagicMock(return_value={"id": 1})
    layout_a = MagicMock()
    layout_a.id = 3
    layout_b = MagicMock()
    layout_b.id = 7
    client.asset_layouts.list = MagicMock(return_value=[layout_a, layout_b])
    res = ExportsResource(client)

    res.start({"format": "pdf", "company_id": 2})

    client.create.assert_called_once_with(
        HuduEndpoint.EXPORTS,
        {
            "format": "pdf",
            "company_id": 2,
            "include_passwords": True,
            "include_websites": True,
            "include_articles": True,
            "include_archived_articles": True,
            "include_archived_passwords": True,
            "include_archived_websites": True,
            "include_archived_assets": True,
            "asset_layout_ids": [3, 7],
        },
    )


def test_exports_start_respects_explicit_asset_layout_ids():
    client = MagicMock()
    client.create = MagicMock(return_value={"id": 1})
    client.asset_layouts.list = MagicMock()
    res = ExportsResource(client)

    res.start({"format": "csv", "company_id": 1, "asset_layout_ids": [9]})

    client.asset_layouts.list.assert_not_called()
    assert client.create.call_args[0][1]["asset_layout_ids"] == [9]


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
    download_response = MagicMock()
    download_response.content = b"pdf-bytes"
    download_response.raise_for_status = MagicMock()
    client.get_url = MagicMock(return_value=download_response)

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
    client.get_url.assert_called_once()
    args, kwargs = client.get_url.call_args
    assert args[0] == "https://cdn.example/x"
    assert kwargs["timeout"] == 30
    assert kwargs["allow_redirects"] is True


def test_exports_wait_until_downloadable():
    client = MagicMock()
    res = ExportsResource(client)

    pending = MagicMock()
    pending.to_dict.return_value = {
        "id": 7,
        "status": "processing",
        "download_url": None,
    }
    ready = MagicMock()
    ready.to_dict.return_value = {
        "id": 7,
        "status": "complete",
        "download_url": "https://cdn.example/file.pdf",
    }

    res.get = MagicMock(side_effect=[pending, ready])

    out = res.wait_until_downloadable(7, interval=0.01, timeout=5)
    assert out is ready
    assert res.get.call_count == 2


def test_exports_wait_until_downloadable_timeout():
    client = MagicMock()
    res = ExportsResource(client)
    pending = MagicMock()
    pending.to_dict.return_value = {"id": 1, "status": "pending", "download_url": None}
    res.get = MagicMock(return_value=pending)

    with pytest.raises(TimeoutError):
        res.wait_until_downloadable(1, interval=0.01, timeout=0.05)


def test_exports_wait_until_downloadable_failed_status():
    client = MagicMock()
    res = ExportsResource(client)
    failed = MagicMock()
    failed.to_dict.return_value = {"id": 2, "status": "failed", "download_url": None}
    res.get = MagicMock(return_value=failed)

    with pytest.raises(RuntimeError, match="ended with status"):
        res.wait_until_downloadable(2, interval=0.01, timeout=5)


def test_exports_download_without_download_url_builds_api_path(tmp_path: Path):
    client = MagicMock()
    client.timeout = 15
    client.build_url = MagicMock(return_value="https://hudu/api/v1/exports/3?download=true")
    download_response = MagicMock()
    download_response.content = b"csv-data"
    download_response.raise_for_status = MagicMock()
    client.get_url = MagicMock(return_value=download_response)

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
    res.get = MagicMock(return_value=export)
    out = res.download(export, tmp_path)

    assert out.name == "export-3.csv"
    assert out.read_bytes() == b"csv-data"
    client.build_url.assert_called_once_with("exports/3?download=true")
    client.get_url.assert_called_once_with(
        "https://hudu/api/v1/exports/3?download=true",
        timeout=15,
        allow_redirects=True,
    )


def test_relations_list_relations_uses_from_and_to_filters():
    client = MagicMock()
    as_from = MagicMock()
    as_from.id = 1
    as_from.fromable_type = "Asset"
    as_from.fromable_id = 10
    as_from.toable_type = "Website"
    as_from.toable_id = 20

    as_to = MagicMock()
    as_to.id = 2
    as_to.fromable_type = "Article"
    as_to.fromable_id = 5
    as_to.toable_type = "Asset"
    as_to.toable_id = 10

    duplicate = MagicMock()
    duplicate.id = 1
    duplicate.fromable_type = "Asset"
    duplicate.fromable_id = 10
    duplicate.toable_type = "Website"
    duplicate.toable_id = 20

    res = RelationsResource(client)
    res.list = MagicMock(side_effect=[[as_from], [as_to, duplicate]])

    asset = Asset(client, HuduEndpoint.ASSETS, {"id": 10})
    results = res.list_relations(asset)

    assert [r.id for r in results] == [1, 2]
    assert res.list.call_count == 2
    first_kwargs = res.list.call_args_list[0].kwargs
    second_kwargs = res.list.call_args_list[1].kwargs
    assert first_kwargs == {"fromable_type": "Asset", "fromable_id": 10}
    assert second_kwargs == {"toable_type": "Asset", "toable_id": 10}


def test_base_resource_list_relations_delegates_to_relations_resource():
    client = MagicMock()
    client.relations.list_relations = MagicMock(return_value=[])
    article = Article(client, HuduEndpoint.ARTICLES, {"id": 3})
    res = ArticlesResource(client)

    res.list_relations(article, page_size=50)

    client.relations.list_relations.assert_called_once_with(article, page_size=50)


def test_huduobject_list_relations_delegates_to_relations_resource():
    client = MagicMock()
    client.relations.list_relations = MagicMock(return_value=["ok"])
    article = Article(client, HuduEndpoint.ARTICLES, {"id": 3})

    assert article.list_relations() == ["ok"]
    client.relations.list_relations.assert_called_once_with(to_object=article)
