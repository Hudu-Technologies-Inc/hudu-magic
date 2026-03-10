# hudu-magic

purposefully tiny, enum-driven, and class-based API client library for Hudu

## Install

for now, build and run tests (in python 3.11-3.14 venv) with:
```
./build.sh
```

future:
```bash
pip install hudu-magic
```

## Generating Class Definitions

When a new version of Hudu comes along with updated endpoints, we simply generate from the new openapi spec file https://yoururl.huducloud.com/api-docs.json and place in project dir named hudu-openapiv1.json.

install dev dependencies in generate-requirements.txt and then generate new class definitions with generate-endpoints.py

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

companies = client.get(HuduEndpoint.COMPANIES)

client.companies.get(144)
client.companies.create({"name": "Acme"})
client.articles.create({"name": "How To", "content": "..."})
client.assets.create(company_id=5, payload={"name": "Router", "asset_layout_id": 2})

...
```