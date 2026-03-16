from __future__ import annotations

from typing import Any
from .endpoints import HuduEndpoint
from .payloads import (transform_custom_fields_for_save,
                       clean_payload, normalize_asset_payload_for_save,
                       normalize_company_payload_for_save,
                       normalize_password_payload_for_save,
                       normalize_website_payload_for_save,
                       normalize_folder_payload_for_save,
                       normalize_ipam_payload_for_save
)
from .validation import (
    HuduValidationError,
    validate_vlan_id,
    validate_vlan_id_ranges,
    validate_network_address,
    validate_ip_address,
    to_bool,
    validate_relatables,
)

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

    def relate_to(self, other: "HuduObject", description: str | None = None,
                  is_inverse: bool = False):
        return self._client.relations.create(
            self,
            other,
            description=description,
            is_inverse=is_inverse,
        )

    def to_relation_ref(self) -> dict[str, object]:
        if self.id is None:
            raise ValueError(f"{self.__class__.__name__} has no id")
        if not self.relation_type:
            raise ValueError(f"{self.__class__.__name__} not relateable")

        return {
            "id": self.id,
            "type": self.relation_type,
        }    


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
    relation_type = "Company"
    
    def save(self, **kwargs):
        if self.id is None:
            raise ValueError("Cannot save object without an id")

        payload = normalize_company_payload_for_save(self.to_dict())

        path = f"companies/{self.id}"
        updated = self._client.put(path, json=payload)
        refreshed = self._client.get(path, paginate=False)
        if hasattr(refreshed, "_data"):
            self._data = dict(refreshed._data)
        elif isinstance(refreshed, dict):
            refreshed = self._client._extract_primary_object(refreshed)
            self._data = dict(refreshed)

        return self


class Article(HuduObject):
    relation_type = "Article"
    

    def to_folder(self, folder: int | HuduObject.folder):
        if self.id is None:
            raise ValueError("Cannot add article to folder without an id")
        if isinstance(folder, HuduObject):
            folder_id = folder.id
        elif isinstance(folder, int):
            folder_id = folder
        else:
            raise ValueError("folder must be an int or HuduObject")

        self.folder_id = folder_id
        return self.save()
    
    def save(self, **kwargs):
        if self.id is None:
            raise ValueError("Cannot save object without an id")

        payload = clean_payload(self.to_dict())

        path = f"articles/{self.id}"
        updated = self._client.put(path, json=payload)
        refreshed = self._client.get(path, paginate=False)
        if hasattr(refreshed, "_data"):
            self._data = dict(refreshed._data)
        elif isinstance(refreshed, dict):
            refreshed = self._client._extract_primary_object(refreshed)
            self._data = dict(refreshed)

        return self


class Asset(HuduObject):
    relation_type = "Asset"
    resource_attr = "assets"
    endpoint = HuduEndpoint.ASSETS

    def delete(self):
        if self.id is None:
            raise ValueError("Cannot delete object without an id")

        company_id = self.company_id or self.get("company_id")
        if company_id is None:
            raise ValueError("Asset delete() requires company_id")

        path = f"companies/{company_id}/assets/{self.id}"
        return self._client.delete(path)

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


class Relation(HuduObject):
    def create(self, fromable: HuduObject, toable: HuduObject, **kwargs) -> Any:
        if fromable.id is None or toable.id is None:
            raise ValueError("Both objects in a relation must have an id")
        try:
            validate_relatables(fromable._endpoint, toable._endpoint)
        except HuduValidationError as e:
            raise ValueError(f"Invalid relation: {e}")

        payload = {"relation": {
            "from_type": fromable._endpoint,
            "from_id": fromable.id,
            "to_type": toable._endpoint,
            "to_id": toable.id,
        }}
        return self._client.post(self._endpoint, payload, **kwargs)


class Folder(HuduObject):
    def save(self, **kwargs):
        if self.id is None:
            raise ValueError("Cannot save object without an id")

        payload = normalize_folder_payload_for_save(self.to_dict())

        path = f"folders/{self.id}"
        updated = self._client.put(path, json=payload)
        refreshed = self._client.get(path, paginate=False)
        if hasattr(refreshed, "_data"):
            self._data = dict(refreshed._data)
        elif isinstance(refreshed, dict):
            refreshed = self._client._extract_primary_object(refreshed)
            self._data = dict(refreshed)

        return self


