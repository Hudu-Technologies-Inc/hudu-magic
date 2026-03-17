from hudu_magic.endpoints import EndpointMeta, HuduEndpoint
from hudu_magic.constants import PROPERTIES_TO_POP_ON_SAVE, COMPANY_PROPERTIES_TO_POP_ON_SAVE, PASSWORD_PROPERTIES_TO_POP_ON_SAVE, WEBSITE_PROPERTIES_TO_POP_ON_SAVE, FOLDER_PROPERTIES_TO_POP_ON_SAVE, IPAM_PROPERTIES_TO_POP_ON_SAVE
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

def describe_single(endpoint: HuduEndpoint) -> str:
    return "\n\n".join([
        describe_get(endpoint),
        describe_create_update(endpoint),
        describe_delete(endpoint),
    ])

def endpoint_family_name(endpoint: HuduEndpoint) -> str:
    name = endpoint.name
    if name.endswith("_ID"):
        return name[:-3]
    return name

def get_related_endpoints(endpoint: HuduEndpoint) -> list[HuduEndpoint]:
    family_name = endpoint_family_name(endpoint)
    print(ep for ep in HuduEndpoint if endpoint_family_name(ep) == family_name)
    
    return [
        ep for ep in HuduEndpoint
        if endpoint_family_name(ep) == family_name
    ]

def describe(endpoint: HuduEndpoint) -> str:
    related = get_related_endpoints(endpoint)

    parts = []
    for ep in related:
        parts.append(describe_single(ep))

    return "\n\n".join(p for p in parts if p.strip())

def describe_get(endpoint: HuduEndpoint) -> str:
    meta = endpoint.meta if isinstance(endpoint, HuduEndpoint) else endpoint
    lines = [f"{meta.tag} ({endpoint.path})"]

    if meta.query_params:
        lines.append("Query params:")
        for name, meta in meta.query_params.items():
            req = "required" if meta.required else "optional"
            lines.append(f"  - {name}: {meta.type or 'any'} ({req})")
            if meta.description:
                lines.append(f"      {meta.description}")
    else:
        lines.append("No query params")

    return "\n".join(lines)

def describe_create_update(endpoint: HuduEndpoint) -> str:
    meta = endpoint.meta if isinstance(endpoint, HuduEndpoint) else endpoint
    lines = [f"{meta.tag} ({endpoint.path})"]

    if meta.supports_create:
        lines.append("Supports create")
    else:
        lines.append("Does not support create")
        
    if meta.supports_update:
        lines.append("Supports update")
    else:
        lines.append("Does not support update")

    if meta.create_fields or meta.update_fields:
        lines.append("Fields:")
        for name, meta in (meta.create_fields or meta.update_fields).items():
            req = "required" if meta.required else "optional"
            lines.append(f"  - {name}: {meta.type or 'any'} ({req})")
            if meta.description:
                lines.append(f"      {meta.description}")

    return "\n".join(lines)

def describe_delete(endpoint: HuduEndpoint) -> str:
    meta = endpoint.meta if isinstance(endpoint, HuduEndpoint) else endpoint
    lines = [f"{meta.tag} ({endpoint.path})"]

    if meta.supports_delete:
        lines.append("Supports delete")
    else:
        lines.append("Does not support delete")

    return "\n".join(lines)


def maybe_wrap_payload(endpoint: HuduEndpoint | str, payload: dict) -> dict:
    if not isinstance(endpoint, HuduEndpoint):
        return payload

    endpoint_key = endpoint.endpoint.replace("/{id}", "")
    wrapper = RESOURCE_WRAPPERS.get(endpoint_key)

    if not wrapper:
        return payload

    if wrapper in payload:
        return payload

    return {wrapper: payload}

def transform_asset_fields_for_save(fields):
    transformed = []

    for field in fields:
        if isinstance(field, dict):
            # GET-style field object
            if "label" in field:
                key = field["label"].replace(" ", "_").lower()
                transformed.append({key: field.get("value")})
                continue

            # already in write-shape
            if len(field) == 1:
                transformed.append(field)
                continue

        transformed.append(field)

    return transformed
def transform_custom_fields_for_save(fields):
    """
    Convert Hudu GET-style custom fields:
        [{"label": "Installed At", "value": None}, ...]
    into Hudu PUT/POST-style custom fields:
        [{"Installed At": None}, ...]
    """
    if not isinstance(fields, list):
        return fields

    transformed = []

    for field in fields:
        if isinstance(field, dict):
            # already in write-shape like {"Installed At": None}
            if "label" not in field and "value" not in field and len(field) == 1:
                transformed.append(field)
                continue

            label = field.get("label")
            value = field.get("value")

            if label is not None:
                transformed.append({label: value})
                continue

        transformed.append(field)
    return transformed


def clean_payload(payload: dict) -> dict:
    return {
        k: v
        for k, v in payload.items()
        if k not in PROPERTIES_TO_POP_ON_SAVE and v is not None
    }


def normalize_asset_payload_for_save(data: dict) -> dict:
    allowed = {
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

    payload = {k: v for k, v in data.items() if k in allowed and v is not None}

    if "fields" in data and "custom_fields" not in payload:
        payload["custom_fields"] = transform_asset_fields_for_save(
            data["fields"]
            )
    return payload


def normalize_company_payload_for_save(data: dict) -> dict:
    return {k: v for k, v in data.items() 
            if k not in COMPANY_PROPERTIES_TO_POP_ON_SAVE and v is not None}


def normalize_password_payload_for_save(data: dict) -> dict:
    return {k: v for k, v in data.items() 
            if k not in PASSWORD_PROPERTIES_TO_POP_ON_SAVE and v is not None}


def normalize_website_payload_for_save(data: dict) -> dict:
    return {k: v for k, v in data.items() 
            if k not in WEBSITE_PROPERTIES_TO_POP_ON_SAVE and v is not None}


def normalize_folder_payload_for_save(data: dict) -> dict:
    return {k: v for k, v in data.items() 
            if k not in FOLDER_PROPERTIES_TO_POP_ON_SAVE and v is not None}


def normalize_ipam_payload_for_save(data: dict) -> dict:
    return {k: v for k, v in data.items() 
            if k not in IPAM_PROPERTIES_TO_POP_ON_SAVE and v is not None}
