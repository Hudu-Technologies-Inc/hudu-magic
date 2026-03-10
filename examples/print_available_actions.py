from __future__ import annotations
from hudu_magic.endpoints import HuduEndpoint

for endpoint in HuduEndpoint:
    meta = endpoint.meta

    print(f"\n=== {endpoint.name} ===")

    for attr, value in vars(meta).items():
        if value not in (None, "", (), {}, []):
            print(f"{attr}: {value}")