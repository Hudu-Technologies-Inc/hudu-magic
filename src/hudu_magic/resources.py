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
        if item_id is None:
            return self.list(**params)

        path = self.endpoint.item_path(item_id)
        return self.client.get(path, paginate=False)

    def create(self, payload: dict[str, Any], **kwargs) -> Any:
        return self.client.create(self.endpoint, payload, **kwargs)

    def update(self, item_id: int | str, payload: dict[str, Any], **kwargs) -> Any:
        return self.client.update(self.endpoint, item_id, payload, **kwargs)

    def delete(self, item_id: int | str) -> Any:
        path = self.client.resolve_path(self.endpoint, item_id)
        return self.client.delete(path)


class CompaniesResource(BaseResource):
    endpoint = HuduEndpoint.COMPANIES


class ArticlesResource(BaseResource):
    endpoint = HuduEndpoint.ARTICLES


class FoldersResource(BaseResource):
    endpoint = HuduEndpoint.FOLDERS


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