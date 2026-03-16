from __future__ import annotations
from pathlib import Path
from typing import Any
from hudu_magic.payloads import clean_payload
from .endpoints import HuduEndpoint
from .models import (
    Asset,
    Upload
)
from .validation import (
    validate_vlan_id,
    validate_vlan_id_ranges,
    validate_network_address,
    validate_ip_address,
    to_bool,
    validate_uploadable_type,
    validate_photo_file,
    validate_pubphoto_file
)


class BaseResource:
    endpoint: HuduEndpoint

    def __init__(self, client):
        self.client = client

    def list(self, **params) -> Any:
        return self.client.get(self.endpoint, params=params or None)

    def get(self, item_id=None, **params):
        if item_id is not None and params:
            raise ValueError(
                "Provide either item_id or query params, not both"
                )

        if item_id is None:
            return self.list(**params)

        path = self.endpoint.item_path(item_id)
        return self.client.get(path, paginate=False)

    def get_all(self, **params):
        return self.get(None, **params)

    def create(self, payload: dict[str, Any], **kwargs) -> Any:
        return self.client.create(self.endpoint, payload, **kwargs)

    def update(self, item_id: int | str,
               payload: dict[str, Any], **kwargs) -> Any:
        return self.client.update(self.endpoint, item_id, payload, **kwargs)

    def delete(self, item_id: int | str) -> Any:
        path = self.client.resolve_path(self.endpoint, item_id)
        return self.client.delete(path)

    def new(self, payload: dict, **kwargs):
        return self.create(payload, **kwargs)


class CompaniesResource(BaseResource):
    endpoint = HuduEndpoint.COMPANIES


class PhotosResource(BaseResource):
    endpoint = HuduEndpoint.PHOTOS

    def create(
        self,
        file_path: str | Path,
        to_object: HuduObject,
    ) -> Any:
        file_path = Path(file_path)
        
        validate_pubphoto_file(file_path)
        photoable_type = to_object.to_upload_ref()

        with file_path.open("rb") as fh:
            result = self.client.post(
                self.endpoint,
                files={"file": (file_path.name, fh)},
                data={
                    "upload[photoable_id]": str(to_object.id),
                    "upload[photoable_type]": photoable_type,
                },
            )

        if isinstance(result, dict):
            result = self.client._extract_primary_object(result)
            return Upload(self.client, self.endpoint, result)

        return result

    def download(self, photo_or_id, out_dir: str | Path = ".") -> Path:
        if hasattr(photo_or_id, "download"):
            return photo_or_id.download(out_dir)

        photo = self.get(photo_or_id)
        return photo.download(out_dir)


class PublicPhotosResource(BaseResource):
    endpoint = HuduEndpoint.PUBLIC_PHOTOS

    def create(
        self,
        file_path: str | Path,
        to_object: HuduObject,
    ) -> Any:
        file_path = Path(file_path)
        
        validate_pubphoto_file(file_path)
        
        photoable_type = to_object.to_pubphoto_ref()

        with file_path.open("rb") as fh:
            result = self.client.post(
                self.endpoint,
                files={"file": (file_path.name, fh)},
                data={
                    "upload[photoable_id]": str(to_object.id),
                    "upload[photoable_type]": photoable_type,
                },
            )

        if isinstance(result, dict):
            result = self.client._extract_primary_object(result)
            return Upload(self.client, self.endpoint, result)

        return result

    def download(self, photo_or_id, out_dir: str | Path = ".") -> Path:
        if hasattr(photo_or_id, "download"):
            return photo_or_id.download(out_dir)

        photo = self.get(photo_or_id)
        return photo.download(out_dir)


class UploadsResource(BaseResource):
    endpoint = HuduEndpoint.UPLOADS

    def create(
        self,
        file_path: str | Path,
        to_object: HuduObject,
    ) -> Any:
        file_path = Path(file_path)
        
        if not file_path.is_file():
            raise FileNotFoundError(f"File not found: {file_path}")
        uploadable_type = to_object.to_upload_ref()
        if not uploadable_type or \
                validate_uploadable_type(uploadable_type) is False:
            raise ValueError(
                f"object is not of uploadable type {uploadable_type}"
            )

        with file_path.open("rb") as fh:
            result = self.client.post(
                self.endpoint,
                files={"file": (file_path.name, fh)},
                data={
                    "upload[uploadable_id]": str(to_object.id),
                    "upload[uploadable_type]": uploadable_type,
                },
            )

        if isinstance(result, dict):
            result = self.client._extract_primary_object(result)
            return Upload(self.client, self.endpoint, result)

        return result

    def download(self, upload_or_id, out_dir: str | Path = ".") -> Path:
        if hasattr(upload_or_id, "download"):
            return upload_or_id.download(out_dir)

        upload = self.get(upload_or_id)
        return upload.download(out_dir)


