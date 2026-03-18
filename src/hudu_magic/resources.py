from __future__ import annotations

from pathlib import Path
from typing import Any, ClassVar

from hudu_magic.help import describe_single, supported_methods
from hudu_magic.helpers.general import is_version_greater_or_equal

from .endpoints import HuduEndpoint
from .models import Asset, HuduObject, Photo, PublicPhoto, Upload
from .validation import (
    HuduNotImplementedError,
    HuduValidationError,
    to_bool,
    validate_ip_address,
    validate_network_address,
    validate_pubphoto_file,
    validate_uploadable_type,
    validate_vlan_id,
    validate_vlan_id_ranges,
)


class BaseResource:
    endpoint: HuduEndpoint

    def __init__(self, client):
        self.client = client

    def _require_support(self, operation: str) -> None:
        attr_name = f"supports_{operation}"
        if not getattr(self.endpoint.meta, attr_name, False):
            raise HuduNotImplementedError(
                f"{self.endpoint.name} does not support {operation}"
                f"supported methods are: {supported_methods}"
            )

    def _reraise_with_description(self, exc: HuduValidationError) -> None:
        raise HuduValidationError(
            f"{exc}\n\n{describe_single(self.endpoint)}"
        ) from None

    # core methods for interacting with the API
    def get(self, item_id=None, **params):
        if item_id is None:
            if not self.endpoint.meta.supports_list:
                raise ValueError(f"{self.endpoint.name} does not support list")
            return self.list(**params)

        if not self.endpoint.meta.supports_get:
            raise ValueError(f"{self.endpoint.name} does not support get")

        path = self.client.resolve_path(self.endpoint, item_id)
        return self.client.get(path, paginate=False)

    def create(self, payload: dict[str, Any], **kwargs) -> Any:
        try:
            return self.client.create(self.endpoint, payload, **kwargs)
        except HuduValidationError as e:
            self._reraise_with_description(e)

    def update(self, item_id: int | str, payload: dict[str, Any], **kwargs) -> Any:
        try:
            return self.client.update(self.endpoint, item_id, payload, **kwargs)
        except HuduValidationError as e:
            self._reraise_with_description(e)

    def delete(self, item_id: int | str) -> Any:
        try:
            self._require_support("delete")
            path = self.client.resolve_path(self.endpoint, item_id)
            return self.client.delete(path)
        except HuduValidationError as e:
            raise HuduValidationError(
                f"{e}\n\n{describe_single(self.endpoint)}"
            ) from None

    def archive(self, item_id: int | str) -> Any:
        try:
            self._require_support("archive")
            path = self.client.resolve_path(
                self.endpoint, item_id) + "/archive"
            if item_id is None:
                raise ValueError("Cannot archive object without an id")
            return self.client.put(path)
        except HuduValidationError as e:
            raise HuduValidationError(
                f"{e}\n\n{describe_single(self.endpoint)}"
            ) from None

    def unarchive(self, item_id: int | str) -> Any:
        try:
            self._require_support("unarchive")
            path = self.client.resolve_path(
                self.endpoint, item_id) + "/unarchive"
            if item_id is None:
                raise ValueError("Cannot unarchive object without an id")
            return self.client.put(path)
        except HuduValidationError as e:
            raise HuduValidationError(
                f"{e}\n\n{describe_single(self.endpoint)}"
            ) from None

    # aliased methods for convenience and readability
    def list(self, **params) -> Any:
        self._require_support("list")
        return self.client.get(self.endpoint, params=params or None)

    def get_all(self, **params):
        return self.get(None, **params)

    def new(self, payload: dict, **kwargs):
        return self.create(payload, **kwargs)

    # For resources that support file uploads and relations, we can provide helper methods to list related items
    def list_photos(self, to_object: HuduObject, **params):
        return self.client.photos.list(
            photoable_type=to_object.to_photo_ref(),
            photoable_id=str(to_object.id),
            **params,
        )

    def list_relations(self, to_object: HuduObject):
        relation_ref = to_object.to_relation_ref()
        relation_type = str(relation_ref["type"]).strip().lower()
        object_id = str(relation_ref["id"])

        return [
            r
            for r in self.client.relations.list()
            if (
                str(r.fromable_type).strip().lower() == relation_type
                and str(r.fromable_id) == object_id
            )
            or (
                str(r.toable_type).strip().lower() == relation_type
                and str(r.toable_id) == object_id
            )
        ]

    def list_uploads(self, to_object: HuduObject):
        uploadable_type = to_object.to_upload_ref()
        object_id = str(to_object.id)

        return [
            u
            for u in self.client.uploads.list()
            if u.uploadable_type == uploadable_type
            and str(u.uploadable_id) == object_id
        ]


