"""
Helpers for building ``POST /asset_layouts`` bodies from GET-style layout payloads.

These are separate from :func:`hudu_magic.payloads.transform_asset_fields_for_save`,
which targets **asset** custom field values on save, not asset **layout** definitions.
"""

from __future__ import annotations

from typing import Any, Iterable

from hudu_magic.constants import (
    ASSET_LAYOUT_CREATE_DEFAULTS,
    ASSET_LAYOUT_FIELD_READ_ONLY_KEYS,
    ASSET_LAYOUT_FIELD_WRITE_KEYS,
    ASSET_LAYOUT_POST_BODY_KEYS,
    DEFAULT_ASSET_LAYOUT_FIELD_TYPE,
    HEADING_FIELD_TYPE,
    LIST_SELECT_FIELD_TYPE,
)


def _layout_as_dict(layout: Any) -> dict[str, Any]:
    if hasattr(layout, "to_dict"):
        return dict(layout.to_dict())
    if isinstance(layout, dict):
        return dict(layout)
    raise TypeError(f"Unexpected layout type: {type(layout)!r}")


def layout_to_dict(layout: Any) -> dict[str, Any]:
    """Normalize an :class:`~hudu_magic.models.AssetLayout` instance or dict."""
    return _layout_as_dict(layout)


def _field_as_dict(field: Any) -> dict[str, Any]:
    if isinstance(field, dict):
        return dict(field)
    if hasattr(field, "to_dict"):
        return dict(field.to_dict())
    raise TypeError(f"Unexpected field type: {type(field)!r}")


def _sorted_layout_fields(raw: Iterable[Any]) -> list[dict[str, Any]]:
    fields = [_field_as_dict(f) for f in raw]
    fields.sort(key=lambda d: (d.get("position") is None, d.get("position") or 0))
    return fields


def sorted_asset_layout_fields(raw_fields: Iterable[Any]) -> list[dict[str, Any]]:
    """Return layout ``fields`` sorted by ``position`` (GET-style dicts)."""
    return _sorted_layout_fields(raw_fields)


def collect_list_ids_from_layouts(layouts: Iterable[Any]) -> set[int]:
    """Distinct ``list_id`` values referenced by ``ListSelect`` fields on layouts."""
    ids: set[int] = set()
    for layout in layouts:
        data = _layout_as_dict(layout)
        for f in _sorted_layout_fields(data.get("fields") or []):
            if f.get("field_type") != LIST_SELECT_FIELD_TYPE:
                continue
            lid = f.get("list_id")
            if lid is not None:
                ids.add(int(lid))
    return ids


def layout_linkable_type_excludes_asset_layout_link(linkable_type: str) -> bool:
    """
    When True, ``linkable_id`` on this field should not be treated as another
    asset layout (companies, integrations, etc.). Blank ``linkable_type`` is
    *not* excluded so layout-to-layout links can still be represented.
    """
    lt = str(linkable_type or "").strip()
    if not lt:
        return False
    u = lt.upper().replace(" ", "")
    if "ASSETLAYOUT" in u:
        return False
    needles = (
        "COMPANY",
        "::USER",
        "USER::",
        "ARTICLE",
        "PASSWORD",
        "WEBSITE",
        "PROCEDURE",
        "FOLDER",
        "FLAG",
        "INTEGRATION",
        "INTEGRATOR",
    )
    return any(n in u for n in needles)


def layout_field_linkable_is_asset_layout_scope(field: dict[str, Any]) -> bool:
    """
    Whether this field's ``linkable_id`` should participate in layout-to-layout
    transfer (POST remap). Other polymorphic targets are omitted from the create
    payload.
    """
    if field.get("linkable_id") is None:
        return False
    lt = str(field.get("linkable_type") or "")
    if layout_linkable_type_excludes_asset_layout_link(lt):
        return False
    u = lt.upper().replace(" ", "")
    if "ASSETLAYOUT" in u:
        return True
    if not lt.strip():
        return True
    return False


def layout_has_self_referential_linkables(layout: Any) -> bool:
    """
    True when a layout-scope Asset Link field's ``linkable_id`` points at this
    same layout (common for fields like "Hypervisor" / "Parent server").
    """
    data = _layout_as_dict(layout)
    self_id = data.get("id")
    if self_id is None:
        return False
    sid = int(self_id)
    for f in _sorted_layout_fields(data.get("fields") or []):
        if not layout_field_linkable_is_asset_layout_scope(_field_as_dict(f)):
            continue
        try:
            if int(f.get("linkable_id")) == sid:
                return True
        except (TypeError, ValueError):
            continue
    return False


