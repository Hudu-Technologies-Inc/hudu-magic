"""Dev utility: copy asset layouts between Hudu instances (see --help)."""

from __future__ import annotations

import argparse
import os
import sys
from typing import Any, Iterable

from hudu_magic import HuduClient
from hudu_magic.helpers.asset_layouts import (
    collect_list_ids_from_layouts,
    layout_create_payload_from_get,
    layout_linkable_asset_layout_ref_ids,
    layout_linkable_asset_layout_ref_ids_in_batch,
    layout_to_dict,
)
from hudu_magic.validation import HuduAPIError


def _list_item_create_attrs(src: dict[str, Any]) -> list[dict[str, str]]:
    """
    Build list_items_attributes for POST /lists. Duplicate item names under one
    list can trigger server-side validation errors; disambiguate with a suffix.
    """
    items = src.get("list_items") or src.get("items") or []
    result: list[dict[str, str]] = []
    seen_counts: dict[str, int] = {}
    for it in items:
        if isinstance(it, dict):
            d = dict(it)
        elif hasattr(it, "to_dict"):
            d = dict(it.to_dict())
        else:
            continue
        nm = d.get("name")
        if not isinstance(nm, str):
            continue
        base = nm.strip()
        if not base:
            continue
        n = seen_counts.get(base, 0)
        seen_counts[base] = n + 1
        label = base if n == 0 else f"{base} (import {n + 1})"
        result.append({"name": label})
    return result


def _first_target_list_by_name(target: HuduClient, exact_name: str) -> dict[str, Any] | None:
    res = target.lists.list(name=exact_name)
    if res is None:
        return None
    rows = list(res) if isinstance(res, (list, tuple)) else [res]
    if not rows:
        return None
    if len(rows) > 1:
        print(
            f"warning: target has {len(rows)} lists named {exact_name!r}; using the first",
            file=sys.stderr,
        )
    return layout_to_dict(rows[0])


def _register_created_list(
    mapping: dict[int, int],
    source_list_id: int,
    created: Any,
    *,
    list_name: str,
    item_count: int,
    note: str = "",
) -> None:
    created_d = layout_to_dict(created)
    new_id = created_d.get("id")
    if new_id is None:
        print(
            f"error: could not read id from created list {list_name!r}: {created_d!r}",
            file=sys.stderr,
        )
        sys.exit(1)
    mapping[source_list_id] = int(new_id)
    suffix = f" {note}" if note else ""
    print(
        f"cloned list {list_name!r}: source_id={source_list_id} -> target_id={new_id} "
        f"({item_count} items){suffix}",
        file=sys.stderr,
    )


def clone_referenced_lists(
    source: HuduClient,
    target: HuduClient,
    source_list_ids: set[int],
    *,
    dry_run: bool,
    reuse_target_by_name: bool,
) -> dict[int, int]:
    """
    For each source list id, create a matching list on the target (or reuse by
    name) and return source_id -> target_id.
    """
    mapping: dict[int, int] = {}
    for lid in sorted(source_list_ids):
        raw = source.lists.get(lid)
        if raw is None:
            print(f"error: source list id={lid} not found", file=sys.stderr)
            sys.exit(1)
        src = layout_to_dict(raw)
        list_name = src.get("name") or f"Imported list {lid}"
        item_attrs = _list_item_create_attrs(src)

        if reuse_target_by_name:
            match = _first_target_list_by_name(target, list_name)
            if match is not None:
                tid = match.get("id")
                if tid is not None:
                    mapping[lid] = int(tid)
                    print(
                        f"reuse target list id={tid} name={list_name!r} "
                        f"(instead of cloning source list_id={lid})",
                        file=sys.stderr,
                    )
                    continue

        if dry_run:
            print(
                f"dry-run: would create list {list_name!r} "
                f"({len(item_attrs)} items) for source list_id={lid}",
            )
            continue

        create_body: dict[str, Any] = {"name": list_name}
        if item_attrs:
            create_body["list_items_attributes"] = item_attrs

        try:
            created = target.lists.create(create_body)
        except HuduAPIError as exc:
            if exc.status_code != 422:
                raise
            # Often "Validation failed" when the list name already exists on target.
            match = _first_target_list_by_name(target, list_name)
            if match is not None and match.get("id") is not None:
                mapping[lid] = int(match["id"])
                print(
                    f"warning: POST /lists for {list_name!r} returned 422; "
                    f"reusing existing target list id={match['id']} (items may differ from source)",
                    file=sys.stderr,
                )
                continue
            alt_name = f"{list_name} (hudu-magic import {lid})"
            alt_body = {**create_body, "name": alt_name}
            try:
                created = target.lists.create(alt_body)
            except HuduAPIError as exc2:
                print(
                    f"error: could not create list {list_name!r} (422) or "
                    f"disambiguated name {alt_name!r}.\n"
                    f"First error: {exc}\nSecond error: {exc2}",
                    file=sys.stderr,
                )
                raise exc2 from exc
            _register_created_list(
                mapping,
                lid,
                created,
                list_name=alt_name,
                item_count=len(item_attrs),
                note=f"(renamed from {list_name!r} after 422)",
            )
            continue

        _register_created_list(
            mapping, lid, created, list_name=list_name, item_count=len(item_attrs)
        )

    return mapping


