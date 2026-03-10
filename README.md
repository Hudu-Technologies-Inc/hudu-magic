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

companies = client.get_all_pages(HuduEndpoint.COMPANIES)
...
```