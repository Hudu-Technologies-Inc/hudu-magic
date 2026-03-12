ASSET_LAYOUT_ALLOWED_FIELDS = ["label", "field_type", "required", "show_in_list", "position"]

FROMABLE_TOABLE_TYPES = {
    "RackStorage": "rack_storages",
    "Password": "asset_passwords",
    "Asset": "assets",
    "IpAddress": "ip_addresses",
    "Network": "networks",
}

TOABLE_FROMABLE_TYPES = {v: k for k, v in FROMABLE_TOABLE_TYPES.items()}

MATCH_FOUND_OPTIONS = [
    "always ask me if matching",
    "always skip import if matching (keep dest data)",
    "always overwrite destination if matching (keep source data)",
    "auto-select more-recent last updated date (keep most-recent)",
    "auto-select earlier created-on date (keep)",
    "ask me after each type of item.",
]

FIELD_TYPES = [
    "Text",
    "Number",
    "CheckBox",
    "Website",
    "AssetTag",
    "Email",
    "Phone",
    "Date",
    "RichText",
    "Heading",
    "Password"
]

NESTED_FIELD_TYPES=[
    "ListSelect"
]

PROPERTIES_TO_POP_ON_SAVE = {
    "created_on",
    "updated_on",
    "created_by",
    "updated_by",
    "slug",
    "asset_type",
    "object_type",
    "company_name",
    "archived",
    "url",
    "cards",
    "radar_id",
}

ASSET_PROPERTIES_TO_KEEP_ON_SAVE = {
    "name",
    "asset_layout_id",
    "company_id",
    "slug",
    "primary_serial",
    "primary_model",
    "primary_mail",
    "primary_manufacturer",
    "custom_fields",
}

COMPANY_PROPERTIES_TO_POP_ON_SAVE = {
    "slug",
    "parent_company_name",
    "archived",
    "url",
    "full_url",
    "passwords_url",
    "knowledge_base_url",
    "created_at",
    "updated_at",
    "discarded_at",    
    "integrations",
}

PASSWORD_PROPERTIES_TO_POP_ON_SAVE = {
    "slug",
    "password_folder_name",
    "url",
    "archived",
    "created_at",
    "updated_at",
    "discarded_at",    
    }

WEBSITE_PROPERTIES_TO_POP_ON_SAVE = {
    "code",
    "message",
    "keyword",
    "monitor_type",
    "status",
    "monitoring_status",
    "refreshed_at",
    "monitored_at",
    "slug",
    "headers",
    "account_id",
    "asset_field_id",
    "created_at",
    "updated_at",    
    "discarded_at",
    "cloudflare_details",
    "potentially_proxied",
    "icon",
    "asset_type",
    "company_name",
    "object_type",
    "sent_notifications",
    
}

FOLDER_PROPERTIES_TO_POP_ON_SAVE = {
    "slug",
    "folder_type",
    "updated_at",
    "created_at",
    "discarded_at",    
    "archived",
    "url",
    "object_type",    
    "icon",
}

IPAM_PROPERTIES_TO_POP_ON_SAVE = {
    "asset_url",
    "asset_id",
    "asset_name",
    "fqdn",
    "object_type",
    "created_at",
    "updated_at",
    "discarded_at",
}

TRUTHY_VALUES = {"true", "1", "yes", "y", "on", "t"}
FALSY_VALUES  = {"false", "0", "no", "n", "off", "f", "", "none", "null"}