def _source_layout_id(layout: Any) -> int:
    d = layout_to_dict(layout)
    i = d.get("id")
    if i is None:
        raise SystemExit(
            f"Source layout {d.get('name')!r} has no id; cannot order linkable_id dependencies"
        )
    return int(i)


def _index_source_layouts_by_id(source_layouts: Iterable[Any]) -> dict[int, Any]:
    out: dict[int, Any] = {}
    for L in source_layouts:
        d = layout_to_dict(L)
        i = d.get("id")
        if i is None:
            continue
        out[int(i)] = L
    return out


def _target_layout_id_by_name(target: HuduClient, exact_name: str) -> int | None:
    res = target.asset_layouts.list(name=exact_name)
    if res is None:
        return None
    rows = list(res) if isinstance(res, (list, tuple)) else [res]
    if not rows:
        return None
    if len(rows) > 1:
        print(
            f"warning: target has {len(rows)} asset layouts named {exact_name!r}; using the first",
            file=sys.stderr,
        )
    i = layout_to_dict(rows[0]).get("id")
    return int(i) if i is not None else None


def _hydrate_source_layout(
    source: HuduClient,
    layout_id: int,
    source_by_id: dict[int, Any],
) -> Any | None:
    """Ensure ``source_by_id`` contains ``layout_id`` (GET when missing from list)."""
    if layout_id in source_by_id:
        return source_by_id[layout_id]
    raw = source.asset_layouts.get(layout_id)
    if raw is None:
        return None
    source_by_id[layout_id] = raw
    return raw


def _linkable_dependency_closure_ids(
    seed_layouts: list[Any],
    source_by_id: dict[int, Any],
    source: HuduClient,
) -> set[int]:
    """Transitive closure of source layout ids reachable via linkable_id."""
    seen: set[int] = set()
    stack: list[int] = []
    for L in seed_layouts:
        sid = _source_layout_id(L)
        if sid not in seen:
            seen.add(sid)
            stack.append(sid)

    i = 0
    while i < len(stack):
        sid = stack[i]
        i += 1
        L = source_by_id.get(sid) or _hydrate_source_layout(source, sid, source_by_id)
        if L is None:
            print(
                f"warning: could not load source asset layout id={sid} (skipping)",
                file=sys.stderr,
            )
            continue
        for ref in layout_linkable_asset_layout_ref_ids(L):
            if ref not in source_by_id:
                got = _hydrate_source_layout(source, ref, source_by_id)
                if got is None:
                    continue
            if ref not in seen:
                seen.add(ref)
                stack.append(ref)
    return seen


