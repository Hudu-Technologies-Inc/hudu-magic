from __future__ import annotations

from typing import Any

from hudu_magic.payloads import clean_payload

from .endpoints import HuduEndpoint
from .models import Asset, Company, Article, Folder, Website, AssetLayout, PasswordFolder, AssetPassword, Network, IpAddress, vlan, vlanzone

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

class WebsitesResource(BaseResource):
    endpoint = HuduEndpoint.WEBSITES

class AssetLayoutsResource(BaseResource):
    endpoint = HuduEndpoint.ASSET_LAYOUTS

class PasswordFoldersResource(BaseResource):
    endpoint = HuduEndpoint.PASSWORD_FOLDERS
    def save(self, item_id: int | str, payload: dict[str, Any], **kwargs) -> Any:
        company_id = payload.get("company_id")
        if not company_id:
            raise ValueError("company_id is required in payload to update a password folder")
        path = f"companies/{company_id}/password_folders/{item_id}"
        if payload.security is None:
            payload["security"] = "all_users"
        wrapped_payload = {"password_folder": payload}


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
    
    
class NetworkResource(BaseResource):
    endpoint = HuduEndpoint.NETWORKS
    
class IpAddressesResource(BaseResource):
    endpoint = HuduEndpoint.IP_ADDRESSES
    
class VlansResource(BaseResource):
    endpoint = HuduEndpoint.VLANS

class VlanZonesResource(BaseResource):
    endpoint = HuduEndpoint.VLAN_ZONES
