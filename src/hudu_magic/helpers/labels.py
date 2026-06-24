"""Label type color helpers (parity with HuduAPI PowerShell ``ConvertTo-HuduLabelColor``)."""

from __future__ import annotations

import re

from ..validation import HuduValidationError

# Canonical label colors supported by Hudu (English keys).
HUDU_LABEL_COLOR_HEX: dict[str, str] = {
    "Red": "#ff0000",
    "Blue": "#0000ff",
    "Green": "#008000",
    "Yellow": "#ffff00",
    "Purple": "#800080",
    "Orange": "#ffa500",
    "LightPink": "#ffb6c1",
    "LightBlue": "#add8e6",
    "LightGreen": "#90ee90",
    "LightPurple": "#cbc3e3",
    "LightOrange": "#ffcc99",
    "LightYellow": "#ffffe0",
    "White": "#ffffff",
    "Grey": "#808080",
}

# Aliases per canonical color (English + DE / FR / IT / ES), mirroring HuduAPI PS module.
HUDU_LABEL_COLOR_ALIASES: dict[str, tuple[str, ...]] = {
    "Red": (
        "red",
        "crimson",
        "scarlet",
        "rot",
        "karminrot",
        "scharlachrot",
        "rouge",
        "cramoisi",
        "écarlate",
        "rosso",
        "cremisi",
        "scarlatto",
        "rojo",
        "carmesí",
        "escarlata",
    ),
    "Blue": (
        "blue",
        "navy",
        "blau",
        "marineblau",
        "bleu",
        "bleu marine",
        "blu",
        "blu navy",
        "azul",
        "azul marino",
    ),
    "Green": (
        "green",
        "lime",
        "grün",
        "limettengrün",
        "vert",
        "vert citron",
        "verde",
        "verde lime",
        "verde lima",
    ),
    "Yellow": (
        "yellow",
        "gold",
        "gelb",
        "gold",
        "jaune",
        "or",
        "giallo",
        "oro",
        "amarillo",
        "oro",
    ),
    "Purple": (
        "purple",
        "violet",
        "lila",
        "violett",
        "violet",
        "pourpre",
        "viola",
        "porpora",
        "púrpura",
        "violeta",
    ),
    "Orange": ("orange", "orange", "orange", "arancione", "naranja"),
    "LightPink": (
        "light pink",
        "pink",
        "baby pink",
        "hellrosa",
        "rosa",
        "rose clair",
        "rose",
        "rosa chiaro",
        "rosa",
        "rosa claro",
        "rosa",
    ),
    "LightBlue": (
        "light blue",
        "baby blue",
        "sky blue",
        "hellblau",
        "babyblau",
        "himmelblau",
        "bleu clair",
        "bleu ciel",
        "azzurro",
        "blu chiaro",
        "azul claro",
        "celeste",
    ),
    "LightGreen": (
        "light green",
        "mint",
        "hellgrün",
        "mintgrün",
        "vert clair",
        "menthe",
        "verde chiaro",
        "menta",
        "verde claro",
        "menta",
    ),
    "LightPurple": (
        "light purple",
        "lavender",
        "helllila",
        "lavendel",
        "violet clair",
        "lavande",
        "viola chiaro",
        "lavanda",
        "morado claro",
        "lavanda",
    ),
    "LightOrange": (
        "light orange",
        "peach",
        "hellorange",
        "pfirsich",
        "orange clair",
        "pêche",
        "arancione chiaro",
        "pesca",
        "naranja claro",
        "melocotón",
    ),
    "LightYellow": (
        "light yellow",
        "cream",
        "hellgelb",
        "creme",
        "jaune clair",
        "crème",
        "giallo chiaro",
        "crema",
        "amarillo claro",
        "crema",
    ),
    "White": ("white", "weiß", "blanc", "bianco", "blanco"),
    "Grey": (
        "grey",
        "gray",
        "silver",
        "grau",
        "silber",
        "gris",
        "argent",
        "grigio",
        "argento",
        "gris",
        "plateado",
    ),
}

_HEX_6_OR_8 = re.compile(r"^#?([0-9a-fA-F]{6})([0-9a-fA-F]{2})?$")
_HEX_3 = re.compile(r"^#?([0-9a-fA-F]{3})$")


def _normalize_color_lookup_key(value: str) -> str:
    return re.sub(r"[-\s]+", "_", value.strip().lower())


def _build_color_lookup() -> dict[str, str]:
    lookup: dict[str, str] = {}
    for canonical, aliases in HUDU_LABEL_COLOR_ALIASES.items():
        for alias in (canonical, *aliases):
            if not alias:
                continue
            lookup[_normalize_color_lookup_key(alias)] = canonical
    return lookup


_COLOR_LOOKUP: dict[str, str] | None = None


def _color_lookup() -> dict[str, str]:
    global _COLOR_LOOKUP
    if _COLOR_LOOKUP is None:
        _COLOR_LOOKUP = _build_color_lookup()
    return _COLOR_LOOKUP


def resolve_canonical_label_color_name(color: str) -> str:
    """
    Resolve a human-readable color name to a canonical Hudu label color key.

    Raises :class:`HuduValidationError` when the input cannot be resolved.
    """
    raw = color.strip()
    if not raw:
        raise HuduValidationError("color must be a non-empty string")

    key = _normalize_color_lookup_key(raw)
    canonical = _color_lookup().get(key)
    if canonical is None:
        allowed = ", ".join(HUDU_LABEL_COLOR_HEX.keys())
        raise HuduValidationError(
            f"Invalid color {color!r}. Allowed canonical values: {allowed}"
        )
    return canonical


def normalize_label_type_hex_color(color: str) -> str:
    """
    Normalize hex label colors to ``#rrggbb`` (lowercase, no alpha channel).

    Accepts optional ``#``, 3- or 6-digit hex, and 8-digit ``#rrggbbaa`` (alpha stripped).
    """
    raw = color.strip()
    if not raw:
        raise HuduValidationError("color must be a non-empty string")

    match_6 = _HEX_6_OR_8.match(raw)
    if match_6:
        return f"#{match_6.group(1).lower()}"

    match_3 = _HEX_3.match(raw)
    if match_3:
        r, g, b = match_3.group(1).lower()
        return f"#{r}{r}{g}{g}{b}{b}"

    raise HuduValidationError(
        f"Invalid hex color {color!r}. Expected #rgb, #rrggbb, or #rrggbbaa."
    )


def convert_to_hudu_label_color(color: str) -> str:
    """
    Convert a hex or human-readable color to a Hudu label type hex color.

    Mirrors HuduAPI PowerShell ``ConvertTo-HuduLabelColor``.
    """
    raw = color.strip()
    if not raw:
        raise HuduValidationError("color must be a non-empty string")

    if _HEX_6_OR_8.match(raw) or _HEX_3.match(raw):
        return normalize_label_type_hex_color(raw)

    canonical = resolve_canonical_label_color_name(raw)
    return HUDU_LABEL_COLOR_HEX[canonical]