class Website(HuduObject):
    relation_type = "Website"
    
    def update(self, payload: dict[str, Any], **kwargs):
        if self.id is None:
            raise ValueError("Cannot update object without an id")
        if self.company_id is None:
            raise ValueError("Cannot update object without a company_id")

        payload = normalize_website_payload_for_save(payload)
        path = f"websites/{self.id}"
        updated = self._client.put(path, self.id, payload, **kwargs)

        if isinstance(updated, HuduObject):
            self._data = updated._data
            return self

        if isinstance(updated, dict):
            self._data = updated
            return self

        return updated
    def save(self, **kwargs):
        if self.id is None:
            raise ValueError("Cannot update object without an id")
        if self.company_id is None:
            raise ValueError("Cannot update object without a company_id")

        payload = normalize_website_payload_for_save(self.to_dict())
        path = f"websites/{self.id}"
        updated = self._client.put(path, json=payload)
        refreshed = self._client.get(path, paginate=False)
        if hasattr(refreshed, "_data"):
            self._data = dict(refreshed._data)
        elif isinstance(refreshed, dict):
            refreshed = self._client._extract_primary_object(refreshed)
            self._data = dict(refreshed)
        return self


class AssetLayout(HuduObject):
    pass


class PasswordFolder(HuduObject):
    def save(self, item_id: int | str, payload: dict[str, Any], **kwargs) -> Any:
        if self.id is None:
            raise ValueError("Cannot save object without an id")
        company_id = payload.get("company_id") or self.get("company_id")
        if company_id is None:
            raise ValueError("PasswordFolder save() requires company_id")
        payload = normalize_password_payload_for_save(payload)
        path = f"companies/{company_id}/password_folders/{self.id}"
        updated = self._client.put(path, json=payload)
        refreshed = self._client.get(path, paginate=False)
        if hasattr(refreshed, "_data"):
            self._data = dict(refreshed._data)
        elif isinstance(refreshed, dict):
            refreshed = self._client._extract_primary_object(refreshed)
            self._data = dict(refreshed)
        return self

    def add_passwords(self, password: int | list[int] | HuduObject.password | list[HuduObject.password]):
        if self.id is None:
            raise ValueError("Cannot add password to folder without an id")
        if password is None:
            raise ValueError("Must provide password_id to add_password")
        if isinstance(password, HuduObject):
            password.to_folder(self.id)
        elif isinstance(password, int):
            return self._client.asset_passwords.update(password, {"password_folder_id": self.id})
        else:
            raise ValueError("password must be an int or HuduObject")
        if isinstance(password, list):
            for p in password:
                if isinstance(p, HuduObject):
                    p.to_folder(self.id)
                elif isinstance(p, int):
                    self._client.asset_passwords.get(p).to_folder(self.id)
                else:
                    raise ValueError("password list must contain ints or HuduObjects")
        return True


class Network(HuduObject):
    relation_type = "Network"
    endpoint = HuduEndpoint.NETWORKS


class IPaddress(HuduObject):
    relation_type = "IpAddress"
    endpoint = HuduEndpoint.IP_ADDRESSES


class VLan(HuduObject):
    relation_type = "Vlan"
    endpoint = HuduEndpoint.VLANS

    def save(self, **kwargs):
        if self.id is None:
            raise ValueError("Cannot update object without an id")
        if self.company_id is None:
            raise ValueError("Cannot update object without a company_id")    
    
    def update(self, payload: dict[str, Any], **kwargs):
        if self.id is None:
            raise ValueError("Cannot update object without an id")
        payload = normalize_ipam_payload_for_save(payload)
        path = f"vlans/{self.id}"
        updated = self._client.put(path, self.id, payload, **kwargs)
        refreshed = self._client.get(path, paginate=False)
        if hasattr(refreshed, "_data"):
            self._data = dict(refreshed._data)
            return self
        if isinstance(refreshed, dict):
            self._data = dict(refreshed)
            return self
        return updated


