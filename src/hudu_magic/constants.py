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
    "id",
    "created_on",
    "updated_on",
    "created_by",
    "updated_by",
    "slug",
    "asset_type",
    "object_type",
    "company_name",
}