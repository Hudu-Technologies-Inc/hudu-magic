import uuid
from pathlib import Path
from hudu_magic import HuduClient
client = HuduClient(
    api_key="yourkeyfromenv",
    instance_url="yourinstanceurlfromenv",
)
# this contains various typical tasks and examples of how to use the library
# its somewhat of a scratch-pad of examples
# TODO: clean this up and make it more useful, organized

mycompany = client.companies.get(1)

myexports = client.exports.list()
print("exports:", len(myexports))

newexport = client.exports.start(format="pdf", company_id=1, asset_layout_ids=[2],
    include_passwords= True,
    include_websites= True,
    include_articles= True,
    include_archived_articles= True,
    include_archived_passwords= True,
    include_archived_websites= True,
    include_archived_assets= True,
    )
print("new export:", newexport.id)

# Readiness matches Save-HuduExports: wait for non-empty download_url, not a specific status string.
ready = client.exports.wait_until_downloadable(newexport, interval=2.0, timeout=3600)
print("export ready:", ready.get("status"), "download_url set:", bool(ready.get("download_url")))
download = client.exports.download(ready)
print("downloaded export to:", download)


companyprocedures = mycompany.list_procedures()

procedures = client.procedures.list()


print("procedures:", len(procedures))
print(f"company procedures ({mycompany.name}):", len(companyprocedures))
for proc in procedures:
    print(f"Procedure: {proc.id} - {proc.name} - Run: {proc.is_run}; tasks: {len(proc.tasks)}")

for proce in companyprocedures:
    print(f"Company Procedure: {proce.id} - {proce  .name} - Run: {proce.is_run}; tasks: {len(proce.tasks)}")
    if proce.is_run:
        continue
    else:
        proce.kickoff()
        print(f"kicked off tasks for {proce.id}")

myprocedure = client.procedures.create(payload={"name": "asdf", "company_id": 1})
myprocedure.add_task(name="newtask", auto_kickoff=True)

# Must have procedure_id (or use procedure.add_task on one Procedure)
client.procedure_task.create(name="newtask", procedure_id=myprocedure.id)


# One procedure only — not on .list() results
proc = client.procedures.get(id=1)
proc.add_task(name="Step 1", auto_kickoff=True)
exports = client.exports.list()
print(f"exports: {len(exports)}")

