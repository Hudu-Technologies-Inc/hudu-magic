# hudu-magic

purposefully tiny, enum-driven, and class-based API client library for Hudu

Low-Maintenance, generated from openapi spec

## Generating

1. Place openapi spec file https://yoururl.huducloud.com/api-docs.json in project directory as hudu-openapiv1.json

2. run `python generate-endpoints.py` after sourcing virtual environment

## Building

run 

```
./build.sh
```

## Install

for now, first build with
```
./build.sh
```

future:
```bash
pip install hudu-magic
```

## interacting with classes

client.get_all_pages(HuduEndpoint.COMPANIES)
client.get(HuduEndpoint.COMPANIES)
client.get(HuduEndpoint.ASSETS)
client.get(HuduEndpoint.NETWORKS)


## using in your project

include hudu-magic in your project's requirements.txt file, import as hudu_magic, and instantiate a `HuduClient` class member

```
from hudu_magic import HuduClient, HuduEndpoint

client = HuduClient(
    api_key="env.yourkey",
    instance_url="https://env.yourinstance",
)

newasset = client.assets.create(company_id=5,payload={"name": "Router", "asset_layout_id": 2},)
print(newasset)
print(newasset.id)
print(newasset.name)

newcompany = client.companies.create(payload={"name":f"masonmason{uuid.uuid4()}","nickname":"stelteSErstelter"})
print(newcompany)
newcompany.delete()
newarticle = client.articles.create(payload={"name":f"someartASDFicles{uuid.uuid4()}","content":"once upon a time"})
print(newarticle)
newarticle.delete()

...
```