class ArticlesResource(BaseResource):
    endpoint = HuduEndpoint.ARTICLES


class FoldersResource(BaseResource):
    endpoint = HuduEndpoint.FOLDERS


class RackStoragesResource(BaseResource):
    endpoint = HuduEndpoint.RACK_STORAGES


class AssetPasswordsResource(BaseResource):
    endpoint = HuduEndpoint.ASSET_PASSWORDS


class WebsitesResource(BaseResource):
    endpoint = HuduEndpoint.WEBSITES


class AssetLayoutsResource(BaseResource):
    endpoint = HuduEndpoint.ASSET_LAYOUTS


class PasswordFoldersResource(BaseResource):
    endpoint = HuduEndpoint.PASSWORD_FOLDERS
    def save(self, item_id: int | str, payload: dict[str, Any],
             **kwargs) -> Any:
        company_id = payload.get("company_id")
        if not company_id:
            raise ValueError(
                "company_id is required in payload to update a password folder"
                )
        path = f"companies/{company_id}/password_folders/{item_id}"
        if payload.security is None:
            payload["security"] = "all_users"
        wrapped_payload = {"password_folder": payload}
        return self.client.update(self.endpoint, item_id,
                                  wrapped_payload, **kwargs)


class AssetsResource(BaseResource):
    endpoint = HuduEndpoint.ASSETS

    def create(self, company_id: int | str, payload: dict[str, Any],
               **kwargs) -> Any:
        wrapped = {"asset": payload}
        result = self.client.post(f"companies/{company_id}/assets",
                                  json=wrapped)

        if isinstance(result, dict):
            result = self.client._extract_primary_object(result)
            return Asset(self.client, HuduEndpoint.ASSETS, result)

        return result

    def list_for_company(self, company_id: int | str, **params) -> Any:
        path = f"companies/{company_id}/assets"
        return self.client.get(path, params=params or None, paginate=False)


class NetworksResource(BaseResource):
    endpoint = HuduEndpoint.NETWORKS

    def create(self, payload: dict, **kwargs):
        validate_network_address(str(payload.get("address", None)))

        return self.client.create(self.endpoint, payload, **kwargs)


class IPAddressesResource(BaseResource):
    endpoint = HuduEndpoint.IP_ADDRESSES

    def create(self, payload: dict, **kwargs):
        validate_ip_address(str(payload.get("address", None)))

        return self.client.create(self.endpoint, payload, **kwargs)


class VlansResource(BaseResource):
    endpoint = HuduEndpoint.VLANS

    def create(self, payload: dict, **kwargs):
        try:
            vlanid = int(str(payload.get("vlan_id")))
        except ValueError:
            raise ValueError("vlan_id must be an integer")
        validate_vlan_id(vlanid)

        payload["archived"] = to_bool(
                f"{payload.get("archived")}",
                default=False
            )

        return self.client.create(self.endpoint, payload, **kwargs)


class VLANZonesResource(BaseResource):
    endpoint = HuduEndpoint.VLAN_ZONES

    def create(self, payload: dict, **kwargs):
        validate_vlan_id_ranges(
            str(payload.get("vlan_id_ranges")))

        payload["archived"] = to_bool(
            f"{payload.get("archived")}", default=False)

        return self.client.create(self.endpoint, payload, **kwargs)


class RelationsResource(BaseResource):
    endpoint = HuduEndpoint.RELATIONS

    def create(
        self,
        from_obj: HuduObject,
        to_obj: HuduObject,
        description: str | None = None,
        is_inverse: bool = False,
        **kwargs,
    ):
        from_ref = from_obj.to_relation_ref()
        to_ref = to_obj.to_relation_ref()

        payload = {
            "fromable_id": from_ref["id"],
            "fromable_type": from_ref["type"],
            "toable_id": to_ref["id"],
            "toable_type": to_ref["type"],
            "is_inverse": is_inverse,
        }

        if description is not None:
            payload["description"] = description

        return self.client.create(self.endpoint, payload, **kwargs)
