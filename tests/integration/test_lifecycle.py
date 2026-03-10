from __future__ import annotations

import pytest

from .helpers import extract_id, get_nested_value
from .plans import LIFECYCLE_PLANS


@pytest.mark.integration
@pytest.mark.destructive
@pytest.mark.parametrize("plan", LIFECYCLE_PLANS, ids=lambda p: p.name)
def test_resource_lifecycle(integration_client, plan):
    ctx = {
        "client": integration_client,
        "extract_id": extract_id,
    }

    created_id = None

    try:
        create_payload = plan.create_payload(ctx)
        created = integration_client.create(
            plan.endpoint,
            create_payload,
            validate=plan.validate,
        )
        created_id = extract_id(created)

        fetched = integration_client.get(plan.endpoint.item_path(created_id), paginate=False)
        assert extract_id(fetched) == created_id

        update_payload = plan.update_payload(ctx)
        updated = integration_client.update(
            plan.endpoint,
            created_id,
            update_payload,
            validate=plan.validate,
        )

        actual_value = get_nested_value(updated, plan.assert_updated_field)
        assert actual_value == plan.assert_updated_value

    finally:
        if created_id is not None:
            try:
                integration_client.delete(plan.endpoint.item_path(created_id))
            except Exception:
                pass

        if plan.cleanup_hook:
            plan.cleanup_hook(integration_client, ctx)