def layout_linkable_asset_layout_ref_ids(layout: Any) -> set[int]:
    """Source asset_layout ids referenced by layout-scope ``linkable_id`` fields."""
    refs: set[int] = set()
    data = _layout_as_dict(layout)
    self_id = data.get("id")
    for f in _sorted_layout_fields(data.get("fields") or []):
        if not layout_field_linkable_is_asset_layout_scope(_field_as_dict(f)):
            continue
        lid = f.get("linkable_id")
        try:
            rid = int(lid)
        except (TypeError, ValueError):
            continue
        if self_id is not None and rid == int(self_id):
            continue
        refs.add(rid)
    return refs


def layout_linkable_asset_layout_ref_ids_in_batch(
    layout: Any,
    batch_ids: set[int],
) -> set[int]:
    """Like :func:`layout_linkable_asset_layout_ref_ids` limited to ``batch_ids``."""
    return {
        r
        for r in layout_linkable_asset_layout_ref_ids(layout)
        if r in batch_ids
    }


def layout_fields_for_create(raw_fields: Iterable[Any]) -> list[dict[str, Any]]:
    """
    Turn GET-style layout ``fields`` into POST-safe field rows: strip read-only
    keys, assign contiguous ``position`` from 1..n, omit ``list_id`` except for
    ``ListSelect``, omit integration/non-layout ``linkable_id`` pairs, and skip
    ``required`` / ``show_in_list`` on Heading fields when absent from source.
    """
    ordered = _sorted_layout_fields(raw_fields)
    out: list[dict[str, Any]] = []
    for i, src in enumerate(ordered, start=1):
        ft = src.get("field_type") or DEFAULT_ASSET_LAYOUT_FIELD_TYPE
        row: dict[str, Any] = {
            "label": src.get("label") or f"Field {i}",
            "field_type": ft,
            "position": i,
        }
        for key in ASSET_LAYOUT_FIELD_WRITE_KEYS:
            if key in ("label", "field_type", "position"):
                continue
            if key in ("linkable_id", "linkable_type"):
                continue
            if key in ASSET_LAYOUT_FIELD_READ_ONLY_KEYS:
                continue
            val = src.get(key)
            if val is None:
                continue
            if key == "list_id" and ft != LIST_SELECT_FIELD_TYPE:
                continue
            if ft == HEADING_FIELD_TYPE and key in ("required", "show_in_list"):
                continue
            row[key] = val
        if layout_field_linkable_is_asset_layout_scope(src):
            try:
                row["linkable_id"] = int(src["linkable_id"])
            except (TypeError, ValueError):
                pass
            else:
                lt = src.get("linkable_type")
                if lt is not None:
                    row["linkable_type"] = lt
        out.append(row)
    return out


def strip_layout_field_list_ids_unless_list_select(
    fields: list[dict[str, Any]],
) -> None:
    """Remove ``list_id`` from rows where ``field_type`` is not ``ListSelect``."""
    for row in fields:
        if row.get("field_type") == LIST_SELECT_FIELD_TYPE:
            continue
        row.pop("list_id", None)


def apply_asset_layout_list_id_map(
    fields: list[dict[str, Any]],
    list_id_map: dict[int, int],
) -> None:
    """Rewrite ``list_id`` on ``ListSelect`` rows using ``source_id -> target_id``."""
    for row in fields:
        if row.get("field_type") != LIST_SELECT_FIELD_TYPE:
            continue
        old = row.get("list_id")
        if old is None:
            continue
        old_i = int(old)
        if old_i not in list_id_map:
            raise KeyError(
                f"ListSelect field {row.get('label')!r} references list_id={old_i} "
                "but that id is missing from list_id_map"
            )
        row["list_id"] = list_id_map[old_i]


