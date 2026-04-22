from __future__ import annotations

import time
from pathlib import Path
from typing import Any, ClassVar

from hudu_magic.help import describe_single, supported_methods
from hudu_magic.helpers.general import is_version_greater_or_equal

from .endpoints import HuduEndpoint
from .models import (
    Asset,
    Exports,
    HuduCollection,
    HuduObject,
    Photo,
    PublicPhoto,
    Upload,
    ordered_procedure_tasks,
)
from .validation import (
    HuduAPIError,
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

# Passed through to ``HuduClient.create`` / ``update``, not merged into JSON body.
_CLIENT_HTTP_KWARGS = frozenset({"validate", "allow_unknown_fields"})


class BaseResource:
    endpoint: HuduEndpoint
    
    def _resolve_action_path(
        self,
        item_id: int | str | None = None,
        action: str | None = None,
    ) -> str:
        if item_id is None:
            if action is not None:
                raise ValueError(f"Cannot use action '{action}' without an id")
            return self.client.resolve_path(self.endpoint)

        path = self.client.resolve_path(self.endpoint, item_id)

        if action:
            path = f"{path}/{action}"

        return path    

    def __init__(self, client):
        self.client = client

    def _merge_payload(self, payload: dict | None, kwargs: dict) -> dict:
        if payload and kwargs:
            return {**payload, **kwargs}
        if payload:
            return payload
        return kwargs

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

    def get(self, item_id=None, **params):
        if item_id is None and "id" in params:
            item_id = params.pop("id")

        if item_id is not None:
            if not self.endpoint.meta.supports_get:
                raise ValueError(f"{self.endpoint.name} does not support get")

            path = self.client.resolve_path(self.endpoint, item_id)
            raw = self.client._get_nonpaginated(path)

            item_endpoint = getattr(HuduEndpoint, f"{self.endpoint.name}_ID", self.endpoint)
            result = self.client._wrap_result(item_endpoint, raw)
            if isinstance(result, HuduCollection):
                if not result:
                    return None
                if len(result) == 1 or item_id is not None:
                    return result.first() or None

            if isinstance(result, list):
                if not result:
                    return None
                if len(result) == 1 or item_id is not None:
                    return result[0] or None

            return result

        return self.list(**params)

    def create(self, payload: dict[str, Any] | None = None, **kwargs) -> Any:
        try:
            client_kw = {k: v for k, v in kwargs.items() if k in _CLIENT_HTTP_KWARGS}
            body_kw = {k: v for k, v in kwargs.items() if k not in _CLIENT_HTTP_KWARGS}
            merged = self._merge_payload(payload, body_kw)
            return self.client.create(self.endpoint, merged, **client_kw)
        except HuduValidationError as e:
            self._reraise_with_description(e)

    def update(self, item_id: int | str, payload: dict[str, Any] | None = None, **kwargs) -> Any:
        try:
            client_kw = {k: v for k, v in kwargs.items() if k in _CLIENT_HTTP_KWARGS}
            body_kw = {k: v for k, v in kwargs.items() if k not in _CLIENT_HTTP_KWARGS}
            merged = self._merge_payload(payload, body_kw)
            return self.client.update(self.endpoint, item_id, merged, **client_kw)
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

    # resource-level help-get
    def describe(self) -> str:
        return describe_single(self.endpoint)
    
    def help(self) -> str:
        return self.describe()

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

    def get(self, item_id=None, **params):
        if item_id is None and "id" in params:
            item_id = params.pop("id")

        if item_id is None:
            return self.list(**params)

        raw = self.client._get_nonpaginated(self._resolve_action_path(item_id))
        return self.client._wrap_result(HuduEndpoint.ARTICLES_ID, raw)

    def create(self, payload: dict[str, Any] | None = None, **kwargs) -> Any:
        body_kw = {k: v for k, v in kwargs.items() if k not in _CLIENT_HTTP_KWARGS}
        merged = self._merge_payload(payload, body_kw)
        result = self.client.post(self._resolve_action_path(), json={"article": merged})
        return self.client._wrap_result(HuduEndpoint.ARTICLES, result)

    def update(self, item_id: int | str, payload: dict[str, Any] | None = None, **kwargs) -> Any:
        body_kw = {k: v for k, v in kwargs.items() if k not in _CLIENT_HTTP_KWARGS}
        merged = self._merge_payload(payload, body_kw)
        result = self.client.put(
            self._resolve_action_path(item_id),
            json={"article": merged},
        )
        return self.client._wrap_result(HuduEndpoint.ARTICLES_ID, result)

    def delete(self, item_id: int | str) -> Any:
        return self.client.delete(self._resolve_action_path(item_id))

    def archive(self, item_id: int | str) -> Any:
        return self.client.put(self._resolve_action_path(item_id, "archive"))

    def unarchive(self, item_id: int | str) -> Any:
        return self.client.put(self._resolve_action_path(item_id, "unarchive"))


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

    def _list_company_assets(self, company_id: int | str, params: dict | None) -> Any:
        """GET companies/{company_id}/assets — path is not an endpoint enum, so paginate and wrap here."""
        path = f"companies/{company_id}/assets"
        page = 1
        all_items: list[dict] = []
        p = dict(params or {})
        seen_signatures: set[tuple] = set()
        while True:
            page_params = {**p, "page": page}
            result = self.client._get_nonpaginated(path, page_params)
            if isinstance(result, dict):
                items = (
                    result.get("companies_assets")
                    or result.get("assets")
                    or result.get("items")
                    or result.get("data")
                    or []
                )
            elif isinstance(result, list):
                items = result
            else:
                items = []
            if not items:
                break
            signature = tuple(
                item.get("id") for item in items if isinstance(item, dict)
            )
            if signature in seen_signatures:
                break
            seen_signatures.add(signature)
            all_items.extend(items)
            page += 1
        return self.client._wrap_result(HuduEndpoint.ASSETS, all_items)

    def list(self, company_id=None, **params):
        if company_id is None and "company_id" in params:
            company_id = params.pop("company_id")

        if company_id is not None:
            return self._list_company_assets(company_id, params)

        return self.client.get(self.endpoint, params=params or None, paginate=True)

    def get(self, item_id=None, company_id=None, **params):
        if item_id is None and "id" in params:
            item_id = params.pop("id")

        if company_id is None and "company_id" in params:
            company_id = params.pop("company_id")

        if item_id is not None:
            if company_id is not None:
                path = f"companies/{company_id}/assets/{item_id}"
                raw = self.client._get_nonpaginated(path)
                return self.client._wrap_result(HuduEndpoint.ASSETS, raw)

            result = self.client.get(
                self.endpoint,
                params={"id": item_id, **params},
                paginate=False,
            )

            if isinstance(result, HuduCollection):
                if not result:
                    return None
                if len(result) == 1:
                    return result[0]

            if isinstance(result, list):
                if not result:
                    return None
                if len(result) == 1:
                    return result[0]
                
            if isinstance(result, dict):
                result = self.client._extract_primary_object(result)

            return result

        return self.list(company_id=company_id, **params)
    def create(
        self,
        company_id: int | str,
        payload: dict[str, Any] | None = None,
        **kwargs,
    ) -> Any:
        if company_id is None:
            raise ValueError("Asset create() requires company_id")

        body_kw = {k: v for k, v in kwargs.items() if k not in _CLIENT_HTTP_KWARGS}
        merged = self._merge_payload(payload, body_kw)
        wrapped = {"asset": merged}
        result = self.client.post(f"companies/{company_id}/assets", json=wrapped)

        if isinstance(result, dict):
            result = self.client._extract_primary_object(result)
            return Asset(self.client, HuduEndpoint.ASSETS, result)

        return result

    def update(
        self,
        item_id: int | str,
        company_id: int | str,
        payload: dict[str, Any] | None = None,
        **kwargs,
    ) -> Any:
        if item_id is None:
            raise ValueError("Cannot update asset without an id")
        if company_id is None:
            raise ValueError("Asset update() requires company_id")

        body_kw = {k: v for k, v in kwargs.items() if k not in _CLIENT_HTTP_KWARGS}
        merged = self._merge_payload(payload, body_kw)
        path = f"companies/{company_id}/assets/{item_id}"
        result = self.client.put(path, json={"asset": merged})
        return self.client._wrap_result(HuduEndpoint.ASSETS, result)

    def delete(self, item_id: int | str, company_id: int | str) -> Any:
        if item_id is None:
            raise ValueError("Cannot delete object without an id")
        if company_id is None:
            raise ValueError("Asset delete() requires company_id")

        return self.client.delete(f"companies/{company_id}/assets/{item_id}")

    def archive(self, item_id: int | str, company_id: int | str) -> Any:
        if item_id is None:
            raise ValueError("Cannot archive object without an id")
        if company_id is None:
            raise ValueError("Asset archive() requires company_id")

        path = f"companies/{company_id}/assets/{item_id}/archive"
        return self.client.put(path)

    def unarchive(self, item_id: int | str, company_id: int | str) -> Any:
        if item_id is None:
            raise ValueError("Cannot unarchive object without an id")
        if company_id is None:
            raise ValueError("Asset unarchive() requires company_id")

        path = f"companies/{company_id}/assets/{item_id}/unarchive"
        return self.client.put(path)

    def list_for_company(self, company_id: int | str | HuduObject, **params) -> Any:
        if isinstance(company_id, HuduObject):
            company_id = company_id.id

        if company_id is None:
            raise ValueError("Cannot list assets without a company id")

        return self.list(company_id=company_id, **params)

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

    def assign_task(self, task_id: int | str, user_id: int | str):
        if task_id is None:
            raise ValueError("task_id is required to assign a user to a procedure task")
        taskItem = self.client.procedure_tasks.get(task_id)
        procedure = taskItem.procedure

        if not procedure.is_run:
            template_tasks = ordered_procedure_tasks(self.client, procedure.id)
            try:
                tid = int(task_id)
                idx = next(
                    i
                    for i, t in enumerate(template_tasks)
                    if int(t.id) == tid
                )
            except (StopIteration, TypeError, ValueError) as exc:
                raise ValueError(
                    f"Task {task_id!r} is not listed for procedure {procedure.id!r}"
                ) from exc

            run = procedure.kick_off()
            run_tasks = ordered_procedure_tasks(self.client, run.id)
            if idx >= len(run_tasks):
                raise ValueError(
                    "kick_off succeeded but run task list length does not match template"
                )
            taskItem = run_tasks[idx]

        assignedusers = list(taskItem.assigned_users or [])
        if user_id in assignedusers:
            raise ValueError(
                f"User {user_id} is already assigned to task {taskItem.id}"
            )
        assignedusers.append(user_id)
        return taskItem.update({"assigned_users": assignedusers})
class GroupsResource(BaseResource):
    endpoint = HuduEndpoint.GROUPS


class ProceduresResource(BaseResource):
    endpoint = HuduEndpoint.PROCEDURES


class ProcedureTasksResource(BaseResource):
    endpoint = HuduEndpoint.PROCEDURE_TASKS


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


class ExportsResource(BaseFileResource):
    endpoint = HuduEndpoint.EXPORTS
    model_cls = Exports

    def start(
        self,
        payload: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        """Queue a company data export (``POST /exports``); same as :meth:`create`."""
        return self.create(payload, **kwargs)

    def get(self, item_id=None, **params):
        if item_id is None and "id" in params:
            item_id = params.pop("id")

        if item_id is None:
            return super().get(None, **params)

        if not self.endpoint.meta.supports_get:
            raise ValueError(f"{self.endpoint.name} does not support get")

        # Plain GET /exports/{id} returns JSON metadata while the job runs. A
        # ``download=false`` query hits file semantics and can 404 with "Export file
        # not available" until the export completes (see Get-HuduExports in HuduAPI).
        path = self.client.resolve_path(self.endpoint, item_id)
        raw = self.client._get_nonpaginated(path)
        item_endpoint = HuduEndpoint.EXPORTS_ID
        result = self.client._wrap_result(item_endpoint, raw)
        if isinstance(result, HuduCollection):
            if not result:
                return None
            if len(result) == 1 or item_id is not None:
                return result.first() or None

        if isinstance(result, list):
            if not result:
                return None
            if len(result) == 1 or item_id is not None:
                return result[0] or None

            return result

        return result

    def wait_until_downloadable(
        self,
        export_or_id,
        *,
        interval: float = 2.0,
        timeout: float | None = 1800.0,
    ) -> Exports:
        """Poll until ``download_url`` is set (same readiness signal as ``Save-HuduExports``).

        Relying on ``status == \"completed\"`` is brittle across Hudu versions; the API
        exposes a ``download_url`` when the file can be fetched.
        """
        if hasattr(export_or_id, "id"):
            export_id = export_or_id.id
        else:
            export_id = export_or_id

        deadline = None if timeout is None else time.monotonic() + timeout
        terminal_fail = frozenset({"failed", "error", "cancelled", "canceled"})

        while True:
            try:
                current = self.get(export_id)
            except HuduAPIError as exc:
                if exc.status_code != 404 or "not available" not in str(exc).lower():
                    raise
                if deadline is not None and time.monotonic() >= deadline:
                    raise TimeoutError(
                        f"Timed out after {timeout}s waiting for export {export_id!r} "
                        f"(export still unavailable)"
                    ) from exc
                time.sleep(interval)
                continue

            if current is None:
                raise ValueError(f"Export {export_id!r} not found while polling")

            data = current.to_dict()
            status = str(data.get("status") or "").strip().lower()
            if status in terminal_fail:
                raise RuntimeError(
                    f"Export {export_id} ended with status={data.get('status')!r}"
                )

            if str(data.get("download_url") or "").strip():
                return current

            if deadline is not None and time.monotonic() >= deadline:
                raise TimeoutError(
                    f"Timed out after {timeout}s waiting for export {export_id} "
                    f"(last status={data.get('status')!r})"
                )

            time.sleep(interval)

    def download(self, export_or_id, out_dir: str | Path = ".") -> Path:
        """Save export bytes to ``out_dir`` (uses ``download_url`` when set, else API download)."""
        if hasattr(export_or_id, "id"):
            obj = export_or_id
            object_id = obj.id
            if not str(obj.get("download_url") or "").strip():
                obj = self.get(object_id)
        else:
            object_id = export_or_id
            obj = self.get(object_id)

        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        file_name = obj.get("file_name")
        is_pdf = obj.get("is_pdf")
        ext = ".pdf" if is_pdf else ".csv"
        safe_name = self._safe_filename(file_name, f"export-{object_id}{ext}")
        destination = out_dir / safe_name

        download_url = obj.get("download_url")
        if download_url and str(download_url).strip():
            url = str(download_url).strip()
        else:
            url = self.client.build_url(f"exports/{object_id}?download=true")

        response = self.client.session.get(
            url,
            timeout=self.client.timeout,
            allow_redirects=True,
        )
        response.raise_for_status()
        destination.write_bytes(response.content)
        return destination


class S3ExportsResource(BaseResource):
    endpoint = HuduEndpoint.S3_EXPORTS

    def start(
        self,
        payload: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        """Begin an S3-side export (``POST /s3_exports``); same as :meth:`create`."""
        return self.create(payload, **kwargs)


class ListResourceListResource(BaseResource):
    endpoint = HuduEndpoint.LISTS
