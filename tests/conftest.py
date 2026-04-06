import os

import pytest


def pytest_collection_modifyitems(config, items):
    run_integration = os.getenv("HUDU_RUN_INTEGRATION") == "1"
    skip_integration = pytest.mark.skip(
        reason="Set HUDU_RUN_INTEGRATION=1 to run integration tests"
    )
    for item in items:
        if "integration" in item.keywords and not run_integration:
            item.add_marker(skip_integration)
