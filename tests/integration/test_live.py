import uuid

import pytest

from hudu_magic import HuduClient
from hudu_magic.endpoints import HuduEndpoint

from .random_layout import random_asset_layout_payload


@pytest.mark.integration
def test_api_info_live(integration_client):
    api_info_result = integration_client.get(HuduEndpoint.API_INFO)
    assert api_info_result is not None


@pytest.mark.integration
def test_companies_list_live(integration_client):
    companies_result = integration_client.get(HuduEndpoint.COMPANIES)
    assert isinstance(companies_result, list)


@pytest.mark.integration
def test_create_company_live(integration_client):
    name = f"SDK TEST {uuid.uuid4()}"
    payload = {"name": name}

    create_company_result = integration_client.create(HuduEndpoint.COMPANIES, payload)

    assert create_company_result.name == name


@pytest.mark.integration
def test_create_random_asset_layout(integration_client):
    payload = random_asset_layout_payload()
    result = integration_client.create(
        HuduEndpoint.ASSET_LAYOUTS,
        payload,
        validate=False,
    )

    assert result is not None
