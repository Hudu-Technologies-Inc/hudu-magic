from __future__ import annotations

from typing import Any

import requests

from hudu_magic.endpoints import HuduEndpoint
from hudu_magic.instance import Instance

from .models import MODEL_MAP, HuduCollection
from .payloads import maybe_wrap_payload
from .resources import (ActivityLogsResource, ArticlesResource,
                        Asset_LayoutsResource, AssetPasswordsResource,
                        AssetsResource, CardsResource, CompaniesResource,
                        ExpirationsResource, FlagsResource, FlagTypesResource,
                        FoldersResource, GroupsResource, IPAddressesResource,
                        ListResourceListResource, MagicDashesResource,
                        NetworksResource, PasswordFoldersResource,
                        PhotosResource, ProceduresResource,
                        ProcedureTasksResource, PublicPhotosResource,
                        RackStorageItemResource, RackStorageResource,
                        RelationsResource, UploadsResource, UsersResource,
                        ExportsResource, S3ExportsResource,
                        VlansResource, VLANZonesResource, WebsitesResource)
from .validation import HuduAPIError, validate_payload


class HuduClient:
    def __init__(self, api_key: str, instance_url: str, timeout: int = 30):
        self.instance = Instance(api_key=api_key, instance_url=instance_url)
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(self.instance.get_request_headers)
        self.version = None
        self.companies = CompaniesResource(self)
        self.articles = ArticlesResource(self)
        self.folders = FoldersResource(self)
        self.exports = ExportsResource(self)
        self.websites = WebsitesResource(self)
        self.asset_layouts = Asset_LayoutsResource(self)
        self.assets = AssetsResource(self)
        self.asset_passwords = AssetPasswordsResource(self)
        self.password_folders = PasswordFoldersResource(self)
        self.uploads = UploadsResource(self)
        self.photos = PhotosResource(self)
        self.public_photos = PublicPhotosResource(self)
        self.relations = RelationsResource(self)
        self.ipaddresses = IPAddressesResource(self)
        self.vlans = VlansResource(self)
        self.vlan_zones = VLANZonesResource(self)
        self.networks = NetworksResource(self)
        self.users = UsersResource(self)
        self.groups = GroupsResource(self)
        self.procedures = ProceduresResource(self)
        self.procedure_tasks = ProcedureTasksResource(self)
        self.rack_storage_items = RackStorageItemResource(self)
        self.rack_storages = RackStorageResource(self)
        self.ActivityLogs = ActivityLogsResource(self)
        self.flags = FlagsResource(self)
        self.flag_types = FlagTypesResource(self)
        self.cards = CardsResource(self)
        self.magic_dashes = MagicDashesResource(self)
        self.lists = ListResourceListResource(self)
        self.expirations = ExpirationsResource(self)
        # aliases
        self.ActivityLog = self.ActivityLogs
        self.activity_log = self.ActivityLogs
        self.flag = self.flags
        self.flag_type = self.flag_types
        self.card = self.cards
        self.magic_dash = self.magic_dashes
        self.list = self.lists
        self.rack_storage = self.rack_storages
        self.rack_storage_item = self.rack_storage_items
        self.procedure_task = self.procedure_tasks
        self.procedure = self.procedures
        self.group = self.groups
        self.user = self.users
        self.photo = self.photos
        self.public_photo = self.public_photos
        self.relation = self.relations
        self.upload = self.uploads
        self.addresses = self.ipaddresses
        self.ip_addresses = self.ipaddresses
        self.address = self.ipaddresses
        self.ip_address = self.ipaddresses
        self.vlan = self.vlans
        self.zone = self.vlan_zones
        self.vlanzone = self.vlan_zones
        self.vlan_zone = self.vlan_zones
        self.network = self.networks
        self.password_folder = self.password_folders
        self.passwordfolders = self.password_folders
        self.passwordfolder = self.password_folders
        self.asset_password = self.asset_passwords
        self.passwords = self.asset_passwords
        self.password = self.asset_passwords
        self.asset = self.assets
        self.company = self.companies
        self.article = self.articles
        self.folder = self.folders
        self.website = self.websites
        self.asset_layout = self.asset_layouts

    def check_version(self):
        if self.version is None:
            info = (self.get("api_info"))
            self.version = info.get("version", "unknown") if isinstance(
                info, dict) else None
        return self.version

    def build_url(self, endpoint: HuduEndpoint | str) -> str:
        endpoint_path = endpoint.endpoint if isinstance(
            endpoint, HuduEndpoint) else str(endpoint).lstrip("/")
        return f"{self.instance.instance_url}/{endpoint_path}"

    def _handle_response(self, response: requests.Response) -> Any:
        if not response.ok:
            try:
                payload = response.json()
                message = payload.get("message") or payload.get(
                    "error") or response.text
            except Exception:
                message = response.text

            request_body = None
            try:
                request_body = response.request.body
            except Exception:
                pass

            raise HuduAPIError(
                response.status_code,
                f"{message}\n"
                f"METHOD={response.request.method}\n"
                f"URL={response.request.url}\n"
                f"BODY={request_body}"
            )

        if not response.text.strip():
            return None

        content_type = response.headers.get("Content-Type", "")
        if "application/json" in content_type:
            return response.json()

        return response.text

    def _extract_primary_object(self, result: dict):
        if "id" in result:
            return result

        for value in result.values():
            if isinstance(value, dict) and "id" in value:
                return value

        return result

    def _wrap_result(self, endpoint, result):
        if not isinstance(endpoint, HuduEndpoint):
            return result

        model_cls = MODEL_MAP.get(endpoint)
        if model_cls is None:
            return result

        def wrap_item(item):
            return model_cls(self, endpoint, item) if isinstance(item, dict) else item

        def wrap_many(items):
            wrapped = [wrap_item(item) for item in items]
            if len(wrapped) == 1:
                return wrapped[0]
            return HuduCollection(wrapped)

        if isinstance(result, list):
            return wrap_many(result)

        if isinstance(result, dict):
            collection_key = endpoint.resource_name
            if collection_key in result and isinstance(result[collection_key], list):
                return wrap_many(result[collection_key])

            primary = self._extract_primary_object(result)
            if isinstance(primary, dict):
                return model_cls(self, endpoint, primary)

        return result

    def _prepare_payload(
        self,
        endpoint: HuduEndpoint | str,
        payload: dict[str, Any],
        *,
        operation: str,
        validate: bool = True,
        allow_unknown_fields: bool = False,
    ) -> dict[str, Any]:
        if isinstance(endpoint, HuduEndpoint) and validate:
            validate_payload(
                endpoint,
                payload,
                operation,
                allow_unknown_fields=allow_unknown_fields,
            )

        return maybe_wrap_payload(endpoint, payload)

    def post(
        self,
        endpoint: HuduEndpoint | str,
        *,
        json: dict | None = None,
        files: dict | None = None,
        data: dict | None = None,
    ) -> Any:
        response = self.session.post(
            self.build_url(endpoint),
            json=json if files is None else None,
            data=data,
            files=files,
            timeout=self.timeout,
        )
        return self._handle_response(response)

    def put(
        self,
        endpoint: HuduEndpoint | str,
        *,
        json: dict | None = None,
        files: dict | None = None,
        data: dict | None = None,
    ) -> Any:
        response = self.session.put(
            self.build_url(endpoint),
            json=json if files is None else None,
            data=data if files is not None else None,
            files=files,
            timeout=self.timeout,
        )
        return self._handle_response(response)

    def delete(self, endpoint: HuduEndpoint | str) -> Any:
        response = self.session.delete(
            self.build_url(endpoint),
            timeout=self.timeout,
        )
        return self._handle_response(response)

    def get(
        self,
        endpoint: HuduEndpoint | str,
        params: dict | None = None,
        paginate: bool | None = None,
        property_name: str | None = None,
    ):
        if isinstance(endpoint, HuduEndpoint):
            if paginate is None:
                paginate = endpoint.is_paginated

            if paginate:
                result = self._get_all_pages(
                    endpoint, params, property_name=property_name)
                return self._wrap_result(endpoint, result)

        result = self._get_nonpaginated(endpoint, params)
        return self._wrap_result(endpoint, result)

    def _get_nonpaginated(self, endpoint: HuduEndpoint | str, params: dict | None = None) -> Any:
        response = self.session.get(
            self.build_url(endpoint),
            params=params,
            timeout=self.timeout,
        )
        return self._handle_response(response)

    def _get_all_pages(
        self,
        endpoint: HuduEndpoint,
        params: dict | None = None,
        property_name: str | None = None,
    ) -> list[dict]:
        page = 1
        all_items: list[dict] = []
        params = dict(params or {})
        seen_signatures: set[tuple] = set()

        while True:
            page_params = dict(params)
            page_params["page"] = page

            result = self._get_nonpaginated(endpoint, params=page_params)

            if isinstance(result, dict):
                items = result.get(property_name) or result.get(
                    endpoint.resource_name) or result.get("items") or result.get("data") or []
            elif isinstance(result, list):
                items = result
            else:
                items = []

            if not items:
                break

            signature = tuple(
                item.get("id") for item in items
                if isinstance(item, dict)
            )
            if signature in seen_signatures:
                break

            seen_signatures.add(signature)
            all_items.extend(items)
            page += 1

        return all_items

    def archive(self, endpoint: HuduEndpoint | str, item_id: int | str,
                payload: dict | None = None):
        path = self.resolve_path(endpoint, item_id) + "/archive"
        return self.put(path, json=payload)

    def unarchive(self, endpoint: HuduEndpoint | str, item_id: int | str,
                  payload: dict | None = None):
        path = self.resolve_path(endpoint, item_id) + "/unarchive"
        return self.put(path, json=payload)

    def create(
        self,
        endpoint: HuduEndpoint | str,
        payload: dict[str, Any],
        *,
        validate: bool = True,
        allow_unknown_fields: bool = False,
    ):
        prepared = self._prepare_payload(
            endpoint,
            payload,
            operation="create",
            validate=validate,
            allow_unknown_fields=allow_unknown_fields,
        )
        result = self.post(endpoint, json=prepared)
        return self._wrap_result(endpoint, result)

    def update(
        self,
        endpoint: HuduEndpoint | str,
        item_id: int | str,
        payload: dict[str, Any],
        *,
        validate: bool = True,
        allow_unknown_fields: bool = False,
    ):
        if isinstance(endpoint, HuduEndpoint) and validate:
            validate_payload(
                endpoint,
                payload,
                "update",
                allow_unknown_fields=allow_unknown_fields,
            )

        path = self.resolve_path(endpoint, item_id)
        wrapped_payload = maybe_wrap_payload(endpoint, payload)
        result = self.put(path, json=wrapped_payload)
        return self._wrap_result(endpoint, result)

    def resolve_path(self, endpoint: HuduEndpoint | str, item_id: int | str | None = None) -> str:
        if isinstance(endpoint, HuduEndpoint):
            if item_id is not None:
                if "{id}" in endpoint.endpoint:
                    return f"/{endpoint.endpoint.replace('{id}', str(item_id))}"
                return endpoint.item_path(item_id)
            return endpoint.path

        endpoint_str = str(endpoint).lstrip("/")
        if item_id is not None:
            if "{id}" in endpoint_str:
                return f"/{endpoint_str.replace('{id}', str(item_id))}"
            return f"/{endpoint_str.rstrip('/')}/{item_id}"
        return f"/{endpoint_str}"

    def delete_item(self, endpoint: HuduEndpoint | str, item_id: int | str):
        return self.delete(self.resolve_path(endpoint, item_id))
