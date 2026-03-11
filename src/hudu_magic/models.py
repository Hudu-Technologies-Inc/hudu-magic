from __future__ import annotations

from typing import Any
from .endpoints import HuduEndpoint
from .payloads import transform_custom_fields_for_save, clean_payload, normalize_asset_payload_for_save

class HuduObject:
    def __init__(self, client, endpoint, data):
        self._client = client
        self._endpoint = endpoint
        self._data = data

    def __repr__(self):
        object_id = self._data.get("id")
        name = self._data.get("name")
        return f"<{self.__class__.__name__} id={object_id} name={name!r}>"

    def __str__(self) -> str:
        return repr(self)

    def __getattr__(self, item: str):
        try:
            return self._data[item]
        except KeyError as exc:
            raise AttributeError(item) from exc

    def get(self, key, default=None):
        return self._data.get(key, default)

    def values(self):
        return self._data.values()

    def items(self):
        return self._data.items()

    def keys(self):
        return self._data.keys()

    def to_dict(self):
        return dict(self._data)

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def __contains__(self, item):
        return item in self._data

    def __getitem__(self, item):
        return self._data[item]

    def save(self, **kwargs):
        if self.id is None:
            raise ValueError("Cannot save object without an id")

        update_endpoint = getattr(self.__class__,
                                  "update_endpoint",
                                  self._endpoint)

        payload = clean_payload(self.to_dict())


        updated = self._client.update(
            update_endpoint,
            self.id,
            payload,
            **kwargs,
        )

        if hasattr(updated, "_data"):
            self._data = dict(updated._data)
            return self

        if isinstance(updated, dict):
            self._data = dict(updated)
            return self

        return updated


    @property
    def id(self):
        return self._data.get("id")

    def refresh(self):
        if self.id is None:
            raise ValueError("Cannot refresh object without an id")

        refreshed = self._client.get(
            self._client.resolve_path(self._endpoint, self.id),
            paginate=False,
        )

        if isinstance(refreshed, HuduObject):
            self._data = refreshed._data
        elif isinstance(refreshed, dict):
            self._data = refreshed
        else:
            raise ValueError(f"Unexpected refresh result: {type(refreshed)}")

        return self

    def update(self, payload: dict[str, Any], **kwargs):
        if self.id is None:
            raise ValueError("Cannot update object without an id")

        updated = self._client.update(self._endpoint, self.id, payload, **kwargs)

        if isinstance(updated, HuduObject):
            self._data = updated._data
            return self

        if isinstance(updated, dict):
            self._data = updated
            return self

        return updated

    def delete(self):
        if self.id is None:
            raise ValueError("Cannot delete object without an id")

        return self._client.delete(
            self._client.resolve_path(self._endpoint, self.id)
        )


    @classmethod
    def get(cls, client, item_id: int | str | None = None, **params):
        if not cls.resource_attr:
            raise NotImplementedError(f"{cls.__name__} does not define resource_attr")

        resource = getattr(client, cls.resource_attr)

        if item_id is None:
            return resource.list(**params)

        return resource.get(item_id)

    @classmethod
    def get_all(cls, client, **params):
        return cls.get(client, **params)

    @classmethod
    def get_by_id(cls, client, item_id: int | str):
        return cls.get(client, item_id)
    

class Company(HuduObject):
    pass


class Article(HuduObject):
    pass

class Asset(HuduObject):
    # Note: Asset has a custom save() method because the API requires
    # a different payload structure for updates vs creates, and the endpoint
    # is also different (nested under company)
    # in the future, when models are isomorphic with API endpoints,
    # we may want to move this logic into the client or resources layer
    # instead of the model layer
    endpoint = HuduEndpoint.ASSETS
    resource_attr = "assets"

    def save(self, **kwargs):
        if self.id is None:
            raise ValueError("Cannot save object without an id")

        payload = normalize_asset_payload_for_save(self.to_dict())
        company_id = payload.get("company_id") or self.get("company_id")
        if company_id is None:
            raise ValueError("Asset save() requires company_id")

        path = f"companies/{company_id}/assets/{self.id}"
        updated = self._client.put(path, json={"asset": payload})
        refreshed = self._client.get(path, paginate=False)
        if hasattr(refreshed, "_data"):
            self._data = dict(refreshed._data)
        elif isinstance(refreshed, dict):
            refreshed = self._client._extract_primary_object(refreshed)
            self._data = dict(refreshed)

        return self
    @classmethod
    def from_dict(cls, client, endpoint, data):
        return cls(client, endpoint, data)

class Folder(HuduObject):
    pass


class Website(HuduObject):
    pass


class AssetLayout(HuduObject):
    pass

class HuduCollection(list):
    def first(self):
        return self[0] if self else None

    def ids(self):
        return [obj.id for obj in self if getattr(obj, "id", None) is not None]

    def to_dicts(self):
        return [obj.to_dict() if hasattr(obj, "to_dict") else obj for obj in self]

    def filter(self, **criteria):
        def matches(obj):
            return all(getattr(obj, key, None) == value for key, value in criteria.items())
        return HuduCollection([obj for obj in self if matches(obj)])

MODEL_MAP = {
    HuduEndpoint.COMPANIES: Company,
    HuduEndpoint.COMPANIES_ID: Company,
    HuduEndpoint.ARTICLES: Article,
    HuduEndpoint.ARTICLES_ID: Article,
    HuduEndpoint.ASSETS: Asset,
    HuduEndpoint.FOLDERS: Folder,
    HuduEndpoint.FOLDERS_ID: Folder,
    HuduEndpoint.WEBSITES: Website,
    HuduEndpoint.WEBSITES_ID: Website,
    HuduEndpoint.ASSET_LAYOUTS: AssetLayout,
    HuduEndpoint.ASSET_LAYOUTS_ID: AssetLayout,
}