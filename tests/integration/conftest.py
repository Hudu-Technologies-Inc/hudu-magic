import os

import pytest
from dotenv import load_dotenv

from hudu_magic import HuduClient

load_dotenv("testenv")


def _get_test_config():
    api_key = os.getenv("HUDU_TEST_API_KEY")
    instance_url = os.getenv("HUDU_TEST_INSTANCE")
    return api_key, instance_url


@pytest.fixture(scope="session")
def integration_client():
    api_key, instance_url = _get_test_config()

    if not api_key or not instance_url:
        pytest.skip(
            "Integration test credentials not set (copy testenv.example to testenv "
            "and set HUDU_TEST_API_KEY, HUDU_TEST_INSTANCE)"
        )

    return HuduClient(
        api_key=api_key,
        instance_url=instance_url,
    )

