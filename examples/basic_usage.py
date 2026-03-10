from hudu_magic import HuduClient, HuduEndpoint

client = HuduClient(
    api_key="your-api-key",
    instance_url="https://your-instance.hudu.app",
)

companies = client.get_all_pages(HuduEndpoint.COMPANIES)
print(companies)