def _classify_layout_closure(
    closure_ids: set[int],
    source_by_id: dict[int, Any],
    *,
    target: HuduClient,
    existing_target_names: set[str],
    skip_existing: bool,
) -> tuple[set[int], dict[int, int]]:
    """
    Split closure into layouts to POST (``create_ids``) vs already on target
    (``prefetch_map``: source_id -> target_id).
    """
    create_ids: set[int] = set()
    prefetch_map: dict[int, int] = {}
    for sid in closure_ids:
        L = source_by_id[sid]
        name = layout_to_dict(L).get("name") or ""
        if skip_existing and name in existing_target_names:
            tid = _target_layout_id_by_name(target, name)
            if tid is None:
                print(
                    f"error: layout {name!r} is marked existing on target but "
                    "could not resolve its id (name filter returned nothing)",
                    file=sys.stderr,
                )
                sys.exit(1)
            prefetch_map[sid] = tid
        else:
            create_ids.add(sid)
    return create_ids, prefetch_map


def _expand_to_create_with_linkables(
    seed: list[Any],
    source_layouts: Iterable[Any],
    *,
    source: HuduClient,
    target: HuduClient,
    existing_target_names: set[str],
    skip_existing: bool,
) -> tuple[list[Any], set[int], dict[int, int]]:
    """
    Follow linkable_id to other source layouts, add them to the create batch
    (or prefetch target ids when names already exist on target).

    Returns ``(ordered_layouts_to_post, batch_source_ids, initial_layout_id_map)``.
    """
    source_by_id = _index_source_layouts_by_id(source_layouts)
    closure = _linkable_dependency_closure_ids(seed, source_by_id, source)
    create_ids, prefetch_map = _classify_layout_closure(
        closure,
        source_by_id,
        target=target,
        existing_target_names=existing_target_names,
        skip_existing=skip_existing,
    )

    seed_ids = {_source_layout_id(L) for L in seed}
    for sid in sorted(closure - seed_ids):
        L = source_by_id[sid]
        nm = layout_to_dict(L).get("name") or sid
        if sid in prefetch_map:
            print(
                f"note: auto-resolved dependency layout {nm!r} (source id={sid}) "
                f"-> existing target id={prefetch_map[sid]}",
                file=sys.stderr,
            )
        elif sid in create_ids:
            print(
                f"note: auto-including dependency layout {nm!r} (source id={sid}) "
                "for linkable_id",
                file=sys.stderr,
            )

    if not create_ids:
        return [], closure, prefetch_map

    create_layouts = [source_by_id[sid] for sid in create_ids]
    ordered = topo_ordered_layouts(create_layouts)
    return ordered, closure, prefetch_map


def topo_ordered_layouts(layouts: list[Any]) -> list[Any]:
    """
    Creation order so every linkable_id pointing at another layout in ``layouts``
    is satisfied (source asset_layout ids).
    """
    batch_ids = {_source_layout_id(L) for L in layouts}
    id_to_layout = {_source_layout_id(L): L for L in layouts}

    indegree: dict[int, int] = {bid: 0 for bid in batch_ids}
    dependents: dict[int, list[int]] = {bid: [] for bid in batch_ids}

    for L in layouts:
        sl = _source_layout_id(L)
        for ref in layout_linkable_asset_layout_ref_ids_in_batch(L, batch_ids):
            dependents[ref].append(sl)
            indegree[sl] += 1

    queue = sorted(bid for bid in batch_ids if indegree[bid] == 0)
    order_ids: list[int] = []
    while queue:
        n = queue.pop(0)
        order_ids.append(n)
        for m in sorted(dependents[n]):
            indegree[m] -= 1
            if indegree[m] == 0:
                queue.append(m)
        queue.sort()

    if len(order_ids) != len(batch_ids):
        print(
            "error: linkable_id references among these layouts form a cycle "
            "(or could not be ordered); fix source layouts or split the batch",
            file=sys.stderr,
        )
        sys.exit(1)

    return [id_to_layout[i] for i in order_ids]


def _created_asset_layout_id(result: Any) -> int:
    d = layout_to_dict(result)
    i = d.get("id")
    if i is None:
        print(f"error: could not read id from created asset layout: {d!r}", file=sys.stderr)
        sys.exit(1)
    return int(i)


