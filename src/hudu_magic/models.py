from __future__ import annotations

from pathlib import Path
from typing import Any

from typing_extensions import Self

from hudu_magic.help import describe_endpoint
from hudu_magic.helpers.general import is_zero_percent

from .endpoints import HuduEndpoint
from .payloads import (
    clean_payload,
    normalize_asset_payload_for_save,
    normalize_company_payload_for_save,
    normalize_password_payload_for_save,
    normalize_website_payload_for_save,
    normalize_folder_payload_for_save,
    normalize_ipam_payload_for_save,
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

    def _require_id(self) -> int | str:
        if self.id is None:
            raise ValueError(f"Cannot use {self.__class__.__name__} without an id")
        return self.id

    def _require_company_id(self) -> int | str:
        if self.company_id is None:
            raise ValueError(
                f"Cannot use {self.__class__.__name__} without a company id"
            )
        return self.company_id

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

    def help(self) -> str:
        return "\n".join(describe_endpoint(self._endpoint))

    def get(self, key, default=None):
        return self._data.get(key, default)

    def values(self):
        return self._data.values()

    def archive(self):
        return self._client.archive(endpoint=self._endpoint, item_id=self.id)

    def unarchive(self):
        return self._client.unarchive(endpoint=self._endpoint, item_id=self.id)

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
        self._require_id()
        update_endpoint = getattr(self.__class__, "update_endpoint", self._endpoint)

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
        return self._client.delete(self._client.resolve_path(self._endpoint, self.id))

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

    def list_photos(self, **params) -> HuduCollection:
        if self.id is None:
            raise ValueError("Cannot list photos without a company id")
        return self._client.photos.list_photos(to_object=self, **params)

    def list_uploads(self):
        self.to_upload_ref()
        return self._client.uploads.list_uploads(to_object=self)

    def list_relations(self):
        self.to_relation_ref()
        return self._client.relations.list_relations(to_object=self)

    @classmethod
    def fetch(cls, client, item_id: int | str | None = None, **params):
        if not cls.resource_attr:
            raise NotImplementedError(f"{cls.__name__} does not define resource_attr")

        resource = getattr(client, cls.resource_attr)

        if hasattr(item_id, "id"):
            item_id = item_id.id

        if item_id is None:
            return resource.list(**params)

        return resource.get(item_id)

    @classmethod
    def get_all(cls, client, **params):
        return cls.fetch(client, **params)

    @classmethod
    def get_by_id(cls, client, item_id: int | str):
        return cls.fetch(client, item_id)


class Company(HuduObject):
    endpoint = HuduEndpoint.COMPANIES
    relation_type = "Company"
    resource_upl_type = "Company"
    resource_photo_type = "Company"

    def _create_company_resource(
        self,
        resource_name: str,
        payload: dict[str, Any] | None = None,
        **kwargs,
    ):
        merged = dict(payload or {})
        if kwargs:
            merged.update(kwargs)

        resource = getattr(self._client, resource_name)
        return resource.create(company_id=self._require_id(), payload=merged)

    def _list_company_resource(self, resource_name: str, **params) -> HuduCollection:
        resource = getattr(self._client, resource_name)
        return resource.list(company_id=self._require_id(), **params)

    def create_asset(self, payload: dict[str, Any] | None = None, **kwargs) -> Asset:
        merged = dict(payload or {})
        if kwargs:
            merged.update(kwargs)

        return self._client.assets.create(
            company_id=self._require_id(),
            payload=merged,
        )

    def create_article(
        self, payload: dict[str, Any] | None = None, **kwargs
    ) -> Article:
        return self._create_company_resource("articles", payload, **kwargs)

    def create_password(
        self, payload: dict[str, Any] | None = None, **kwargs
    ) -> AssetPassword:
        return self._create_company_resource("asset_passwords", payload, **kwargs)

    def create_procedure(
        self, payload: dict[str, Any] | None = None, **kwargs
    ) -> Procedure:
        return self._create_company_resource("procedures", payload, **kwargs)

    def create_website(
        self, payload: dict[str, Any] | None = None, **kwargs
    ) -> Website:
        return self._create_company_resource("websites", payload, **kwargs)

    # List Items for Company
    def list_assets(self, **params) -> HuduCollection:
        return self._list_company_resource("assets", **params)

    def list_articles(self, **params) -> HuduCollection:
        return self._list_company_resource("articles", **params)

    def list_passwords(self, **params) -> HuduCollection:
        return self._list_company_resource("asset_passwords", **params)

    def list_procedures(self, **params) -> HuduCollection:
        return self._list_company_resource("procedures", **params)

    def list_websites(self, **params) -> HuduCollection:
        return self._list_company_resource("websites", **params)

    def list_folders(self, **params) -> HuduCollection:
        return self._list_company_resource("folders", **params)

    def list_password_folders(self, **params) -> HuduCollection:
        return self._list_company_resource("password_folders", **params)

    def list_photos(self, **params) -> HuduCollection:
        self._require_id()
        return self._client.photos.list_photos(to_object=self, **params)

    # Other company-specific actions
    def save(self, **kwargs):
        if self.id is None:
            raise ValueError("Cannot save object without an id")

        payload = normalize_company_payload_for_save(self.to_dict())
        path = f"companies/{self._require_id()}"
        self._client.put(path, json=payload)
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

    def add_public_photo(self, file_path: str | Path) -> PublicPhoto:
        return self._client.public_photos.create(
            file_path=file_path,
            to_object=self,
        )

    def to_folder(self, folder: int | HuduObject) -> Self:
        if self.id is None:
            raise ValueError("Cannot add article to folder without an id")
        if isinstance(folder, HuduObject):
            folder_id = folder.id
        elif isinstance(folder, int):
            folder_id = folder
        else:
            raise ValueError("folder must be an int or HuduObject")

        self._data["folder_id"] = folder_id
        return self.save()

    def save(self, **kwargs) -> Self:
        if self.id is None:
            raise ValueError("Cannot save object without an id")

        payload = clean_payload(self.to_dict())

        path = f"articles/{self.id}"
        self._client.put(path, json=payload)
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

    def update(self, payload: dict[str, Any] | None = None, **kwargs) -> Self:
        if self.id is None:
            raise ValueError("Cannot update object without an id")
        if self.company_id is None:
            raise ValueError("Cannot update object without a company id")

        merged = dict(payload or {})
        if kwargs:
            merged.update(kwargs)

        merged = normalize_asset_payload_for_save(merged)

        updated = self._client.assets.update(
            item_id=self.id,
            company_id=self.company_id,
            payload=merged,
        )

        if isinstance(updated, HuduObject):
            self._data = dict(updated._data)
        elif isinstance(updated, dict):
            self._data = dict(updated)

        return self

    def get(self, key, default=None) -> Any:

        return self._data.get(key, default)

    def archive(self) -> Any:
        return self._client.assets.archive(
            item_id=self._require_id(),
            company_id=self._require_company_id(),
        )

    def unarchive(self) -> Any:
        return self._client.assets.unarchive(
            item_id=self._require_id(),
            company_id=self._require_company_id(),
        )

    def delete(self) -> Any:
        return self._client.assets.delete(
            item_id=self._require_id(),
            company_id=self._require_company_id(),
        )

    def get_path(self) -> str:
        company_id = self._require_company_id()
        return f"companies/{company_id}/assets/{self._require_id()}"

    def to_pubphoto_ref(self) -> str:
        id = self._require_id()
        if not hasattr(self, "resource_pubphoto_type"):
            raise ValueError(
                f"{self.__class__.__name__} with ID {id} not public photoable"
            )

        return self.resource_pubphoto_type

    def add_public_photo(self, file_path: str | Path) -> PublicPhoto:
        return self._client.public_photos.create(
            file_path=file_path,
            to_object=self,
        )

    def save(self, **kwargs) -> Self:
        if self.id is None:
            raise ValueError("Cannot save object without an id")

        payload = normalize_asset_payload_for_save(self.to_dict())
        path = self.get_path()
        self._client.put(path, json={"asset": payload})
        refreshed = self._client.get(path, paginate=False)
        if hasattr(refreshed, "_data"):
            self._data = dict(refreshed._data)
        elif isinstance(refreshed, dict):
            refreshed = self._client._extract_primary_object(refreshed)
            self._data = dict(refreshed)

        return self

    def list_for_company(
        self, company: int | str | HuduObject | None = None, **params
    ) -> HuduCollection:
        if isinstance(company, HuduObject):
            company_id = company.id
        elif company is None:
            company_id = self.company_id
        else:
            company_id = company

        if company_id is None:
            raise ValueError("Cannot list assets without a company id")

        return self._client.assets.list(company_id=company_id, **params)

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

        payload = {
            "relation": {
                "from_type": fromable._endpoint,
                "from_id": fromable.id,
                "to_type": toable._endpoint,
                "to_id": toable.id,
            }
        }
        return self._client.post(self._endpoint, payload, **kwargs)


class Folder(HuduObject):
    def save(self, **kwargs):
        if self.id is None:
            raise ValueError("Cannot save object without an id")

        payload = normalize_folder_payload_for_save(self.to_dict())

        path = f"folders/{self.id}"
        self._client.put(path, json=payload)
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

    @property
    def tasks(self) -> list:
        return self._data.get("procedure_tasks_attributes", [])

    @property
    def is_run(self) -> bool:
        return is_zero_percent(
            self._data.get("completion_percentage", 0)
            ) is False

    def kick_off(self):
        if self.id is None:
            raise ValueError("Cannot kick off procedure without an id")
        if self.is_run:
            raise ValueError(
                "Cannot kick off procedure that has already started"
                )
        path = f"procedures/{self.id}/kickoff"
        return self._client.post(path)

# aliases
    @property
    def procedure_tasks(self) -> list:
        return self.tasks
    
    def list_tasks(self) -> list:
        return self.tasks
    
    def kickoff(self):
        return self.kick_off()


class ProcedureTasks(HuduObject):
    endpoint = HuduEndpoint.PROCEDURE_TASKS
    resource_attr = "procedure_tasks"

    @property
    def procedure(self) -> Procedure:
        return self._client.procedures.get(self.procedure_id)


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
        self._client.put(path, json=payload)
        refreshed = self._client.get(path, paginate=False)
        if hasattr(refreshed, "_data"):
            self._data = dict(refreshed._data)
        elif isinstance(refreshed, dict):
            refreshed = self._client._extract_primary_object(refreshed)
            self._data = dict(refreshed)
        return self


class AssetLayout(HuduObject):
    endpoint = HuduEndpoint.ASSET_LAYOUTS
    resource_attr = "asset_layouts"


class PasswordFolder(HuduObject):
    def save(self, **kwargs):
        if self.id is None:
            raise ValueError("Cannot save object without an id")

        company_id = self.company_id or self.get("company_id")
        if company_id is None:
            raise ValueError("PasswordFolder save() requires company_id")

        payload = normalize_password_payload_for_save(self.to_dict())
        if payload.get("security") is None:
            payload["security"] = "all_users"

        path = f"companies/{company_id}/password_folders/{self.id}"
        self._client.put(path, json={"password_folder": payload})

        refreshed = self._client.get(path, paginate=False)
        if hasattr(refreshed, "_data"):
            self._data = dict(refreshed._data)
        elif isinstance(refreshed, dict):
            refreshed = self._client._extract_primary_object(refreshed)
            self._data = dict(refreshed)

        return self

    def add_passwords(self, password: int | HuduObject | list[int] | list[HuduObject]):
        if self.id is None:
            raise ValueError("Cannot add password to folder without an id")
        if password is None:
            raise ValueError("Must provide password_id to add_password")

        if isinstance(password, list):
            for p in password:
                self.add_passwords(p)
            return True

        if isinstance(password, HuduObject):
            return password.to_folder(self.id)

        if isinstance(password, int):
            pw = self._client.asset_passwords.get(password)
            return pw.to_folder(self.id)

        raise ValueError("password must be an int, HuduObject, or list of those")


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

    def to_folder(self, folder: int | PasswordFolder):
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
        self._client.put(path, json={"asset_password": payload})
        refreshed = self._client.get(path, paginate=False)
        if hasattr(refreshed, "_data"):
            self._data = dict(refreshed._data)
        elif isinstance(refreshed, dict):
            refreshed = self._client._extract_primary_object(refreshed)
            self._data = dict(refreshed)

        return self

    def update(self, payload: dict[str, Any], **kwargs):
        if self.id is None:
            raise ValueError("Cannot update object without an id")

        payload = normalize_password_payload_for_save(payload)
        updated = self._client.update(self._endpoint, self.id, payload, **kwargs)

        if isinstance(updated, HuduObject):
            self._data = dict(updated._data)
            return self
        if isinstance(updated, dict):
            self._data = dict(updated)
            return self
        return updated


class Exports(HuduObject):
    endpoint = HuduEndpoint.EXPORTS
    resource_attr = "exports"


class S3Exports(HuduObject):
    endpoint = HuduEndpoint.S3_EXPORTS
    resource_attr = "s3_exports"
    
    def get(self) -> None:
        raise NotImplementedError("S3Exports does not support get()")


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
    HuduEndpoint.EXPORTS: Exports,
    HuduEndpoint.S3_EXPORTS: S3Exports,
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
    HuduEndpoint.PASSWORD_FOLDERS: PasswordFolder,
    HuduEndpoint.PASSWORD_FOLDERS_ID: PasswordFolder,
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
    def __getattr__(self, name: str):
        if not self:
            raise AttributeError(name)

        sample = getattr(self[0], name, None)
        if sample is None:
            raise AttributeError(name)

        if callable(sample):

            def caller(*args, flatten: bool = False, unique: bool = False, **kwargs):
                results = []

                for obj in self:
                    method = getattr(obj, name)
                    value = method(*args, **kwargs)

                    if flatten and isinstance(
                        value, (list, HuduCollection, tuple, set)
                    ):
                        results.extend(value)
                    else:
                        results.append(value)

                if unique:
                    deduped = []
                    seen = set()

                    for item in results:
                        if isinstance(item, HuduObject):
                            key = (item.__class__.__name__, item.id)
                        else:
                            key = repr(item)

                        if key not in seen:
                            seen.add(key)
                            deduped.append(item)

                    results = deduped

                if results and all(isinstance(x, HuduObject) for x in results):
                    return HuduCollection(results)

                return results

            return caller

        return [getattr(obj, name, None) for obj in self]

    def first(self):
        return self[0] if self else None

    def ids(self):
        return [obj.id for obj in self if getattr(obj, "id", None) is not None]

    def to_dicts(self):
        return [obj.to_dict() if hasattr(obj, "to_dict") else obj for obj in self]

    def filter(self, **criteria):
        def matches(obj):
            return all(
                getattr(obj, key, None) == value for key, value in criteria.items()
            )

        return HuduCollection([obj for obj in self if matches(obj)])