def apply_asset_layout_linkable_id_map(
    fields: list[dict[str, Any]],
    layout_id_map: dict[int, int],
    batch_source_layout_ids: set[int],
    *,
    layout_name: str = "(unnamed)",
    current_source_layout_id: int | None = None,
    defer_unmapped_batch_linkables: bool = False,
) -> list[str]:
    """
    Rewrite ``linkable_id`` using ``source_layout_id -> target_layout_id``.
    Unmapped ids outside ``batch_source_layout_ids`` are dropped silently.

    Self-referential links (``linkable_id`` equals ``current_source_layout_id``)
    and, when ``defer_unmapped_batch_linkables`` is True, other in-batch ids not
    yet present in ``layout_id_map`` (cycles / not-yet-created deps) are omitted
    from the create body. Their field labels are returned so the caller can
    ``PUT`` after those target ids exist.
    """
    deferred_labels: list[str] = []
    for row in fields:
        lid = row.get("linkable_id")
        if lid is None:
            continue
        try:
            old = int(lid)
        except (TypeError, ValueError):
            row.pop("linkable_id", None)
            row.pop("linkable_type", None)
            continue
        if old in layout_id_map:
            row["linkable_id"] = layout_id_map[old]
            continue
        if (
            current_source_layout_id is not None
            and old == int(current_source_layout_id)
        ) or (defer_unmapped_batch_linkables and old in batch_source_layout_ids):
            deferred_labels.append(str(row.get("label") or ""))
            row.pop("linkable_id", None)
            row.pop("linkable_type", None)
            continue
        if old in batch_source_layout_ids:
            raise RuntimeError(
                f"layout {layout_name!r} field {row.get('label')!r} linkable_id={old} "
                "should have been mapped already (ordering bug)"
            )
        row.pop("linkable_id", None)
        row.pop("linkable_type", None)
    return deferred_labels


def layout_needs_linkable_patch(
    layout: Any,
    batch_source_layout_ids: set[int],
) -> bool:
    """
    True when this layout has layout-scope Asset Links that point at itself or
    at another id in ``batch_source_layout_ids`` (may need a post-create PUT).
    """
    if layout_has_self_referential_linkables(layout):
        return True
    return bool(
        layout_linkable_asset_layout_ref_ids(layout) & batch_source_layout_ids
    )


def normalize_layout_for_create(
    layout: Any,
    *,
    list_id_map: dict[int, int] | None = None,
    layout_id_map: dict[int, int] | None = None,
    batch_source_layout_ids: set[int] | None = None,
    defer_self_linkables: bool = True,
    defer_unmapped_batch_linkables: bool = False,
) -> dict[str, Any]:
    """
    Build a JSON body suitable for ``POST /asset_layouts`` (wrapped as
    ``{"asset_layout": ...}`` by the client) from a GET-style layout dict or
    :class:`~hudu_magic.models.AssetLayout` instance.

    Pass ``list_id_map`` / ``layout_id_map`` when cloning to another instance so
    ``list_id`` and ``linkable_id`` reference target rows. When using
    ``layout_id_map``, also pass ``batch_source_layout_ids`` (all source layout
    ids considered in scope for link resolution).

    Self-referential Asset Links (``linkable_id`` equals this layout's source
    ``id``) are omitted when ``defer_self_linkables`` is True and that id is not
    yet in ``layout_id_map``. With ``defer_unmapped_batch_linkables=True``,
    in-batch targets missing from the map (cycles / not-yet-created deps) are
    omitted the same way. After every batch id is mapped, call again and
    ``PUT`` to restore deferred links.

    Cosmetic / include flags default from :data:`~hudu_magic.constants.ASSET_LAYOUT_CREATE_DEFAULTS`
    when the source omits a key or sets it to ``None``.
    """
    data = _layout_as_dict(layout)
    raw_fields = data.get("fields") or []
    fields = layout_fields_for_create(raw_fields)
    strip_layout_field_list_ids_unless_list_select(fields)
    if list_id_map:
        apply_asset_layout_list_id_map(fields, list_id_map)
    if layout_id_map is not None and batch_source_layout_ids is not None:
        source_id = data.get("id")
        current_id: int | None = None
        if defer_self_linkables and source_id is not None:
            try:
                current_id = int(source_id)
            except (TypeError, ValueError):
                current_id = None
        apply_asset_layout_linkable_id_map(
            fields,
            layout_id_map,
            batch_source_layout_ids,
            layout_name=str(data.get("name") or "(unnamed)"),
            current_source_layout_id=current_id,
            defer_unmapped_batch_linkables=defer_unmapped_batch_linkables,
        )

    payload: dict[str, Any] = {"fields": fields}

    for key in ASSET_LAYOUT_POST_BODY_KEYS:
        if key == "fields":
            continue
        val = data.get(key)
        if val is None:
            continue
        payload[key] = val

    name = data.get("name")
    if name is not None:
        payload["name"] = name

    for key, default in ASSET_LAYOUT_CREATE_DEFAULTS.items():
        if key not in payload or payload[key] is None:
            payload[key] = default

    return payload
