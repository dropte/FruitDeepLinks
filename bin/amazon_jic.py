"""Decode Amazon detail-link JIC provider hints for audits.

JIC is link context, not account entitlement. The fields below are observed
wire-format strings; this module deliberately makes no service classification.
"""

from __future__ import annotations

import base64
import binascii
import re
from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse


_TIER_ID = re.compile(r"amzn1\.dv\.channelTier\.[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$", re.I)


@dataclass(frozen=True)
class JicHint:
    prefix: int
    benefit_ids: tuple[str, ...]
    offer_types: tuple[str, ...]
    channel_tier_ids: tuple[str, ...]


def _read_varint(data: bytes, offset: int) -> tuple[int, int]:
    value = 0
    for shift in range(0, 70, 7):
        if offset >= len(data):
            raise ValueError("truncated JIC varint")
        byte = data[offset]
        offset += 1
        value |= (byte & 0x7f) << shift
        if not byte & 0x80:
            return value, offset
    raise ValueError("oversized JIC varint")


def decode_jic(value: str) -> JicHint:
    """Decode the observed prefix|base64, length-delimited JIC wire shape.

    Raises ValueError for malformed or unsupported shapes. Callers must not
    infer subscription ownership or classify a playable from this alone.
    """
    try:
        prefix_text, encoded = value.split("|", 1)
        if not prefix_text.isascii() or not prefix_text.isdigit():
            raise ValueError("invalid JIC prefix")
        prefix = int(prefix_text)
        if prefix != len(encoded):
            raise ValueError("JIC prefix does not match encoded length")
        data = base64.b64decode(encoded, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise ValueError("invalid JIC encoding") from exc
    if not data or len(data) > 4096:
        raise ValueError("invalid JIC payload length")

    fields: dict[int, list[str]] = {1: [], 2: [], 3: []}
    offset = 0
    count = 0
    while offset < len(data):
        count += 1
        if count > 64:
            raise ValueError("too many JIC fields")
        tag, offset = _read_varint(data, offset)
        field_number, wire_type = tag >> 3, tag & 7
        if field_number not in fields or wire_type != 2:
            raise ValueError("unsupported JIC field")
        length, offset = _read_varint(data, offset)
        if length == 0 or length > 512 or offset + length > len(data):
            raise ValueError("invalid JIC field length")
        try:
            text = data[offset:offset + length].decode("ascii")
        except UnicodeDecodeError as exc:
            raise ValueError("non-ASCII JIC field") from exc
        fields[field_number].append(text)
        offset += length

    if any(not _TIER_ID.fullmatch(tier) for tier in fields[3]):
        raise ValueError("invalid JIC channel-tier ID")
    return JicHint(prefix, tuple(fields[1]), tuple(fields[2]), tuple(fields[3]))


def decode_jic_url(url: str) -> JicHint | None:
    """Return a decoded JIC from a URL, or None if it has no JIC parameter."""
    values = parse_qs(urlparse(url).query).get("jic")
    return decode_jic(values[0]) if values else None