class BaseFileResource(BaseResource):
    endpoint: ClassVar[HuduEndpoint]
    model_cls: ClassVar[type]
    file_form_field: ClassVar[str] = "file"

    def _validate_file_path(self, file_path: str | Path) -> Path:
        file_path = Path(file_path)
        if not file_path.is_file():
            raise FileNotFoundError(f"File not found: {file_path}")
        return file_path

    def _safe_filename(self, filename: str | None, fallback: str) -> str:
        filename = filename or fallback
        return "".join("_" if c in '<>:"/\\|?*' else c for c in filename)

    def _wrap_model(self, result: Any) -> Any:
        if isinstance(result, dict):
            result = self.client._extract_primary_object(result)
            return self.model_cls(self.client, self.endpoint, result)
        return result

    def _post_file(
        self,
        file_path: str | Path,
        *,
        data: dict[str, str],
    ) -> Any:
        file_path = self._validate_file_path(file_path)

        with file_path.open("rb") as fh:
            result = self.client.post(
                self.endpoint,
                files={self.file_form_field: (file_path.name, fh)},
                data=data,
            )

        return self._wrap_model(result)

    def _download_file(
        self,
        object_or_id,
        out_dir: str | Path = ".",
        *,
        download_path_template: str,
        fallback_prefix: str,
    ) -> Path:
        if hasattr(object_or_id, "id"):
            obj = object_or_id
            object_id = obj.id
        else:
            object_id = object_or_id
            obj = self.get(object_id)

        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        filename = (
            getattr(obj, "name", None)
            or getattr(obj, "file_name", None)
            or str(object_id)
        )

        safe_name = self._safe_filename(
            filename, f"{fallback_prefix}-{object_id}")
        destination = out_dir / safe_name

        url = self.client.build_url(
            download_path_template.format(id=object_id))
        response = self.client.session.get(url, timeout=self.client.timeout)
        response.raise_for_status()

        destination.write_bytes(response.content)

        return destination


class CompaniesResource(BaseResource):
    endpoint = HuduEndpoint.COMPANIES


class PhotosResource(BaseFileResource):
    endpoint = HuduEndpoint.PHOTOS
    model_cls = Photo
    file_form_field = "file"

    def create(
        self,
        file_path: str | Path,
        to_object: HuduObject,
        caption: str | None = None,
    ) -> Any:
        validate_pubphoto_file(file_path)

        photoable_type = to_object.to_photo_ref()

        if not caption or not str(caption).strip():
            caption = f"uploaded photo to {photoable_type} with id {to_object.id} without caption"

        return self._post_file(
            file_path,
            data={
                "caption": caption,
                "photoable_id": str(to_object.id),
                "photoable_type": photoable_type,
            },
        )

    def download(self, photo_or_id, out_dir: str | Path = ".") -> Path:
        return self._download_file(
            photo_or_id,
            out_dir=out_dir,
            download_path_template="photos/{id}?download=true",
            fallback_prefix="photo",
        )


class PublicPhotosResource(BaseFileResource):
    endpoint = HuduEndpoint.PUBLIC_PHOTOS
    model_cls = PublicPhoto
    file_form_field = "photo"

    def create(
        self,
        file_path: str | Path,
        to_object: HuduObject,
    ) -> Any:
        validate_pubphoto_file(file_path)

        photoable_type = to_object.to_pubphoto_ref()

        return self._post_file(
            file_path,
            data={
                "record_id": str(to_object.id),
                "record_type": photoable_type,
            },
        )

    def download(self, photo_or_id, out_dir: str | Path = ".") -> Path:
        raise NotImplementedError(
            "Hudu API does not currently support downloading public photos"
        )


