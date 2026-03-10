def pytest_collection_modifyitems(config, items):
    run_integration = os.getenv("HUDU_RUN_INTEGRATION") == "1"
    skip_integration = pytest.mark.skip(reason="Set HUDU_RUN_INTEGRATION=1 to run integration tests")

    for item in items:
        if "integration" in item.keywords and not run_integration:
            item.add_marker(skip_integration)


def integration_client():
    api_key = os.getenv("HUDU_TEST_API_KEY")
    instance_url = os.getenv("HUDU_TEST_INSTANCE")

    if not api_key or not instance_url:
        pytest.skip("Integration test credentials not set in .testenv")

    return HuduClient(api_key=api_key, instance_url=instance_url)

def test_api_info_live(integration_client):
    result = integration_client.get(HuduEndpoint.APIINFO)
    assert result is not None

def test_companies_list_live(integration_client):
    result = integration_client.get(HuduEndpoint.COMPANIES)
    assert isinstance(result, list)

def test_create_company_live(integration_client):
    name = f"SDK TEST {uuid.uuid4()}"
    payload = {"name": name}

    result = integration_client.create(HuduEndpoint.COMPANIES, payload)

    assert result is not None
    assert name in str(result)