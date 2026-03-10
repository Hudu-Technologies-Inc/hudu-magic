from __future__ import annotations
import requests
from typing import Any
from dataclasses import dataclass, field
from enum import Enum
from hudu_magic.endpoints import HuduEndpoint
from hudu_magic.exceptions import HuduAPIError
from hudu_magic.instance import Instance
from .validation import validate_payload

class HuduClient:
    def __init__(self, api_key: str, instance_url: str, timeout: int = 30):
        self.instance = Instance(api_key=api_key, instance_url=instance_url)
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(self.instance.get_request_headers)


    def build_url(self, endpoint: HuduEndpoint | str) -> str:
        endpoint_path = endpoint.endpoint if isinstance(endpoint, HuduEndpoint) else str(endpoint).lstrip("/")
        return f"{self.instance.instance_url}/{endpoint_path}"

    def _handle_response(self, response: requests.Response) -> Any:
        if not response.ok:
            try:
                payload = response.json()
                message = payload.get("message") or payload.get("error") or response.text
            except Exception:
                message = response.text
            raise HuduAPIError(response.status_code, message)

        if not response.text.strip():
            return None

        content_type = response.headers.get("Content-Type", "")
        if "application/json" in content_type:
            return response.json()

        return response.text


    def create(
        self,
        endpoint: HuduEndpoint | str,
        payload: dict[str, Any],
        *,
        validate: bool = True,
        allow_unknown_fields: bool = False,
    ):
        if isinstance(endpoint, HuduEndpoint) and validate:
            validate_payload(
                endpoint,
                payload,
                "create",
                allow_unknown_fields=allow_unknown_fields,
            )
        return self.post(endpoint, json=payload)


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

        path = endpoint.item_path(item_id) if isinstance(endpoint, HuduEndpoint) else f"{str(endpoint).rstrip('/')}/{item_id}"
        return self.put(path, json=payload)

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
            data=data if files is not None else None,
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
    ) -> Any:
        """
        Intelligent GET with optional pagination override.
        """

        if isinstance(endpoint, HuduEndpoint):
            if paginate is None:
                paginate = endpoint.is_paginated

            if paginate:
                return self._get_all_pages(endpoint, params)

        return self._get_nonpaginated(endpoint, params)

    def _get_nonpaginated(self, endpoint: HuduEndpoint | str, params: dict | None = None) -> Any:
        response = self.session.get(
            self.build_url(endpoint),
            params=params,
            timeout=self.timeout,
        )
        return self._handle_response(response)


    def _get_all_pages(self, endpoint: HuduEndpoint, params: dict | None = None) -> list[dict]:
        page = 1
        all_items: list[dict] = []
        params = dict(params or {})

        while True:
            page_params = dict(params)
            page_params["page"] = page

            result = self._get_nonpaginated(endpoint, params=page_params)

            if isinstance(result, dict):
                items = result.get(endpoint.endpoint) or result.get("items") or result.get("data") or []
            elif isinstance(result, list):
                items = result
            else:
                items = []

            if not items:
                break

            all_items.extend(items)
            page += 1

        return all_items



