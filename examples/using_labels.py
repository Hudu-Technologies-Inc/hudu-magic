import uuid
import random
from hudu_magic import HuduClient
import uuid
COMPANY_ID = 5  # or 1 — pick a sandbox company

client = HuduClient(
    api_key="yourkeyfromenv",
    instance_url="yourinstanceurlfromenv",
)

run_id = str(uuid.uuid4())[:8]
def count_labels(obj, label_type=None):
    rows = obj.list_labels(label_type)
    return len(list(rows)) if rows is not None else 0

priority_type = client.label_types.create({
    "name": f"SDK Priority {run_id}",
    "color": "#6136ff",
    "applicable_record_types": ["Article", "Asset"],
})
status_type = client.label_types.create({
    "name": f"SDK Status {run_id}",
    "color": "light green",
    "applicable_record_types": ["Article","Asset","AssetPassword"],
})
print(f"label types: priority={priority_type.id}, status={status_type.id}")

article = client.articles.create(payload={
    "company_id": COMPANY_ID,
    "name": f"SDK Label Test Article {run_id}",
    "content": "<p>label test</p>",
})
print(f"article: {article.id}")
assert count_labels(article) == 0, "expected no labels initially"

applied = article.add_label(priority_type)
print(f"add_label (object): label id={applied.id}, type={applied.label_type_id}")
assert count_labels(article) == 1
assert count_labels(article, priority_type) == 1
status_type.assign_to(article)
assert count_labels(article) == 2
print("assign_to: ok")

asset = client.assets.create(
    company_id=COMPANY_ID,
    payload={"name": f"SDK Label Test Asset {run_id}", "asset_layout_id": 2},
)
client.labels.assign(asset, priority_type)
assert count_labels(asset, priority_type) == 1
print(f"labels.assign on asset: ok (asset={asset.id})")

via_object = list(article.list_labels())
via_resource = list(client.labels.list_for(article))
via_base = list(client.articles.list_labels(article))
print(f"list counts: object={len(via_object)}, labels={len(via_resource)}, articles={len(via_base)}")
assert len(via_object) == len(via_resource) == len(via_base) == 2
assets = client.assets.list()
print(f"listed {len(assets)} assets")
labelsforassets = assets.list_labels()
print(f"listed {len(labelsforassets)} labels for assets")


article.strip_labels(priority_type)
assert count_labels(article) == 1
assert count_labels(article, status_type) == 1
print("strip_labels(single type): ok")

client.articles.strip_labels(article)
assert count_labels(article) == 0
print("strip_labels(all): ok")

company = client.companies.get(COMPANY_ID)
try:
    company.add_label(priority_type)
    raise AssertionError("expected ValueError for non-labelable company")
except ValueError as e:
    print(f"non-labelable guard: {e}")

try:
    client.label_types.create({
        "name": f"SDK Bad Type {run_id}",
        "color": "#ff0000",
        "applicable_record_types": ["Company"],  # not in LABELABLE_TYPES
    })
    raise AssertionError("expected validation error")
except Exception as e:
    print(f"bad record type rejected: {type(e).__name__}: {e}")


articles = client.articles.list()
print(f"listed {len(articles)} articles")
labelsforartcles = articles.list_labels()
print(f"listed {len(labelsforartcles)} labels for articles")

passwords = client.asset_passwords.list()
print(f"listed {len(passwords)} asset passwords")
labelsforpasswords = passwords.list_labels()
print(f"listed {len(labelsforpasswords)} labels for asset passwords. stripping now")

print("stripped labels for asset passwords. applying based on id now.")
for password in passwords:
    if (password.id % 3 == 0):
        password.add_label(client.labeltypes.create(name=f"SDK Test Label {random.randint(0, 1000000)} for password with id {password.id}", color=f"#{random.randint(0, 0xFFFFFF):06x}", applicable_record_types=["AssetPassword"], access_level="specific_companies", allowed_company_ids=[password.company_id]))
    elif (password.id % 3 == 1):
        password.add_label(client.labeltypes.create(name=f"SDK Test Label {random.randint(0, 1000000)} for password with id {password.id}", color=f"#{random.randint(0, 0xFFFFFF):06x}", applicable_record_types=["AssetPassword"], access_level="all_companies"))
    else:
        password.add_label(client.labeltypes.create(name=f"OMNI SDK Test Label {random.randint(0, 1000000)} for password with id {password.id}", color=f"#{random.randint(0, 0xFFFFFF):06x}", applicable_record_types=["AssetPassword", "Asset","Article"], access_level="all_companies"))

labelsforpasswords = passwords.list_labels()
print(f"listed {len(labelsforpasswords)} labels for asset passwords after applying")


for article in articles:
    if (article.id % 3 == 0):
        article.add_label(status_type)
    elif (article.id % 3 == 1):
        article.add_label(priority_type)
    else:
        article.add_label(client.labeltypes.create(name=f"OMNI SDK Test Label {random.randint(0, 1000000)} for article with id {article.id}", color=f"#{random.randint(0, 0xFFFFFF):06x}", applicable_record_types=["Article", "Asset","AssetPassword"], access_level="all_companies"))

for asset in assets:
    if (asset.id % 3 == 0):
        asset.add_label(priority_type)
    elif (asset.id % 3 == 1):
        asset.add_label(status_type)
    else:
        asset.add_label(client.labeltypes.create(name=f"OMNI SDK Test Label {random.randint(0, 1000000)} for asset with id {asset.id}", color=f"#{random.randint(0, 0xFFFFFF):06x}", applicable_record_types=["Asset", "Article","AssetPassword"], access_level="all_companies"))

labelsforarticles = articles.list_labels()
print(f"listed {len(labelsforarticles)} labels for articles after applying")
labelsforassets = assets.list_labels()
print(f"listed {len(labelsforassets)} labels for assets after applying")

