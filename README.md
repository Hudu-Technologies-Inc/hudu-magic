# hudu-magic

A **tiny, enum-driven, class-based Python API client** for Hudu.

- Minimal dependencies (requests)
- Generated from OpenAPI  
- Low Maintenance
- Designed for clarity and maintainability


---

[PyWheels](https://www.piwheels.org/project/hudu-magic/)

[PyPi](https://pypi.org/project/hudu-magic/)

---

# Quick Start

```python
from hudu_magic import HuduClient

client = HuduClient(
    api_key="your_api_key",
    instance_url="https://yourinstance.huducloud.com"
)

company = client.companies.create(name="Test Company")

# Use a real asset_layout_id from your Hudu instance (e.g. from client.asset_layouts.list()).
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
---

# Usage Info and Guide

There are several examples in the examples folder that might be helpful if you're just starting out

# Core Concepts

## Client
Handles auth, requests, pagination, wrapping.

```python
client.assets.list()
```

## Collections
Collection-level operations:
- list()
- get()
- create()
- delete()
- archive()
- unarchive()

```python
assetsforcompany.save()
assetsforcompany.delete()
assetsforcompany.archive()
```

## Models (HuduObject)
Instance-level operations:
- save()
- delete()
- refresh()
- relate_to()
- list_photos()
- list_uploads()
- relate_to()
- upload_to()

```python
asset.save()
asset.delete()
```

## Special Model Methods

### Assets

```python
someasset.add_public_photo("smile.png")
someasset.add_photo("dogslaughing.jpeg")
```

some objects can be attributed directly to or uploaded to assets

### Companies

```python
mycompany.list_assets()
mycompany.list_articles()
mycompany.list_passwords()
mycompany.list_procedures()
mycompany.list_websites()
mycompany.list_folders()
mycompany.list_password_folders()


mycompany.create_website()
mycompany.create_password()
mycompany.create_procedure()
mycompany.create_article()
mycompany.create_asset()
```

objects that require or can be attributed to a company often can be listed or created directly from a company object

### Procedures and Tasks

```python
myprocedure.kick_off()
myprocedure.kickoff()
myprocedure.start()

myprocedure.is_run

someprocedure.list_tasks()
someotherprocedure.tasks
myprocedure.tasks[0].assign(ouruser)
client.procedure_tasks.get(5).assign(ourotheruser)

sometask.assign_user(mypersonaluser)
```

Starting a procedure with start, kick_off or kickoff methods results in new procedure [as-a-run] object. Runs still are procedures, and use the same model, but they and their tasks are slightly different.


you can call `is_run` property (bool) on a procedure to check if it has been started (and therefore, a run)

procedures that have tasks created already will have a huducollection of procedure_task

proceduretasks can be assigned if the parent procedure has been started. like 'assigned_users', a task can only be assigned 'due_date', 'priority',

you can assign a user using a user's id or a user object directly.

### Users

```python
myuser.assign_task(thistask)
myotheruser.assign_task(client.proceduretasks.get(56))
```

you can assign a task directly to a user object

### Others

there are many other handy and helpful class methods and many more that are planned. Whenever possible, I'll update this section with specific examples.



---

# Creating Objects

The create base method for all objects is simple. you can specify properties in either the payload object (standard dictionary) or as kwargs (just propertyname=value)

This means you can use either:

### kwargs (recommended)
```python
client.assets.create(name="Router", company_id=1, asset_layout_id=10)
```

### dict payload
```python
client.assets.create(payload={"name": "Router", "company_id": 1, "asset_layout_id": 10})
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

2. run `python generate_endpoints.py` after sourcing virtual environment (that has dev dependencies installed)

3. run `./build.sh`

***todo: `.\build.ps1`***

this is designed to be super simple so that subsequent releases can eventually just be automatically generated, tested, validated, and pushed to pypi.

#### Note on building and tests

- Run tests with `./build.sh --test` (or `pytest` from a dev environment with `pip install -e ".[dev]"`).
- Integration tests are skipped unless you set `HUDU_RUN_INTEGRATION=1`. With that set, copy `testenv.example` to `testenv` and fill in `HUDU_TEST_API_KEY` and `HUDU_TEST_INSTANCE`.

---

# Error Handling, Additional Info / Help


If more information is needed, you can call this method on class members to get all associated info from hudu's API spec-

`huduobject.help()`

For resources such as `client.assets`, you can call:

`client.assets.describe()`

or for more verbose info:

`client.assets.help()`

if an object type or resource doesnt support a method call or payload param, you'll be notified of which one(s), if any, are invalid.


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

---

# Versioning convention

PyPI releases use a **library** SemVer prefix and a numeric suffix derived from the **Hudu OpenAPI spec** used to generate `HuduEndpoint` and related code:

`MAJOR.MINOR.HUDUSPECVERSION`

- **`MAJOR` / `MINOR`** — reserved for this Python package (breaking API changes, larger feature sets, and so on).
- **`HUDUSPECVERSION`** — encodes the spec’s `(major, minor, patch)` as a single integer:

  `hudu_spec_major * 1000 + hudu_spec_minor * 10 + hudu_spec_patch`

  Example: OpenAPI **2.41.0** → `2 * 1000 + 41 * 10 + 0` = **2410** → package segment **0.1.2410** (with `0.1` as the current library prefix).

When Hudu publishes a new spec, regenerate and bump **`HUDUSPECVERSION`** accordingly. For **Python-only** fixes (same spec, no regeneration), prefer a **PEP 440** suffix such as `0.1.2410.post1` so the encoded spec stays honest.

**Spec used for the current release:** Hudu OpenAPI **2.41.0** (as of 2026-04-06). The canonical package version is in `pyproject.toml`.

# History

## Hudu 2.41.0 Spec

- v0.1.2410 - Apr 6, 2026; Initial Release

- v0.2.2410 - Apr 7, 2026; added validation, differentiation for procedure-vs-run and task-vs-runtask, as well as some helpful class methods.

- v0.2.2410.post1 - Apr 21, 2026; Recent topical changes to verbiage, descriptions, for process runs / procedures

