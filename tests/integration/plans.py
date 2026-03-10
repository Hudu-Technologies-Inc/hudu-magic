from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from hudu_magic.endpoints import HuduEndpoint
from .factories import (
    company_payload,
    company_update_payload,
    article_payload,
    article_update_payload,
    folder_payload,
    folder_update_payload,
    website_payload,
    website_update_payload,
    asset_layout_payload,
    asset_layout_update_payload,
)


CreateFactory = Callable[[dict[str, Any]], dict[str, Any]]
UpdateFactory = Callable[[dict[str, Any]], dict[str, Any]]
CleanupHook = Callable[[Any, dict[str, Any]], None]


@dataclass(frozen=True)
class LifecyclePlan:
    name: str
    create_endpoint: HuduEndpoint
    update_endpoint: HuduEndpoint
    delete_endpoint: HuduEndpoint
    create_payload: CreateFactory
    update_payload: UpdateFactory
    assert_updated_field: str
    assert_updated_value: Any
    validate_create: bool = True
    validate_update: bool = True
    cleanup_hook: CleanupHook | None = None



def company_create(ctx: dict[str, Any]) -> dict[str, Any]:
    return company_payload()


def company_update(ctx: dict[str, Any]) -> dict[str, Any]:
    return company_update_payload()


def article_create(ctx: dict[str, Any]) -> dict[str, Any]:
    return article_payload()


def article_update(ctx: dict[str, Any]) -> dict[str, Any]:
    return article_update_payload()


def folder_create(ctx: dict[str, Any]) -> dict[str, Any]:
    return folder_payload()


def folder_update(ctx: dict[str, Any]) -> dict[str, Any]:
    return folder_update_payload()


def asset_layout_create(ctx: dict[str, Any]) -> dict[str, Any]:
    return asset_layout_payload()


def asset_layout_update(ctx: dict[str, Any]) -> dict[str, Any]:
    created = ctx["created"]
    layout = created.get("asset_layout", created)

    return {
        "name": layout.get("name"),
        "icon": "fas fa-network-wired",
        "color": "#228B22",
        "icon_color": layout.get("icon_color", "#FFFFFF"),
        "fields": layout.get("fields", []),
        "include_passwords": layout.get("include_passwords", False),
        "include_photos": layout.get("include_photos", False),
        "include_comments": layout.get("include_comments", False),
        "include_files": layout.get("include_files", False),
    }


def website_create(ctx: dict[str, Any]) -> dict[str, Any]:
    company = ctx["client"].create(HuduEndpoint.COMPANIES, company_payload())
    company_id = ctx["extract_id"](company)
    ctx["company_id"] = company_id
    return website_payload(company_id)


def website_update(ctx: dict[str, Any]) -> dict[str, Any]:
    return website_update_payload()


def website_cleanup(client, ctx: dict[str, Any]) -> None:
    company_id = ctx.get("company_id")
    if company_id:
        try:
            client.delete(HuduEndpoint.COMPANIES.item_path(company_id))
        except Exception:
            pass


LIFECYCLE_PLANS = [
    LifecyclePlan(
        name="companies",
        create_endpoint=HuduEndpoint.COMPANIES,
        update_endpoint=HuduEndpoint.COMPANIES_ID,
        delete_endpoint=HuduEndpoint.COMPANIES_ID,
        create_payload=company_create,
        update_payload=company_update,
        assert_updated_field="notes",
        assert_updated_value="Updated by integration test",
    ),
    LifecyclePlan(
        name="articles",
        create_endpoint=HuduEndpoint.ARTICLES,
        update_endpoint=HuduEndpoint.ARTICLES_ID,
        delete_endpoint=HuduEndpoint.ARTICLES_ID,        
        create_payload=article_create,
        update_payload=article_update,
        assert_updated_field="content",
        assert_updated_value="<p>Updated from integration test</p>",
        validate_create=True,
        validate_update=True        
    ),
    LifecyclePlan(
        name="folders",
        create_endpoint=HuduEndpoint.FOLDERS,
        update_endpoint=HuduEndpoint.FOLDERS_ID,
        delete_endpoint=HuduEndpoint.FOLDERS_ID,
        create_payload=folder_create,
        update_payload=folder_update,
        assert_updated_field="description",
        assert_updated_value="Updated by integration test",
        validate_create=True,
        validate_update=True        
    ),
    LifecyclePlan(
        name="asset_layouts",
        create_endpoint=HuduEndpoint.ASSET_LAYOUTS,
        update_endpoint=HuduEndpoint.ASSET_LAYOUTS_ID,
        delete_endpoint=HuduEndpoint.ASSET_LAYOUTS_ID,
        create_payload=asset_layout_create,
        update_payload=asset_layout_update,
        assert_updated_field="icon",
        assert_updated_value="fas fa-network-wired",
        validate_create=True,
        validate_update=True
    ),
    LifecyclePlan(
        name="websites",
        create_endpoint=HuduEndpoint.WEBSITES,
        update_endpoint=HuduEndpoint.WEBSITES_ID,
        delete_endpoint=HuduEndpoint.WEBSITES_ID,        
        create_payload=website_create,
        update_payload=website_update,
        assert_updated_field="paused",
        assert_updated_value=True,
        cleanup_hook=website_cleanup,
        validate_create=True,
        validate_update=True        
    ),
]