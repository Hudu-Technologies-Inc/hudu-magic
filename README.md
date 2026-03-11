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
print(f"created {newasset.name} with id {newasset.id}")

newname = f"Router {str(uuid.uuid4())[:8]}"
print(f"updating name to {newname}")
newasset.name = newname

newasset.save()
print(f"updated {newasset.name} with id {newasset.id}")

companyassets = client.assets.list_for_company(5)

newasset.delete()
print(f"deleted asset with id {newasset.id}")

article = client.articles.create(payload={"name":"asdfasdf","content": "This is a test article.","company_id":5})
print(f"created article with id {article.id}")

article.content = "This is updated content for the test article."
article.save()
print(f"updated article with id {article.id}, new content: {article.content}")

article.delete()
print(f"deleted article with id {article.id}")

newcompany = client.companies.create(payload={"name": f"Test Company {str(uuid.uuid4())[:8]}"})
print(f"created company with id {newcompany.id}")

newcompany.name = f"Updated Test Company {str(uuid.uuid4())[:8]}"
newcompany.save()
print(f"updated company with id {newcompany.id}, new name: {newcompany.name}")

newcompany.delete()
print(f"deleted company with id {newcompany.id}")

client.folders.get()          # all folders
client.folders.get(5)         # one folder

Folder.get(client)            # all folders
Folder.get(client, 5)         # one folder
client.folders.get(name="IT")  # filtered list

newpassword = client.asset_passwords.create(payload={"company_id": 5, "name": f"Test Password {str(uuid.uuid4())[:8]}", "username": "testuser", "password": "testpass"})
print(f"created password with id {newpassword.id}")

newpassword.name = f"Updated Test Password {str(uuid.uuid4())[:8]}"
newpassword.save()
print(f"updated password with id {newpassword.id}, new name: {newpassword.name}")

newpassword.delete()
print(f"deleted password with id {newpassword.id}")

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