def _client_from_env(prefix: str) -> HuduClient:
    key = os.environ.get(f"{prefix}_API_KEY")
    url = os.environ.get(f"{prefix}_INSTANCE_URL")
    if not key or not url:
        print(
            f"Set {prefix}_API_KEY and {prefix}_INSTANCE_URL.",
            file=sys.stderr,
        )
        sys.exit(1)
    return HuduClient(api_key=key, instance_url=url)


def _layout_names_on_instance(client: HuduClient) -> dict[str, Any]:
    names: set[str] = set()
    layouts = client.asset_layouts.list()
    for item in layouts:
        d = layout_to_dict(item)
        n = d.get("name")
        if isinstance(n, str):
            names.add(n)
    return names


def _parse_name_list(arg: str | None) -> list[str]:
    if not arg:
        return []
    return [p.strip() for p in arg.split(",") if p.strip()]


def _names_from_args_and_env(args: argparse.Namespace) -> list[str]:
    if args.names:
        return _parse_name_list(args.names)
    env_names = os.environ.get("HUDU_LAYOUT_NAMES", "")
    return _parse_name_list(env_names)


def main() -> None:
    epilog = """
The API expects each layout field as a JSON object (same idea as a PowerShell
hashtable), for example:
  label, position, field_type, required, show_in_list

GET responses include read-only keys (id, value, …). Those are stripped before
POST. Creating a layout is not idempotent; by default layouts whose names
already exist on the target are skipped (--no-skip-existing to try anyway).

ListSelect fields reference list_id on the source; those lists are cloned on
the target first so new list rows exist and field list_ids are rewritten.
If POST /lists returns 422 (often a duplicate list name on the target), the
script reuses the existing target list with that name, or retries with a
suffix name. Use --reuse-target-lists-by-name to reuse before attempting POST.
Other field types may still carry list_id from GET; those are stripped so the
server does not set an invalid FK.

Layouts that reference each other via linkable_id are created in dependency
order; linkable_id is rewritten to the new target layout ids.

By default, layout fields whose linkable_type looks like another asset layout
(including blank type) pull that layout into this run when needed. Integration
and other non-layout linkable_type values are stripped from the create payload
with no message. Use --no-auto-include-linkables to disable following
linkable_id for extra layouts.

Environment (required):
  HUDU_SOURCE_API_KEY, HUDU_SOURCE_INSTANCE_URL
  HUDU_TARGET_API_KEY, HUDU_TARGET_INSTANCE_URL

Optional:
  HUDU_LAYOUT_NAMES — comma-separated names (overridden by --names)

Examples:
  export HUDU_SOURCE_API_KEY=… HUDU_SOURCE_INSTANCE_URL=https://source.hudu.app
  export HUDU_TARGET_API_KEY=… HUDU_TARGET_INSTANCE_URL=https://target.hudu.app
  uv run python dev/createlayouts.py --dry-run --names "Layout A,Layout B"
  uv run python dev/createlayouts.py --list-source
"""
    parser = argparse.ArgumentParser(
        description="Copy asset layouts from one Hudu instance to another.",
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--names",
        help="Comma-separated layout names to copy (overrides HUDU_LAYOUT_NAMES)",
    )
    parser.add_argument(
        "--all-layouts",
        action="store_true",
        help="Copy every asset layout from the source instance",
    )
    parser.add_argument(
        "--list-source",
        action="store_true",
        help="Print layout names from the source and exit",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print payloads only; do not call the target API",
    )
    parser.add_argument(
        "--no-skip-existing",
        action="store_true",
        help="Attempt create even when a layout with the same name exists on target",
    )
    parser.add_argument(
        "--reuse-target-lists-by-name",
        action="store_true",
        help=(
            "Before POST /lists, if the target already has that exact list name, "
            "reuse it (avoids an extra 422). Without this flag, a 422 on create "
            "still falls back to reuse-by-name, then to a disambiguated name."
        ),
    )
    parser.add_argument(
        "--no-auto-include-linkables",
        action="store_true",
        help=(
            "Do not add source layouts reached only via linkable_id to the batch; "
            "unmapped layout linkable_id values are omitted from the POST body"
        ),
    )
    args = parser.parse_args()
    args.names = _names_from_args_and_env(args)

    source = _client_from_env("HUDU_SOURCE")
    target = _client_from_env("HUDU_TARGET")

    if args.list_source:
        layouts = source.asset_layouts.list()
        for item in sorted(layouts, key=lambda x: (layout_to_dict(x).get("name") or "")):
            d = layout_to_dict(item)
            print(d.get("name", ""))
        return

    if not args.all_layouts and not args.names:
        parser.error(
            "Specify --names, set HUDU_LAYOUT_NAMES, or use --all-layouts "
            "(use --list-source to see names)"
        )

    source_layouts = source.asset_layouts.list()
    if args.all_layouts:
        selected = list(source_layouts)
    else:
        want = set(args.names)
        selected = [
            L
            for L in source_layouts
            if layout_to_dict(L).get("name") in want
        ]
        missing = want - {layout_to_dict(L).get("name") for L in selected}
        for m in sorted(missing):
            print(f"warning: source has no layout named {m!r}", file=sys.stderr)

    if not selected:
        print("No matching layouts to copy.", file=sys.stderr)
        sys.exit(1)

    existing_target = _layout_names_on_instance(target)
    skip_existing = not args.no_skip_existing

    to_create: list[Any] = []
    for layout in selected:
        name = layout_to_dict(layout).get("name", "(unnamed)")
        if skip_existing and name in existing_target:
            print(f"skip (exists): {name!r}")
            continue
        to_create.append(layout)

    if not to_create:
        print("Nothing to do: every selected layout already exists on the target.")
        return

    if args.no_auto_include_linkables:
        ordered_layouts = topo_ordered_layouts(to_create)
        batch_source_ids = {_source_layout_id(L) for L in to_create}
        prefetch_layout_map: dict[int, int] = {}
    else:
        ordered_layouts, batch_source_ids, prefetch_layout_map = (
            _expand_to_create_with_linkables(
                to_create,
                source_layouts,
                source=source,
                target=target,
                existing_target_names=existing_target,
                skip_existing=skip_existing,
            )
        )

    if not ordered_layouts:
        print(
            "Nothing to POST: every layout in scope (including link dependencies) "
            "already exists on the target; linkable_id values are mapped to those.",
            file=sys.stderr,
        )
        return

    list_ids = collect_list_ids_from_layouts(ordered_layouts)
    list_id_map = clone_referenced_lists(
        source,
        target,
        list_ids,
        dry_run=args.dry_run,
        reuse_target_by_name=args.reuse_target_lists_by_name,
    )

    if args.dry_run and list_ids:
        print(
            f"dry-run: {len(list_ids)} distinct source list(s) will be cloned "
            "before layouts (see lines above)",
        )

    layout_id_map: dict[int, int] = dict(prefetch_layout_map)

    for layout in ordered_layouts:
        try:
            payload = layout_create_payload_from_get(
                layout,
                list_id_map=list_id_map if not args.dry_run else None,
                layout_id_map=layout_id_map if not args.dry_run else None,
                batch_source_layout_ids=batch_source_ids if not args.dry_run else None,
            )
        except KeyError as exc:
            print(f"error: {exc}", file=sys.stderr)
            sys.exit(1)
        except RuntimeError as exc:
            print(f"error: {exc}", file=sys.stderr)
            sys.exit(1)
        name = payload.get("name", "(unnamed)")

        if args.dry_run:
            print(
                f"dry-run: would create layout {name!r} with "
                f"{len(payload.get('fields', []))} fields",
            )
            continue

        created = target.asset_layouts.create(
            payload,
            allow_unknown_fields=True,
        )
        layout_id_map[_source_layout_id(layout)] = _created_asset_layout_id(created)
        print(f"created: {name!r}")
        existing_target.add(name)


if __name__ == "__main__":
    main()
