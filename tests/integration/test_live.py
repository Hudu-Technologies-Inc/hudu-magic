import random
import uuid
from hudu_magic import HuduClient
from hudu_magic.endpoints import HuduEndpoint
from hudu_magic.constants import FIELD_TYPES
from .random_layout import random_asset_layout_payload

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
    api_info_result = integration_client.get(HuduEndpoint.API_INFO)
    assert api_info_result is not None

def test_companies_list_live(integration_client):
    companies_result = integration_client.get(HuduEndpoint.COMPANIES)
    assert isinstance(companies_result, list)

def test_create_company_live(integration_client):
    name = f"SDK TEST {uuid.uuid4()}"
    payload = {"name": name}

    create_company_result = integration_client.create(HuduEndpoint.COMPANIES, payload)

    assert create_company_result.name == name

def test_create_random_asset_layout(integration_client):

    payload = random_asset_layout_payload()
    print(payload)
    result = integration_client.create(
        HuduEndpoint.ASSET_LAYOUTS,
        payload,
        validate=False,
    )

    assert result is not None
