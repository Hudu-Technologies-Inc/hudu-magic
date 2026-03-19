# hudu-magic

A **tiny, enum-driven, class-based Python API client** for Hudu.

- Minimal dependencies  
- Generated from OpenAPI  
- Low Maintenance
- Designed for clarity and maintainability  


---

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

# Quick Start

```python
from hudu_magic import HuduClient

client = HuduClient(
    api_key="your_api_key",
    instance_url="https://yourinstance.huducloud.com"
)

company = client.companies.create(name="Test Company")

asset = client.assets.create(
    company_id=company.id,
    name="Router",
    asset_layout_id=1,
)

asset.name = "Updated Router"
asset.save()

asset.delete()
```

---

# Installation

## Install package

```bash
pip install hudu-magic
```

Until published:

```bash
./build.sh
pip install dist/*.whl
```

---

# Usage Info and Guide

There are several examples in the examples folder that might be helpful if you're just starting out

# Core Concepts

## Client
Handles auth, requests, pagination, wrapping.

```python
client.assets.list()
```

## Resources
Collection-level operations:
- list()
- get()
- create()
- delete()
- archive()
- unarchive()

## Models (HuduObject)
Instance-level operations:
- save()
- delete()
- refresh()
- relate_to()
- list_photos()
- list_uploads()

```python
asset.save()
asset.delete()
```

---

# Creating Objects

The create base method for all objects is simple. you can specify properties in either the payload object (standard dictionary) or as kwargs (just propertyname=value)

This means you can use either:

### kwargs (recommended)
```python
client.assets.create(name="Router", company_id=1)
```

### dict payload
```python
client.assets.create(payload={"name": "Router", "company_id": 1})
```

---

# Updating Objects

```python
asset.name = "New Name"
asset.save()
```

or

```python
asset.update(name="New Name")
```

---

# Relations

```python
asset.relate_to(website)
```

or

```python
client.relations.create(from_obj=asset, to_obj=website)
```

---

# Uploads

```python
asset.upload_to("file.zip")

uploads = asset.list_uploads()
```

# Photos

```python
asset.add_photo("image.png")

photos = asset.list_photos()
```

---

## Generating builds for new Hudu versions or previous versions

1. Place openapi spec file https://yoururl.huducloud.com/api-docs.json in project directory as hudu-openapiv1.json

2. run `python generate-endpoints.py` after sourcing virtual environment (that has dev dependencies installed)

3. run `./build.sh`

***todo: `.\build.ps1`***

this is designed to be suyper simple so that subsequent releases can eventually just be automatically generated, tested, validated, and pushed to pypi.

#### Note on Building:

unit tests and integration tests run during build, so if you want the integration tests to actually run (and succeed), ensure you've filled out testenv from template testenv.example.

---

# Error Handling, Additional Info / Help


If more information is needed, you can call this method on class members to get all associated info from hudu's API spec-

`huduobject.help()`

for resources like client.huduobject / client.assets, you can call either of these to get information from hudu's OpenAPI spec-

`client.huduobjecttype.describe()` / `client.huduobjecttype.describe()`

or for more-verbose info-

`client.huduobjecttype.help()`

if an object type or resource doesnt support a method call or payload param, you'll be notified of which one(s), if any, are invalid.

# Special Class Methods



## Advanced Use Possibilities

### Multi-Client

You can instantiate two or more client objects, like above, to transfer data from, say, your dev instance to production. This hasn't been extensively tested expecially for objects dependent on companies (assets, passwordfolders)

```python
client2.assets.create(
    **client1.assets.get(6).to_dict()
)
```

# Philosophy

- Simple > clever  
- Explicit > implicit  
- Thin wrapper over Hudu API  

---

# License

MIT

