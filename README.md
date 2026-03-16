# hudu-magic

purposefully tiny, enum-driven, and class-based API client library for Hudu

**Low-Maintenance, generated from openapi spec**

---

# Getting Started - Installing

## Installing Python

#### Windows 11 Windows 10 version 2004 or newer with (May 2020 Update, which contains winget) Windows 8.1 (non-ARM architecture) with (May 2020 Update, which contains winget)

```powershell
. .\install-python.ps1
```

#### Linux and MacOS
Ubuntu, Debian, Linux mint, MX Linux, Zorin OS, Pop! OS, KDE Neon, Antix, or any other Debian-based distro that uses apt for package management can run the start.sh bash script.

```bash/zsh/csh/sh
chmod +x ./install-python.sh && ./install-python.sh
```

---

## Install hudu-magic package in Python
if you already have python 3.11 - 3.14, you can install to system packages or your virtual environment packages (reccomended) with:

for now, first build with the below script
```
./build.sh
```

after this is published to pypi:

```bash
pip install hudu-magic
```

---

## Generating builds for new Hudu versions or previous versions

1. Place openapi spec file https://yoururl.huducloud.com/api-docs.json in project directory as hudu-openapiv1.json

2. run `python generate-endpoints.py` after sourcing virtual environment (that has dev dependencies installed)

3. run `./build.sh` or `.\build.ps1`

this is designed to be suyper simple so that subsequent releases can eventually just be automatically generated, tested, validated, and pushed to pypi.

#### Note on Building:

unit tests and integration tests run during build, so if you want the integration tests to actually run (and succeed), ensure you've filled out testenv from template testenv.example.

---

# Usage Info and Guide

There are several examples in the examples folder that might be helpful if you're just starting out

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

#### Relations

If any object can be related to/from, you can call relations.create to create a new relation


```
newrelation = client.relations.create(from_obj=newasset, to_obj=newwebsite)
```

Or, often easier, you can call

```
object.relate_to(otherobject)
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
