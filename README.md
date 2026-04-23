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

### Exports

#### starting a CSV or PDF export

```python
newexport = client.exports.start(format="pdf", company_id=1, asset_layout_ids=[2],
    include_passwords= True,
    include_websites= True,
    include_articles= True,
    include_archived_articles= True,
    include_archived_passwords= True,
    include_archived_websites= True,
    include_archived_assets= True,
    )
```

client.Exports.new() is aliased to client.Exports.start()
```python
csvexport = client.exports.start(format="csv",company_id=mycompany.id)
pdfexport = client.exports.start(format="pdf",company_id=mycompany.id)
```


##### Friendly defaults on create

the include_* options here default to true if not provided

the asset layout array defaults to all layouts found with `HuduClient.asset_layouts.list` are included.

#### Checking status of export

blocking-check on export status

```python
ready = client.exports.wait_until_downloadable(newexport, interval=2.0, timeout=3600)
someexport.wait_until_downloadable(interval=5.0, timeout=600)
```

#### downloading exports

```python
download = client.exports.download(newexport.id, "/home/myoutputfolder")
download = client.exports.download(otherexportobject) # download to current working dir
someexportobject.download() # download to current working dir
myexportobject.download("/home/myoutputfolder")
```


### Procedures (processes) and tasks

The API and OpenAPI 2.41.0 use **process** / **run** wording; this library still exposes `Procedure` / `procedure_tasks` and the `client.procedure` / `client.procedure_tasks` aliases (`client.process`, `client.tasks`, etc.).

```python
myprocedure.kick_off()
myprocedure.kickoff()
myprocedure.start()

myprocedure.is_run #bool property

companyprocedures = mycompany.list_procedures()
procedures = client.procedures.list()

myprocedure = client.procedures.create(payload={"name": "asdf", "company_id": 1})
myprocedure.add_task(name="newtask", auto_kickoff=True)

client.procedure_task.create(name="newtask", procedure_id=myprocedure.id)

# One procedure only — not on .list() results
proc = client.procedures.get(id=1)
proc.add_task(name="Step 1", auto_kickoff=True)

someprocedure.list_tasks()
someotherprocedure.tasks

sometask.assign_to(mypersonaluser)
```

Calling `kick_off`, `kickoff`, or `start` returns a new **run** (still a `Procedure` with `is_run` true). Runs share the same model as templates but behave differently for tasks.

Use `is_run` to tell a template from a run.

**Creating tasks** (`POST /procedure_tasks`) is for **process** (template) tasks only: supported body fields include `name`, `description`, `procedure_id`, `position`, `optional`, and `parent_task_id`. You cannot set assignees or run-only fields on create; kick off the process first, then set **`due_date`**, **`priority`**, and **`assigned_users`** on the **run** task via `PUT /procedure_tasks/{id}`, or use `Users.assign_task` (which updates `assigned_users` on the run task).

**Updating a procedure/run** (`PUT /procedures/{id}`) accepts **`name`**, **`description`**, and **`archived`** (company processes only for archiving). It no longer accepts moving a process between companies via **`company_id`** or legacy **`company_template`** on PATCH—use create/duplicate flows per Hudu’s API.

`POST` / `PUT` `/procedures` use a **flat** JSON body (`{"name": "...", "company_id": ...}`), not a nested `procedure` object—this matches Hudu **2.39.6+** and avoids `422` “Name can’t be blank” if the server ignored the old wrapper.

Paginated **`GET /procedures`** responses are normalized to a **`HuduCollection`** even when only one row is returned (so `len()` is a row count and `for p in …` yields `Procedure` objects, not attribute names). List payloads may use **`procedures`** or **`processes`** as the collection key.

`Procedure.save()` sends only those allowed fields so validation matches the spec.

Use **`Procedure.add_task(...)`** to create a template task (optional **`auto_kickoff=True`** after create). Run-only fields belong on the run task after kickoff.

### Users

```python
myuser.assign_task(thistask)
myotheruser.assign_task(client.procedure_tasks.get(56))
```

You can assign a run task from a `Users` instance or call `task.assign_to(user)`; both use `assigned_users` on the run task.

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

- v0.3.2410 - Apr 21, 2026; Procedures `POST`/`PUT` send a **flat** JSON body (no `procedure` wrapper), Paginated lists always return **`HuduCollection`** (removed previous single-page `len`/iteration quirks); accept **`processes`** list key on GET; add **`Procedure.add_task`**. README Re-aligned with process/run task rules; `Procedure.save`/`update`/`delete` use `PROCEDURES_ID` and allowed PATCH fields; `PROCEDURE_TASK_RUN_ONLY_FIELDS` no longer lists removed `user_id` update key. **`BaseResource.create` / `update`**: optional `payload` (kwargs-only body fields supported); `validate` / `allow_unknown_fields` are not merged into JSON.

- v0.4.2410.post1 - Added better support for exports, aliased create methods for exports to `new()` and `start()`. Added kind defaults to these and extended resource from `BaseFileResource` to allow for downloading. Lastly, added blocking method that until an export is ready for download. [PEP440 suffix noted for tag adjustment.]