company = client.companies.get(5)
articles = company.list_articles()
# articles.archive()
company.create_article(name=f"SDK Test Article {str(uuid.uuid4())[:8]}", content="This is a test article.")
print("company:", company.id, company.name)
asset = company.create_asset(
    name=f"SDK Test Asset {str(uuid.uuid4())[:8]}",
    asset_layout_id=2,
)
print("created:", asset.id, asset.name, asset.company_id)
asset_from_get = client.assets.get(id=asset.id)
print("got:", asset_from_get.id, asset_from_get.name, asset_from_get.company_id)
asset_from_get.update(name=f"Updated {str(uuid.uuid4())[:8]}")
print("updated:", asset_from_get.id, asset_from_get.name)
asset_from_get.archive()
print("archived")
asset_from_get.unarchive()
print("unarchived")
asset_from_get.delete()  # or resource delete if needed
asset = client.assets.get(id=66)
asset.update({"name": f"Test Asset {str(uuid.uuid4())[:8]}"})
asset.save()
print("updated asset using dict")
asset.name = f"Test Asset {str(uuid.uuid4())[:8]}"
asset.save()
print("updated asset using attribute")
asset.list_for_company()
print("listed assets for company with id 5 using asset-self: ", asset.list_for_company())
asset.list_for_company(5)
company = client.companies.get(5)
print("listed assets for company with id 5 using company id: ", asset.list_for_company(5))
companylist = asset.list_for_company(company)
print("listed assets for company with id 5 using direct company object: ", asset.list_for_company(company))
company.create_asset(name="Router", asset_layout_id=2)
assetlayouts = client.asset_layouts.list()
print(f"listed {len(assetlayouts)} asset layouts")
print(client.asset_layouts.get(2))
newcompanyforu= client.companies.create(payload={"name": f"Test Company {str(uuid.uuid4())[:8]}"})
print(f"created company with id {newcompanyforu.id}")
print(client.check_version())
print(client.version)
uploads = client.uploads.list()
print(f"listed {len(uploads)} uploads")
procedures = client.procedures.list()
print(f"listed {len(procedures)} procedures")
proceduretasks = client.procedure_tasks.list()
print(f"listed {len(proceduretasks)} procedure tasks")
users = client.users.list()
print(f"listed {len(users)} users")
groups = client.groups.list()
print(f"listed {len(groups)} groups")
magic_dashes = client.magic_dashes.list()
print(f"listed {len(magic_dashes)} magic dashes")
lists = client.lists.list()
print(f"listed {len(lists)} lists")
expirations = client.expirations.list()
print(f"listed {len(expirations)} expirations")
flags = client.flags.list()
print(f"listed {len(flags)} flags")
flagtypes = client.flag_types.list()
print(f"listed {len(flagtypes)} flag types")
fileupload = "/Users/masonstelter/Downloads/Installing_twain_imaging_devices002.png"
newasset = client.assets.create(company_id=5, payload={"name": "Router", "asset_layout_id": 2},)
print(f"created {newasset.name} with id {newasset.id}")
newname = f"Router {str(uuid.uuid4())[:8]}"
print(f"updating name to {newname}")
newasset.name = newname
newasset.save()
print(f"updated {newasset.name} with id {newasset.id}")
newasset.add_public_photo(fileupload)
print(f"added public photo with file {fileupload} to asset with id {newasset.id}")
companyassets = client.assets.list_for_company(5)
print(f"listed {len(companyassets)} assets for company with id 5")
article = client.articles.create(payload={"name":"asdfasdf", "content": "This is a test article.", "company_id":5})
print(f"created article with id {article.id}")
article.content = "This is updated content for the test article."
article.save()
print(f"updated article with id {article.id}, new content: {article.content}")
article.add_photo(fileupload, caption="This is a test photo for the article.")
newcompany = client.companies.create(payload={"name": f"Test Company {str(uuid.uuid4())[:8]}"})
print(f"created company with id {newcompany.id}")
newcompany.name = f"Updated Test Company {str(uuid.uuid4())[:8]}"
newcompany.save()
print(f"updated company with id {newcompany.id}, new name: {newcompany.name}")
newcompany.delete()
print(f"deleted company with id {newcompany.id}")
newpassword = client.asset_passwords.create(payload={"company_id": 5, "name": f"Test Password {str(uuid.uuid4())[:8]}", "username": "testuser", "password": "testpass"})
print(f"created password with id {newpassword.id}")
newpassword.name = f"Updated Test Password {str(uuid.uuid4())[:8]}"
newpassword.save()
print(f"updated password with id {newpassword.id}, new name: {newpassword.name}")
passwordfolder = client.password_folders.create(payload={"company_id": 5, "name": f"Test Password Folder {str(uuid.uuid4())[:8]}","security": "all_users"})
print(f"created password folder with id {passwordfolder.id}")
newpassword.to_folder(passwordfolder)
print(f"added password with id {newpassword.id} to folder with id {passwordfolder.id}")
otherpasswordfolder = client.password_folders.create(payload={"company_id": 5, "name": f"Other Password Folder {str(uuid.uuid4())[:8]}","security": "all_users"})
print(f"created other password folder with id {otherpasswordfolder.id}")
newpassword.to_folder(otherpasswordfolder)
print(f"moved password with id {newpassword.id} to folder with id {otherpasswordfolder.id}")
newpassword.delete()
print(f"deleted password with id {newpassword.id}")
newwebsite = client.websites.create(payload={"company_id": 5, "name": f"https://{str(uuid.uuid4())[:8]}", "notes": "https://example.com"})
print(f"created website with id {newwebsite.id}")
newwebsite.upload_to(fileupload)
print(f"uploaded file {fileupload} to website with id {newwebsite.id}")
newwebsite.name = f"https://{str(uuid.uuid4())[:8]}"
newwebsite.save()
print(f"updated website with id {newwebsite.id}, new name: {newwebsite.name}")
folder = client.folders.new(payload={"company_id": 5, "name": f"Test Folder {str(uuid.uuid4())[:8]}"})
print(f"created folder with id {folder.id}")
folder.name = f"Updated Test Folder {str(uuid.uuid4())[:8]}"
folder.save()
print(f"updated folder with id {folder.id}, new name: {folder.name}")
article.to_folder(folder)
network = client.networks.create(payload={"company_id": 5, "address":"192.168.11.0/24", "name": f"Test Network {str(uuid.uuid4())[:8]}"})
address = client.ipaddresses.create(payload={"company_id": 5, "network_id": network.id, "address": f"192.168.11.{str(uuid.uuid4().int)[:2]}"})
print(f"created network with id {network.id} and address {network.address}")
print(f"created ip address with id {address.id} and address {address.address}")
vlan = client.vlans.create(payload={"company_id": 5, "vlan_id": 100, "name": f"Test VLAN {str(uuid.uuid4())[:8]}"})
vlanzone = client.vlan_zones.create(payload={"company_id": 5, "vlan_id_ranges": "100-200", "name": f"Test VLAN Zone {str(uuid.uuid4())[:8]}"})
print(f"created vlan with id {vlan.id} and vlan_id {vlan.vlan_id}")
print(f"created vlan zone with id {vlanzone.id} and vlan_id_ranges {vlanzone.vlan_id_ranges}")
vlan.description = f"Updated Test VLAN {str(uuid.uuid4())[:8]}"
vlan.save()
print(f"updated vlan with id {vlan.id} and vlan_id {vlan.vlan_id}, new description: {vlan.description}")
vlanzone.description = f"Updated Test VLAN Zone {str(uuid.uuid4())[:8]}"
vlanzone.save()
print(f"updated vlan zone with id {vlanzone.id}")
vlan.delete()
vlanzone.delete()
print(f"deleted vlan with id {vlan.id} and vlan zone with id {vlanzone.id}")
uploads = client.uploads.list()
photos = client.photos.list()
public_photos = client.public_photos.list()
relations = client.relations.list()
print(f"listed {len(uploads)} uploads, {len(photos)} photos, {len(public_photos)} public photos, and {len(relations)} relations")
asset_website_relation = client.relations.create(from_obj=newasset, to_obj=newwebsite)
print(f"created relation with id {asset_website_relation.id} from asset with id {newasset.id} to website with id {newwebsite.id}")
print(asset_website_relation.to_dict())
print(newasset.list_relations())
listrelations = newasset.list_relations()
print(f"listed {len(listrelations)} relations for asset with id {newasset.id}")
otherrelation= address.relate_to(article)
print(f"related ip address with id {address.id} to article with id {article.id} for a relation with id {otherrelation.id}")
upload = client.uploads.create(file_path=fileupload, to_object=newasset)
print(f"created upload with id {upload.id} for file {fileupload} {upload.name} related to asset with id {newasset.id}")
photo_two = client.public_photos.create(file_path=fileupload, to_object=article)
print(f"created public photo with id {photo_two.id} for file {fileupload} related to article with id {article.id}")
photosforarticle = article.list_photos()
print(f"listed {len(photosforarticle)} photos for article with id {article.id}")
uploadsforasset = newasset.list_uploads()
print(f"listed {len(uploadsforasset)} uploads for asset with id {newasset.id}")
print("RELATION CREATED:")
print(otherrelation.to_dict() if hasattr(otherrelation, "to_dict") else otherrelation)
print("UPLOAD CREATED:")
print(upload.to_dict() if hasattr(upload, "to_dict") else upload)
print("ASSET REF TYPE:", newasset.to_relation_ref())
print("ASSET UPLOAD TYPE:", newasset.to_upload_ref())
print("ASSET ID:", newasset.id)
photo_three= client.photos.create(file_path=fileupload, to_object=article, caption="ayyyyu")
print(f"created photo with id {photo_three.id} for file {fileupload} related to article with id {article.id}, with caption: {photo_three.caption}")
try:
    Path("./Installing_twain_imaging_devices002.png").unlink()
