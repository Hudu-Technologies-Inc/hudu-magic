from enum import Enum
from .helpers.general import strip_string

class HuduEndpoint(Enum):
    ACTIVITYLOGS = ("activity_logs", True, [])
    APIINFO = ("api_info", False, [])

    ARTICLES = ("articles", True, [
        "content", "name", "enable_sharing", "folder_id", "company_id", "slug"
    ])

    ASSETS = ("assets", True, [
        "name", "asset_layout_id", "primary_serial", "primary_mail",
        "primary_model", "primary_manufacturer", "slug", "custom_fields"
    ])

    ASSETLAYOUTS = ("asset_layouts", True, [
        "name", "icon", "color", "icon_color", "active",
        "include_passwords", "include_photos", "include_comments",
        "include_files", "password_types", "fields"
    ])

    ASSETPASSWORDS = ("asset_passwords", True, [
        "password", "name", "company_id", "passwordable_type",
        "passwordable_id", "in_portal", "otp_secret", "url",
        "username", "description", "password_type",
        "password_folder_id", "slug"
    ])

    CARDSLOOKUP = ("cards/lookup", False, [
        "integration_slug", "integration_id", "integration_identifier"
    ])

    CARDSJUMP = ("cards/jump", False, [
        "integration_type", "integration_slug", "integration_id", "integration_identifier"
    ])

    COMPANIES = ("companies", True, [
        "name", "nickname", "company_type", "address_line_1",
        "address_line_2", "city", "state", "zip", "country_name",
        "phone_number", "fax_number", "website", "id_number",
        "parent_company_id", "notes", "slug"
    ])

    COMPANIESJUMP = ("companies/jump", False, [
        "integration_slug"
    ])

    EXPIRATIONS = ("expirations", True, [
        "archived"
    ])

    EXPORTS = ("exports", False, [
        "format", "company_id", "include_passwords", "include_websites",
        "include_articles", "include_archived_articles",
        "include_archived_passwords", "include_archived_websites",
        "include_archived_assets", "asset_layout_ids", "download"
    ])

    S3EXPORTS = ("s3_exports", False, [])

    FLAGTYPES = ("flag_types", True, [
        "name", "color", "slug"
    ])

    FLAGS = ("flags", True, [
        "flag_type_id", "description", "flagable_type", "flagable_id"
    ])

    FOLDERS = ("folders", True, [
        "name", "icon", "description", "parent_folder_id",
        "company_id", "folder_type"
    ])

    GROUPS = ("groups", True, [])

    IPADDRESSES = ("ip_addresses", False, [
        "address", "status", "fqdn", "description", "notes",
        "asset_id", "network_id", "company_id", "skip_dns_validation"
    ])

    LISTS = ("lists", False, [
        "name", "list_items_attributes"
    ])

    MAGICDASH = ("magic_dash", True, [
        "message", "company_name", "title", "icon",
        "image_url", "content_link", "content", "shade"
    ])

    MATCHERS = ("matchers", True, [])

    NETWORKS = ("networks", False, [
        "id", "name", "address", "network_type", "slug",
        "company_id", "location_id", "description", "vlan_id",
        "archived", "created_at", "updated_at"
    ])

    PASSWORDFOLDERS = ("password_folders", True, [
        "name", "company_id", "description", "security", "allowed_groups"
    ])

    PHOTOS = ("photos", True, [
        "file", "caption", "company_id", "photoable_type",
        "photoable_id", "folder_id", "pinned", "archived"
    ])

    PROCEDURETASKS = ("procedure_tasks", False, [
        "name", "description", "completed", "procedure_id",
        "position", "user_id", "due_date", "priority", "assigned_users"
    ])

    PROCEDURES = ("procedures", True, [
        "name", "description", "company_id", "company_template", "asset_id"
    ])

    PROCEDURESCREATEFROMTEMPLATE = ("procedures/{id}/create_from_template", False, [
        "company_id", "name", "description"
    ])

    PROCEDURESDUPLICATE = ("procedures/{id}/duplicate", False, [
        "company_id", "name", "description"
    ])

    PROCEDURESKICKOFF = ("procedures/{id}/kickoff", False, [
        "asset_id", "name"
    ])

    PUBLICPHOTOS = ("public_photos", True, [
        "id", "numeric_id", "url", "record_type", "record_id", "photo"
    ])

    RACKSTORAGES = ("rack_storages", False, [
        "id", "company_id", "location_id", "name", "description",
        "max_wattage", "starting_unit", "height", "width",
        "created_at", "updated_at", "discarded_at"
    ])

    RACKSTORAGEITEMS = ("rack_storage_items", False, [
        "id", "company_id", "rack_storage_role_id", "asset_id",
        "start_unit", "end_unit", "status", "side", "max_wattage",
        "power_draw", "rack_storage_role_name", "reserved_message",
        "rack_storage_role_description", "rack_storage_role_hex_color",
        "asset_name", "asset_url", "url"
    ])

    RELATIONS = ("relations", True, [
        "toable_id", "toable_type", "fromable_id", "fromable_type",
        "description", "is_inverse"
    ])

    UPLOADS = ("uploads", True, [
        "file", "uploadable_id", "uploadable_type"
    ])

    USERS = ("users", True, [])

    VLANZONES = ("vlan_zones", False, [
        "name", "description", "vlan_id_ranges", "company_id", "archived"
    ])

    VLANS = ("vlans", False, [
        "name", "vlan_id", "description", "notes", "company_id",
        "vlan_zone_id", "status_list_item_id", "role_list_item_id", "archived"
    ])

    WEBSITES = ("websites", True, [
        "company_id", "name", "notes", "paused",
        "disable_dns", "disable_ssl", "disable_whois", "slug"
    ])

    def __init__(self, uri, is_paginated, fields):
        self.endpoint = uri
        self.is_paginated = is_paginated
        self.fields = fields

    @property
    def path(self):
        return f"/{self.endpoint}"

    def item_path(self, item_id):
        if "{id}" in self.endpoint:
            return f"/{self.endpoint.replace('{id}', str(item_id))}"
        return f"/{self.endpoint}/{item_id}"

    def archive_path(self, item_id):
        return f"{self.item_path(item_id)}/archive"

    def unarchive_path(self, item_id):
        return f"{self.item_path(item_id)}/unarchive"
