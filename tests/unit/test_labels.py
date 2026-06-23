"""Label and label type resource/model helpers."""

from unittest.mock import MagicMock

import pytest

from hudu_magic.endpoints import HuduEndpoint
from hudu_magic.models import Article, Asset, LabelType
from hudu_magic.resources import LabelTypesResource, LabelsResource
from hudu_magic.validation import HuduValidationError, validate_labelable_type


def test_validate_labelable_type_accepts_known_types():
    assert validate_labelable_type("Article") == "Article"
    assert validate_labelable_type("Asset") == "Asset"


def test_validate_labelable_type_rejects_unknown():
    with pytest.raises(HuduValidationError, match="Invalid labelable_type"):
        validate_labelable_type("Company")


def test_labels_assign_builds_create_payload():
    client = MagicMock()
    client.create = MagicMock(return_value={"id": 99})
    res = LabelsResource(client)

    article = Article(client, HuduEndpoint.ARTICLES, {"id": 12})
    label_type = LabelType(client, HuduEndpoint.LABEL_TYPES, {"id": 3, "name": "Priority"})

    res.assign(article, label_type, user_id=7)

    client.create.assert_called_once()
    ep, payload = client.create.call_args[0]
    assert ep == HuduEndpoint.LABELS
    assert payload == {
        "label_type_id": 3,
        "labelable_type": "Article",
        "labelable_id": 12,
        "user_id": 7,
    }


def test_labels_list_for_scopes_to_object():
    client = MagicMock()
    client.get = MagicMock(return_value=[])
    res = LabelsResource(client)

    asset = Asset(client, HuduEndpoint.ASSETS, {"id": 5})
    res.list_for(asset, label_type_id=2)

    client.get.assert_called_once()
    ep, = client.get.call_args[0]
    assert ep == HuduEndpoint.LABELS
    assert client.get.call_args[1]["params"] == {
        "labelable_type": "Asset",
        "labelable_id": 5,
        "label_type_id": 2,
    }


def test_labels_strip_deletes_matching_labels():
    client = MagicMock()
    client.delete = MagicMock(return_value=None)
    res = LabelsResource(client)

    label_a = MagicMock()
    label_a.id = 10
    label_b = MagicMock()
    label_b.id = 11
    res.list = MagicMock(return_value=[label_a, label_b])

    article = Article(client, HuduEndpoint.ARTICLES, {"id": 4})
    removed = res.strip(article, label_type=8)

    assert len(removed) == 2
    assert client.delete.call_count == 2


def test_article_assign_label_delegates_to_resource():
    client = MagicMock()
    client.labels.assign = MagicMock(return_value={"id": 1})
    article = Article(client, HuduEndpoint.ARTICLES, {"id": 2})

    article.assign_label(9)

    client.labels.assign.assert_called_once_with(
        to_object=article,
        label_type=9,
        user_id=None,
    )


def test_article_strip_labels_delegates_to_resource():
    client = MagicMock()
    client.labels.strip = MagicMock(return_value=[])
    article = Article(client, HuduEndpoint.ARTICLES, {"id": 2})

    article.strip_labels()

    client.labels.strip.assert_called_once_with(
        to_object=article,
        label_type=None,
    )


def test_label_type_assign_to_delegates_to_object():
    client = MagicMock()
    label_type = LabelType(client, HuduEndpoint.LABEL_TYPES, {"id": 3})
    article = Article(client, HuduEndpoint.ARTICLES, {"id": 2})
    article.assign_label = MagicMock(return_value={"id": 1})

    label_type.assign_to(article, user_id=5)

    article.assign_label.assert_called_once_with(label_type, user_id=5)


def test_label_types_create_validates_applicable_record_types():
    client = MagicMock()
    client.create = MagicMock(return_value={"id": 1})
    res = LabelTypesResource(client)

    res.create(
        {
            "name": "Status",
            "color": "#ff0000",
            "applicable_record_types": ["Article", "Asset"],
        }
    )

    client.create.assert_called_once()
    payload = client.create.call_args[0][1]
    assert payload["applicable_record_types"] == ["Article", "Asset"]


def test_to_labelable_ref_rejects_non_labelable():
    from hudu_magic.models import Company

    client = MagicMock()
    company = Company(client, HuduEndpoint.COMPANIES, {"id": 1})

    with pytest.raises(ValueError, match="not labelable"):
        company.to_labelable_ref()


def test_base_resource_label_helpers_delegate_to_labels():
    from hudu_magic.resources import ArticlesResource

    client = MagicMock()
    client.labels.assign = MagicMock(return_value={"id": 1})
    client.labels.list_for = MagicMock(return_value=[])
    client.labels.strip = MagicMock(return_value=[])

    article = Article(client, HuduEndpoint.ARTICLES, {"id": 2})
    label_type = LabelType(client, HuduEndpoint.LABEL_TYPES, {"id": 3})
    res = ArticlesResource(client)

    res.add_label(article, label_type, user_id=4)
    res.list_labels(article, label_type)
    res.strip_labels(article)

    client.labels.assign.assert_called_once_with(
        article, label_type, user_id=4
    )
    client.labels.list_for.assert_called_once_with(
        article, label_type_id=3
    )
    client.labels.strip.assert_called_once_with(article, label_type=None)
