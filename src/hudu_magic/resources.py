from __future__ import annotations

from typing import Any

from .endpoints import HuduEndpoint
from .models import Asset, Company, Article, Folder, Website, AssetLayout

class BaseResource:
    endpoint: HuduEndpoint

    def __init__(self, client):
        self.client = client

    def list(self, **params) -> Any:
        return self.client.get(self.endpoint, params=params or None)

    def get(self, item_id=None, **params):
        if item_id is not None and params:
            raise ValueError("Provide either item_id or query params, not both")

        if item_id is None:
            return self.list(**params)

        path = self.endpoint.item_path(item_id)
        return self.client.get(path, paginate=False)

    def get_all(self, **params):
        return self.get(None, **params)

    def create(self, payload: dict[str, Any], **kwargs) -> Any:
        return self.client.create(self.endpoint, payload, **kwargs)

    def update(self, item_id: int | str, payload: dict[str, Any], **kwargs) -> Any:
        return self.client.update(self.endpoint, item_id, payload, **kwargs)

    def delete(self, item_id: int | str) -> Any:
        path = self.client.resolve_path(self.endpoint, item_id)
        return self.client.delete(path)

    def new(self, payload: dict, **kwargs):
        return self.create(payload, **kwargs)


class CompaniesResource(BaseResource):
    endpoint = HuduEndpoint.COMPANIES


class ArticlesResource(BaseResource):
    endpoint = HuduEndpoint.ARTICLES


class FoldersResource(BaseResource):
    endpoint = HuduEndpoint.FOLDERS

class AssetPasswordsResource(BaseResource):
    endpoint = HuduEndpoint.ASSET_PASSWORDS
    def save(self, item_id: int | str, payload: dict[str, Any], **kwargs) -> Any:
        path = self.client.resolve_path(self.endpoint, item_id)
        wrapped_payload = {"asset_password": payload}
        result = self.client.put(path, json=wrapped_payload)
        return self.client._wrap_result(self.endpoint, result)
    
    def update(self, item_id: int | str, payload: dict[str, Any], **kwargs) -> Any:
        payload = normalize_password_payload_for_save(payload)
        return self.save(item_id, payload, **kwargs)

class WebsitesResource(BaseResource):
    endpoint = HuduEndpoint.WEBSITES


class AssetLayoutsResource(BaseResource):
    endpoint = HuduEndpoint.ASSET_LAYOUTS


class AssetsResource(BaseResource):
    endpoint = HuduEndpoint.ASSETS

    def create(self, company_id: int | str, payload: dict[str, Any], **kwargs) -> Any:
        wrapped = {"asset": payload}
        result = self.client.post(f"companies/{company_id}/assets", json=wrapped)

        if isinstance(result, dict):
            result = self.client._extract_primary_object(result)
            return Asset(self.client, HuduEndpoint.ASSETS, result)

        return result

    def list_for_company(self, company_id: int | str, **params) -> Any:
        path = f"companies/{company_id}/assets"
        return self.client.get(path, params=params or None, paginate=False)