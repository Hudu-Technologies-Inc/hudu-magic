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
if you already have python 3.11 - 3.9, you can install to system packages or your virtual environment packages (reccomended) with the below command(s).

for now, first build with the below script
```
./build.sh
```

after this is published to pypi:

```bash
pip install hudu-magic
```

hudu-magic is designed to include almost no non-test/dev dependencies and is mainly just regex magic + pure python, so you'll almost never run into dependency or version conflicts when introducing it to a project and it will always be very lightweight.

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

## interacting with HuduObjects

All classes inherit from the base class, HuduObject, and can therefore all do some basic things (with a few exceptions)

member.get() [aliases: .list()]

member.save()

member.keys()

member.contains(string)

member.relate_to(othermember)

member.upload_to(filepath) / member.list_uploads()

member.add_photo() / member.list_photos()

one exception is that, while most objects can be deleted and have .delete() or .delete(id) called from them, asset layouts and a few other object types (users, groups) can't be deleted from Hudu's API, so you'll raise a NotImplementedError.

### Collections



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


```python
newrelation = client.relations.create(from_obj=newasset, to_obj=newwebsite)
```

Or, often easier, you can call

```python
huduobject.relate_to(otherhuduobject)
```


#### Uploads

Similar to relations, this contains a built-in method that can be accessed from instances of uploadable objects

So you can upload like this

```python
upload = client.uploads.create(file_path="somefile.zip", to_object=newasset)
```

or, if easier, you can upload a file with

```python
newasset.Upload_to(somefile.zip)
newwebsite.upload_to(fileupload)
```

you can get the specific uploads associated with an object with

```python
uploadsforarticle = article.list_uploads()
```

uploads can be deleted with

```python
myupload.delete()
```

or 

```python
client.uploads.delete(id)
```

#### Photos and Public Photos

Public Photos can be attributed to an asset or an article and can be added in a few ways-

```python
article.add_photo("mylocalphotopath")
```

or 

```python
client.photos.create(file_path="filepath", to_object=article, caption="mycaption")
```

you can also filter photos or uploads by an instance of an object
like

```python
photosforarticle = article.list_photos()
```

photos can be deleted with

```python
myphoto.delete()
client.photos.delete(id)
```

public photos have similar methods but can only be attributed to assets or articles

```python
newasset.add_public_photo(fileupload)
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
client.websites.create(payload={name="https://yourwebsite.org"})
newwebsite.name = f"https://yourwebsite.net"
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
```

## Advanced Use Possibilities

You can instantiate two or more client objects, like above, to transfer data from, say, your dev instance to production

Before doing as much or similar, be sure that you aren't better off leveraging Hudu Bridge. For some cases, however, this makes sense.

Since all class members (huduobjects) are isomorphic and known-unwanted payload keys are poppeed during creates/post/put are dropped, so long as you're on the same hudu version, you should be able to do things like:

```
client2.assets.create(client1.assets.get(6))
```