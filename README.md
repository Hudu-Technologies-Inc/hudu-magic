# hudu-magic

purposefully tiny, enum-driven, and class-based API client library for Hudu

**Low-Maintenance, generated from openapi spec**

## Install

for now, first build with the below script
```
./build.sh
```

future:
```bash
pip install hudu-magic
```

## Generating builds for new hudu versions

1. Place openapi spec file https://yoururl.huducloud.com/api-docs.json in project directory as hudu-openapiv1.json

2. run `python generate-endpoints.py` after sourcing virtual environment (that has dev dependencies installed)

3. run ./build

this is designed to be suyper simple so that subsequent releases can eventually just be automatically generated, tested, validated, and pushed to pypi.

## Building

run the below script with zsh, sh, or bash

```
./build.sh
```

unit tests and integration tests run during build, so if you want the integration tests to actually run (and succeed), ensure you've filled out testenv from template testenv.example.


## interacting with classes


newasset = client.assets.create(company_id=5,payload={"name": "Router", "asset_layout_id": 2},)
print(newasset)

newasset.keys

print(newasset.id)
print(newasset.name)

newcompany = client.companies.create(payload={"name":f"masonmason{uuid.uuid4()}","nickname":"stelteSErstelter"})
print(newcompany)
newcompany.delete()
newarticle = client.articles.create(payload={"name":f"someartASDFicles{uuid.uuid4()}","content":"once upon a time"})
print(newarticle)
newarticle.delete()

client.folders.get()          # all folders
client.folders.get(5)         # one folder

Folder.get(client)            # all folders
Folder.get(client, 5)         # one folder
client.folders.get(name="IT")  # filtered list

### Future

in the future, once we get all the class methods built in, we'll be able to interact with different objects in new and exciting ways

companyrelation = client.companies.get(45).relate_to(client.get.network(1))

newarticleinfolder = client.folder.new({name="myfolder}).assign(client.articles.get(55))

networkassets.move_to(client.companies.get("roberts company"))


## using in your project

include hudu-magic in your project's requirements.txt file, import as hudu_magic, and instantiate a `HuduClient` class member

```
from hudu_magic import HuduClient, HuduEndpoint

client = HuduClient(
    api_key="env.yourkey",
    instance_url="https://env.yourinstance",
)

newasset = client.assets.create(company_id=5,payload={"name": "Router", "asset_layout_id": 2},)

newarticle = client.articles.create(payload={name:"this",contents:"that"})


...
```