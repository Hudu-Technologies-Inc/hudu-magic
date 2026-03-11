from hudu_magic import HuduClient, HuduEndpoint

client = HuduClient(
    api_key="your-api-key",
    instance_url="https://your-instance.hudu.app",
)

for endpoint in HuduEndpoint:
    print(f"\n=== {endpoint.name} ({endpoint.endpoint}) ===")

    try:
        data = client.get(endpoint)

        print(data)

    except Exception as e:
        print(f"ERROR: {e}")