class UploadsResource(BaseFileResource):
    endpoint = HuduEndpoint.UPLOADS
    model_cls = Upload

    def list(self, **params) -> Any:
        if is_version_greater_or_equal(str(self.client.check_version()), "2.41.3"):
            return self.client.get(self.endpoint, params=params or None, paginate=True)
        return self.client.get(self.endpoint, params=params or None, paginate=False)

    def create(
        self,
        file_path: str | Path,
        to_object: HuduObject,
    ) -> Any:
        uploadable_type = to_object.to_upload_ref()
        if not uploadable_type or validate_uploadable_type(uploadable_type) is False:
            raise ValueError(
                f"object is not of uploadable type {uploadable_type}")

        return self._post_file(
            file_path,
            data={
                "upload[uploadable_id]": str(to_object.id),
                "upload[uploadable_type]": uploadable_type,
            },
        )

    def download(self, upload_or_id, out_dir: str | Path = ".") -> Path:
        return self._download_file(
            upload_or_id,
            out_dir=out_dir,
            download_path_template="uploads/{id}?download=true",
            fallback_prefix="upload",
        )


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


class Asset_LayoutsResource(BaseResource):
    endpoint = HuduEndpoint.ASSET_LAYOUTS


class PasswordFoldersResource(BaseResource):
    endpoint = HuduEndpoint.PASSWORD_FOLDERS

    def save(self, item_id: int | str, payload: dict[str, Any], **kwargs) -> Any:
        company_id = payload.get("company_id")
        if company_id is None:
            raise ValueError(
                "company_id is required in payload to update a password folder"
            )

        if payload.get("security") is None:
            payload["security"] = "all_users"

        path = f"companies/{company_id}/password_folders/{item_id}"
        result = self.client.put(path, json={"password_folder": payload})
        return self.client._wrap_result(self.endpoint, result)


class AssetsResource(BaseResource):
    endpoint = HuduEndpoint.ASSETS

    def delete(self, item_id: int | str, company_id: int | str) -> Any:
        if item_id is None:
            raise ValueError("Cannot delete object without an id")
        if company_id is None:
            raise ValueError("Asset delete() requires company_id")
        return self.client.delete(f"companies/{company_id}/assets/{item_id}")

    def create(self, company_id: int | str, payload: dict[str, Any], **kwargs) -> Any:
        wrapped = {"asset": payload}
        result = self.client.post(
            f"companies/{company_id}/assets", json=wrapped)

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
            str(payload.get("archived")), default=False)
        return self.client.create(self.endpoint, payload, **kwargs)


class VLANZonesResource(BaseResource):
    endpoint = HuduEndpoint.VLAN_ZONES

    def create(self, payload: dict, **kwargs):
        validate_vlan_id_ranges(str(payload.get("vlan_id_ranges")))

        payload["archived"] = to_bool(
            str(payload.get("archived")), default=False)
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


class RackStorageResource(BaseResource):
    endpoint = HuduEndpoint.RACK_STORAGES


class RackStorageItemResource(BaseResource):
    endpoint = HuduEndpoint.RACK_STORAGE_ITEMS


class UsersResource(BaseResource):
    endpoint = HuduEndpoint.USERS


class GroupsResource(BaseResource):
    endpoint = HuduEndpoint.GROUPS


class ProceduresResource(BaseResource):
    endpoint = HuduEndpoint.PROCEDURES


class ProcedureTasksResource(BaseResource):
    endpoint = HuduEndpoint.PROCEDURE_TASKS

    def get(self, item_id=None, **params):
        if item_id is not None and params:
            raise ValueError(
                "Provide either item_id or query params, not both")

        if item_id is None:
            return self.list(**params)

        path = self.endpoint.item_path(item_id)
        return self.client.get(path, paginate=False, property_name="procedure_tasks")


class CardsResource(BaseResource):
    endpoint = HuduEndpoint.CARDS_LOOKUP


class FlagsResource(BaseResource):
    endpoint = HuduEndpoint.FLAGS


class FlagTypesResource(BaseResource):
    endpoint = HuduEndpoint.FLAG_TYPES


class MagicDashesResource(BaseResource):
    endpoint = HuduEndpoint.MAGIC_DASH


class ActivityLogsResource(BaseResource):
    endpoint = HuduEndpoint.ACTIVITY_LOGS


class ExpirationsResource(BaseResource):
    endpoint = HuduEndpoint.EXPIRATIONS


class ListResourceListResource(BaseResource):
    endpoint = HuduEndpoint.LISTS
