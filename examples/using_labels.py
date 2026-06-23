import uuid
from pathlib import Path
from hudu_magic import HuduClient
client = HuduClient(
    api_key="yourkeyfromenv",
    instance_url="yourinstanceurlfromenv",
)

run_id = str(uuid.uuid4())[:8]
def count_labels(obj, label_type=None):
    rows = obj.list_labels(label_type)
    return len(list(rows)) if rows is not None else 0
# 1) Create label types
priority_type = client.label_types.create({
    "name": f"SDK Priority {run_id}",
    "color": "#6136ff",
    "applicable_record_types": ["Article", "Asset"],
})
status_type = client.label_types.create({
    "name": f"SDK Status {run_id}",
    "color": "#00aa00",
    "applicable_record_types": ["Article"],
})
print(f"label types: priority={priority_type.id}, status={status_type.id}")
# 2) Ephemeral article to label (cheap cleanup)
article = client.articles.create(payload={
    "company_id": COMPANY_ID,
    "name": f"SDK Label Test Article {run_id}",
    "content": "<p>label test</p>",
})
print(f"article: {article.id}")
assert count_labels(article) == 0, "expected no labels initially"
# 3) Apply — object method
applied = article.add_label(priority_type)
print(f"add_label (object): label id={applied.id}, type={applied.label_type_id}")
assert count_labels(article) == 1
assert count_labels(article, priority_type) == 1
# 4) Apply — label type → object
status_type.assign_to(article)
assert count_labels(article) == 2
print("assign_to: ok")
# 5) Apply — LabelsResource directly (e.g. on an asset)
asset = client.assets.create(
    company_id=COMPANY_ID,
    payload={"name": f"SDK Label Test Asset {run_id}", "asset_layout_id": 2},
)
client.labels.assign(asset, priority_type)
assert count_labels(asset, priority_type) == 1
print(f"labels.assign on asset: ok (asset={asset.id})")
# 6) List — all three list paths should agree
via_object = list(article.list_labels())
via_resource = list(client.labels.list_for(article))
via_base = list(client.articles.list_labels(article))
print(f"list counts: object={len(via_object)}, labels={len(via_resource)}, articles={len(via_base)}")
assert len(via_object) == len(via_resource) == len(via_base) == 2
# 7) Strip one type only
article.strip_labels(priority_type)
assert count_labels(article) == 1
assert count_labels(article, status_type) == 1
print("strip_labels(single type): ok")
# 8) Strip remainder via resource helper
client.articles.strip_labels(article)
assert count_labels(article) == 0
print("strip_labels(all): ok")
# 9) Negative — non-labelable type should fail locally before API call
company = client.companies.get(COMPANY_ID)
try:
    company.add_label(priority_type)
    raise AssertionError("expected ValueError for non-labelable company")
except ValueError as e:
    print(f"non-labelable guard: {e}")
# 10) Negative — bad applicable_record_types (client-side validation)
try:
    client.label_types.create({
        "name": f"SDK Bad Type {run_id}",
        "color": "#ff0000",
        "applicable_record_types": ["Company"],  # not in LABELABLE_TYPES
    })
    raise AssertionError("expected validation error")
except Exception as e:
    print(f"bad record type rejected: {type(e).__name__}: {e}")
# 11) Cleanup
asset.strip_labels()
asset.delete()
article.delete()
# optional — delete label types if your instance supports it:
# client.label_types.delete(priority_type.id)
# client.label_types.delete(status_type.id)
print("cleanup done")