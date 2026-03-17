from __future__ import annotations

from pathlib import Path
from typing import Any

from .endpoints import HuduEndpoint
from .payloads import (clean_payload, normalize_asset_payload_for_save,
                       normalize_company_payload_for_save,
                       normalize_password_payload_for_save,
                       normalize_website_payload_for_save,
                       normalize_folder_payload_for_save,
                       normalize_ipam_payload_for_save
                       )
from .validation import (
    HuduValidationError,
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
    
    def archive(self):
        return self._client.archive(self.id)
    
    def unarchive(self):
        return self._client.unarchive(self.id)

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

    def relate_to(self, other: "HuduObject", is_inverse: bool = False):
        if self.id is None or other.id is None:
            raise ValueError("Both objects in a relation must have an id")
        if not self.relation_type or not other.relation_type:
            raise ValueError(
                "Both objects in a relation must have a relation_type [making them relateable]"
                )
        
        return self._client.relations.create(
            self,
            other,
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

    def to_upload_ref(self) -> str:
        if self.id is None:
            raise ValueError(f"{self.__class__.__name__} has no id")
        if not hasattr(self, "resource_upl_type"):
            raise ValueError(f"{self.__class__.__name__} not uploadable")

        return self.resource_upl_type

    def to_photo_ref(self) -> str:
        if self.id is None:
            raise ValueError(f"{self.__class__.__name__} has no id")
        if not hasattr(self, "resource_photo_type"):
            raise ValueError(f"{self.__class__.__name__} not photoable")

        return self.resource_photo_type

    @property
    def id(self):
        return self._data.get("id")
    
    @property
    def company_id(self):
        return self._data.get("company_id")

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

    def upload_to(self, file_path: str | Path):
        if not hasattr(self, "resource_upl_type"):
            raise ValueError(f"{self.__class__.__name__} not uploadable")
        return self._client.uploads.create(
            file_path=file_path,
            to_object=self,
        )

    def add_photo(self, file_path: str | Path, caption: str | None = None):
        if not hasattr(self, "resource_photo_type"):
            raise ValueError(f"{self.__class__.__name__} not photoable")
        return self._client.photos.create(
            file_path=file_path,
            to_object=self,
            caption=caption,
        )


    def list_photos(self, **params):
        if not hasattr(self, "resource_photo_type"):
            raise ValueError(f"{self.__class__.__name__} not photoable")
        return self._client.photos.list_photos(to_object=self, **params)

    def list_uploads(self):
        self.to_upload_ref()
        return self._client.uploads.list_uploads(to_object=self)


    def list_relations(self):
        self.to_relation_ref()
        return self._client.relations.list_relations(to_object=self)

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
    endpoint = HuduEndpoint.COMPANIES
    relation_type = "Company"
    resource_upl_type = "Company"
    resource_photo_type = "Company"
    
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
    resource_upl_type = "Article"
    resource_pubphoto_type = "Article"
    resource_photo_type = "Article"

    def to_pubphoto_ref(self) -> str:
        if self.id is None:
            raise ValueError(f"{self.__class__.__name__} has no id")
        if not hasattr(self, "resource_pubphoto_type"):
            raise ValueError(f"{self.__class__.__name__} not public photoable")

        return self.resource_pubphoto_type

    def add_public_photo(self, file_path: str | Path):
        return self._client.public_photos.create(
            file_path=file_path,
            to_object=self,
        )
    
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
    resource_upl_type = "Asset"
    resource_pubphoto_type = "Asset"
    resource_photo_type = "Asset"
    endpoint = HuduEndpoint.ASSETS

    def to_pubphoto_ref(self) -> str:
        if self.id is None:
            raise ValueError(f"{self.__class__.__name__} has no id")
        if not hasattr(self, "resource_pubphoto_type"):
            raise ValueError(f"{self.__class__.__name__} not public photoable")

        return self.resource_pubphoto_type

    def add_public_photo(self, file_path: str | Path):
        return self._client.public_photos.create(
            file_path=file_path,
            to_object=self,
        )

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


class Procedure(HuduObject):
    relation_type = "Procedure"
    resource_upl_type = "Procedure"
    endpoint = HuduEndpoint.PROCEDURES


class Website(HuduObject):
    relation_type = "Website"
    resource_upl_type = "Website"
    endpoint = HuduEndpoint.WEBSITES

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
    resource_upl_type = "Network"    
    endpoint = HuduEndpoint.NETWORKS


class IPaddress(HuduObject):
    relation_type = "IpAddress"
    resource_upl_type = "IpAddress"
    resource_photo_type = "IPAddress"

    endpoint = HuduEndpoint.IP_ADDRESSES


class VLan(HuduObject):
    relation_type = "Vlan"
    resource_upl_type = "Vlan"
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
    resource_upl_type = "VlanZone"
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
    resource_upl_type = "AssetPassword"
    resource_photo_type = "AssetPassword"
    
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


class Photo(HuduObject):
    endpoint = HuduEndpoint.PHOTOS
    resource_attr = "photos"

    def download(self, out_dir="."):
        return self._client.photos.download(self, out_dir)


class PublicPhoto(HuduObject):
    endpoint = HuduEndpoint.PUBLIC_PHOTOS
    resource_attr = "public_photos"

    def download(self, out_dir="."):
        return self._client.public_photos.download(self, out_dir)


class Upload(HuduObject):
    endpoint = HuduEndpoint.UPLOADS
    resource_attr = "uploads"

    def download(self, out_dir="."):
        return self._client.uploads.download(self, out_dir)


class Users(HuduObject):
    endpoint = HuduEndpoint.USERS
    resource_attr = "users"


class Procedures(HuduObject):
    endpoint = HuduEndpoint.PROCEDURES
    resource_attr = "procedures"


class ProcedureTasks(HuduObject):
    endpoint = HuduEndpoint.PROCEDURE_TASKS
    resource_attr = "procedure_tasks"
    


class Groups(HuduObject):
    endpoint = HuduEndpoint.GROUPS
    resource_attr = "groups"


class Lists(HuduObject):
    endpoint = HuduEndpoint.LISTS
    resource_attr = "lists"


class Expirations(HuduObject):
    endpoint = HuduEndpoint.EXPIRATIONS
    resource_attr = "expirations"


class ActivityLogs(HuduObject):
    endpoint = HuduEndpoint.ACTIVITY_LOGS
    resource_attr = "activity_logs"


class Flags(HuduObject):
    endpoint = HuduEndpoint.FLAGS
    resource_attr = "flags"


class FlagTypes(HuduObject):
    endpoint = HuduEndpoint.FLAG_TYPES
    resource_attr = "flag_types"


class MagicDashes(HuduObject):
    endpoint = HuduEndpoint.MAGIC_DASH
    resource_attr = "magic_dashes"


class RackStorage(HuduObject):
    relation_type = "RackStorage"
    resource_upl_type = "RackStorage"
    resource_photo_type = "RackStorage"
    resource_pubphoto_type = "RackStorage"
    endpoint = HuduEndpoint.RACK_STORAGES


class RackstorageItems(HuduObject):
    endpoint = HuduEndpoint.RACK_STORAGE_ITEMS
    resource_attr = "rack_storage_items"


class Cards(HuduObject):
    endpoint = HuduEndpoint.CARDS_LOOKUP
    resource_attr = "card"


MODEL_MAP = {
    HuduEndpoint.ACTIVITY_LOGS: ActivityLogs,
    HuduEndpoint.ASSET_LAYOUTS: AssetLayout,
    HuduEndpoint.ASSET_LAYOUTS_ID: AssetLayout,
    HuduEndpoint.ASSET_PASSWORDS: AssetPassword,
    HuduEndpoint.ASSET_PASSWORDS_ID: AssetPassword,
    HuduEndpoint.ARTICLES: Article,
    HuduEndpoint.ARTICLES_ID: Article,
    HuduEndpoint.ASSETS: Asset,
    HuduEndpoint.CARDS_LOOKUP: Cards,
    HuduEndpoint.CARDS_JUMP: Cards,
    HuduEndpoint.COMPANIES: Company,
    HuduEndpoint.COMPANIES_ID: Company,
    HuduEndpoint.IP_ADDRESSES: IPaddress,
    HuduEndpoint.IP_ADDRESSES_ID: IPaddress,
    HuduEndpoint.GROUPS: Groups,
    HuduEndpoint.EXPIRATIONS: Expirations,
    HuduEndpoint.EXPIRATIONS_ID: Expirations,
    HuduEndpoint.FLAGS: Flags,
    HuduEndpoint.FLAGS_ID: Flags,
    HuduEndpoint.LISTS: Lists,
    HuduEndpoint.LISTS_ID: Lists,
    HuduEndpoint.FLAG_TYPES: FlagTypes,
    HuduEndpoint.FOLDERS: Folder,
    HuduEndpoint.FOLDERS_ID: Folder,
    HuduEndpoint.GROUPS: Groups,
    HuduEndpoint.GROUPS_ID: Groups,
    HuduEndpoint.MAGIC_DASH: MagicDashes,
    HuduEndpoint.MAGIC_DASH_ID: MagicDashes,
    HuduEndpoint.NETWORKS: Network,
    HuduEndpoint.NETWORKS_ID: Network,
    HuduEndpoint.PASSWORD_FOLDERS: Folder,
    HuduEndpoint.PASSWORD_FOLDERS_ID: Folder,
    HuduEndpoint.PROCEDURES: Procedure,
    HuduEndpoint.PROCEDURE_TASKS: ProcedureTasks,
    HuduEndpoint.PROCEDURE_TASKS_ID: ProcedureTasks,
    HuduEndpoint.RELATIONS_ID: Relation,
    HuduEndpoint.PHOTOS: Photo,
    HuduEndpoint.PHOTOS_ID: Photo,
    HuduEndpoint.PUBLIC_PHOTOS: PublicPhoto,
    HuduEndpoint.PUBLIC_PHOTOS_ID: PublicPhoto,
    HuduEndpoint.RACK_STORAGES: RackStorage,
    HuduEndpoint.RACK_STORAGES_ID: RackStorage,
    HuduEndpoint.RACK_STORAGE_ITEMS: RackstorageItems,
    HuduEndpoint.RACK_STORAGE_ITEMS_ID: RackstorageItems,
    HuduEndpoint.RELATIONS: Relation,
    HuduEndpoint.UPLOADS: Upload,
    HuduEndpoint.UPLOADS_ID: Upload,
    HuduEndpoint.USERS: Users,
    HuduEndpoint.VLANS: VLan,
    HuduEndpoint.VLANS_ID: VLan,
    HuduEndpoint.VLAN_ZONES: VLanZone,
    HuduEndpoint.VLAN_ZONES_ID: VLanZone,
    HuduEndpoint.WEBSITES: Website,
    HuduEndpoint.WEBSITES_ID: Website,
}


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