except FileNotFoundError:
    pass
download = client.uploads.download(upload)
print(f"downloaded upload with id {upload.id} to path {download}")
try:
    Path("./Installing_twain_imaging_devices002.png").unlink()
except FileNotFoundError:
    pass
address.delete()
network.delete()
print(f"deleted network with id {network.id} and address {network.address}")
article.delete()
print(f"deleted article with id {article.id}")
# newasset.delete()
# print(f"deleted asset with id {newasset.id}")
newwebsite.delete()
print(f"deleted website with id {newwebsite.id}")
upload.delete()
print(f"deleted upload with id {upload.id}")
procedures = client.procedures.list()
print(f"listed {len(procedures)} procedures")
proceduretasks = client.procedure_tasks.list()
print(f"listed {len(proceduretasks)} procedure tasks")
users = client.users.list()
print(f"listed {len(users)} users")
groups = client.groups.list()
print(f"listed {len(groups)} groups")
magic_dashes = client.magic_dashes.list()
print(f"listed {len(magic_dashes)} magic dashes")
lists = client.lists.list()
print(f"listed {len(lists)} lists")
expirations = client.expirations.list()
print(f"listed {len(expirations)} expirations")
flags = client.flags.list()
print(f"listed {len(flags)} flags")
flagtypes = client.flag_types.list()
print(f"listed {len(flagtypes)} flag types")
rackstorages= client.rack_storages.list()
print(f"listed {len(rackstorages)} rack storages")