class VLanZone(HuduObject):
    relation_type = "VlanZone"
    endpoint = HuduEndpoint.VLAN_ZONES

    def save(self, **kwargs):
        if self.id is None:
            raise ValueError("Cannot update object without an id")
        if self.company_id is None:
            raise ValueError("Cannot update object without a company_id")

    def update(self, payload: dict[str, Any], **kwargs):
        if self.id is None:
            raise ValueError("Cannot update object without an id")
        payload = normalize_ipam_payload_for_save(payload)
        path = f"vlan_zones/{self.id}"
        updated = self._client.put(path, self.id, payload, **kwargs)
        refreshed = self._client.get(path, paginate=False)
        if hasattr(refreshed, "_data"):
            self._data = dict(refreshed._data)
            return self
        if isinstance(refreshed, dict):
            self._data = dict(refreshed)
            return self
        return updated


class AssetPassword(HuduObject):
    relation_type = "AssetPassword"
    endpoint = HuduEndpoint.ASSET_PASSWORDS
    
    def to_folder(self, folder: int | HuduObject.password_folder):
        if self.id is None:
            raise ValueError("Cannot add password to folder without an id")
        if isinstance(folder, HuduObject):
            folder_id = folder.id
        elif isinstance(folder, int):
            folder_id = folder
        else:
            raise ValueError("folder must be an int or HuduObject")

        self.password_folder_id = folder_id
        return self.save()
    
    def save(self, **kwargs):
        if self.id is None:
            raise ValueError("Cannot save object without an id")
        company_id = self.company_id or self.get("company_id")
        if company_id is None:
            raise ValueError("AssetPassword save() requires company_id")

        payload = normalize_password_payload_for_save(self.to_dict())

        path = f"asset_passwords/{self.id}"
        updated = self._client.put(path, json={"asset_password": payload})
        refreshed = self._client.get(path, paginate=False)
        if hasattr(refreshed, "_data"):
            self._data = dict(refreshed._data)
        elif isinstance(refreshed, dict):
            refreshed = self._client._extract_primary_object(refreshed)
            self._data = dict(refreshed)

        return self

    def update(self, item_id: int | str, payload: dict[str, Any], **kwargs) -> Any:
        payload = normalize_password_payload_for_save(payload)
        return self.save(item_id, payload, **kwargs)

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

class PublicPhoto(HuduObject):
    def download(self, out_dir="."):
        return self._client.uploads.download(self.id, out_dir)


class Photo(HuduObject):
    def download(self, out_dir="."):
        return self._client.uploads.download(self.id, out_dir)


class Upload(HuduObject):
    def download(self, out_dir="."):
        return self._client.uploads.download(self.id, out_dir)


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
    HuduEndpoint.ASSET_PASSWORDS: AssetPassword,
    HuduEndpoint.ASSET_PASSWORDS_ID: AssetPassword,
    HuduEndpoint.PASSWORD_FOLDERS: Folder,
    HuduEndpoint.PASSWORD_FOLDERS_ID: Folder,
    HuduEndpoint.RELATIONS: Relation,
    HuduEndpoint.RELATIONS_ID: Relation,
    HuduEndpoint.PUBLIC_PHOTOS: PublicPhoto,
    HuduEndpoint.PUBLIC_PHOTOS_ID: PublicPhoto,
    HuduEndpoint.PHOTOS: Photo,
    HuduEndpoint.PHOTOS_ID: Photo,
    HuduEndpoint.UPLOADS: Upload,
    HuduEndpoint.UPLOADS_ID: Upload,
    HuduEndpoint.NETWORKS: Network,
    HuduEndpoint.NETWORKS_ID: Network,
    HuduEndpoint.IP_ADDRESSES: IPaddress,
    HuduEndpoint.IP_ADDRESSES_ID: IPaddress,
    HuduEndpoint.VLANS: VLan,
    HuduEndpoint.VLANS_ID: VLan,
    HuduEndpoint.VLAN_ZONES: VLanZone,
    HuduEndpoint.VLAN_ZONES_ID: VLanZone,
}
