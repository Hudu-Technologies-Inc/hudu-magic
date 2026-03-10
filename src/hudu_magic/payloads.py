from hudu_magic.endpoints import HuduEndpoint

RESOURCE_WRAPPERS = {
    "asset_layouts": "asset_layout",
    "companies": "company",
    "articles": "article",
    "folders": "folder",
    "websites": "website",
    "asset_passwords": "asset_password",
    "password_folders": "password_folder",
    "networks": "network",
    "vlans": "vlan",
    "vlan_zones": "vlan_zone",
    "rack_storages": "rack_storage",
    "photos": "photo",
    "uploads": "upload",
    "lists": "list",
    "flags": "flag",
    "flag_types": "flag_type",
    "procedures": "procedure",
    "procedure_tasks": "procedure_task",
    "relations": "relation",
    "assets": "asset",
    "asset_layouts_move_layout": "asset",
}

def maybe_wrap_payload(endpoint: HuduEndpoint | str, payload: dict) -> dict:
    if not isinstance(endpoint, HuduEndpoint):
        return payload

    wrapper = RESOURCE_WRAPPERS.get(endpoint.endpoint)
    if not wrapper:
        return payload

    if wrapper in payload:
        return payload

    return {wrapper: payload}