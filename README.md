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

#### Assets

```python
newasset = client.assets.create(company_id=5,payload={"name": "Router", "asset_layout_id": 2},)
newasset.name = f"Router name"
newasset.save()
otherassets.list_for_company("gregs computers")
companyassets = client.assets.list_for_company(5)
otherassets.last.fields["thing1"]=thing2
otherassets.last.save()
otherassets.first.delete()
```

#### Articles

```python
article = client.articles.create(payload={"name":"asdfasdf","content": "This is a test article.","company_id":5})
otherarticle = client.articles.by_folder(5)
deletearticle = client.articles.get("ninja warrior").delete()
article.content = "This is updated content for the test article."
article.save()
otherarticle.to_folder("abc")
deletearticle.delete()
article.get(client) # all folders
```

#### Companies

```python
newcompany = client.companies.create(payload={"name": f"Test Company"})
othercompany = client.companies("frank's franks")
newcompany.name = "Updated Test Company"
othercompany.assign_parent(newcompany)
tertiarycompany=clent.companies.list()[-1]
tertiarycompany.delete()
company.get(client) # all companies
```

#### Folders

```python
specificfolder = client.folders.get()
client.folders.get(5)
specificfolder.add_article(5)
specificfolder.add_article(otherarticle)
Folder.get(client)            # all folders
Folder.get(client, 5)         # one folder
client.folders.get(name="IT")  # filtered list
```

#### IPAM objects

```
network = client.networks.create(payload={"company_id": 5, "address":"192.168.11.0/24", "name": f"Test Network {str(uuid.uuid4())[:8]}"})
address = client.ipaddresses.create(payload={"company_id": 5, "network_id": network.id, "address": f"192.168.11.{str(uuid.uuid4().int)[:2]}"})

address.delete()
network.delete()
```


#### Passwords and Password Folders

```python
newpassword = client.asset_passwords.create(payload={"company_id": 5, "name": f"Test Password {str(uuid.uuid4())[:8]}", "username": "testuser", "password": "testpass"})
newpassword.name = f"Updated Test Password {str(uuid.uuid4())[:8]}"
newpassword.save()

passwordfolder = client.password_folders.create(payload={"company_id": 5, "name": f"Test Password Folder {str(uuid.uuid4())[:8]}","security": "all_users"})
newpassword.to_folder(passwordfolder)

otherpasswordfolder = client.password_folders.create(payload={"company_id": 5, "name": f"Other Password Folder {str(uuid.uuid4())[:8]}","security": "all_users"})
newpassword.to_folder(otherpasswordfolder.id)

newpassword.delete()
```

#### Websites

```python
newwebsite.name = f"https://{str(uuid.uuid4())[:8]}"
newwebsite.save()

newwebsite.delete()
print(f"deleted website with id {newwebsite.id}")
```

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
