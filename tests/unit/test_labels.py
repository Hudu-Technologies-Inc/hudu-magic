"""Label and label type resource/model helpers."""

from unittest.mock import MagicMock

import pytest

from hudu_magic.endpoints import HuduEndpoint
from hudu_magic.helpers.labels import (
    convert_to_hudu_label_color,
    resolve_canonical_label_color_name,
)
from hudu_magic.models import Article, Asset, HuduCollection, Label, LabelType
from hudu_magic.resources import LabelTypesResource, LabelsResource
from hudu_magic.validation import HuduValidationError, validate_labelable_type


def test_validate_labelable_type_accepts_known_types():
    assert validate_labelable_type("Article") == "Article"
    assert validate_labelable_type("Asset") == "Asset"


def test_convert_to_hudu_label_color_hex_six_digits():
    assert convert_to_hudu_label_color("#6136FF") == "#6136ff"
    assert convert_to_hudu_label_color("6136ff") == "#6136ff"


def test_convert_to_hudu_label_color_strips_alpha():
    assert convert_to_hudu_label_color("#6136ff80") == "#6136ff"
    assert convert_to_hudu_label_color("6136ff80") == "#6136ff"


def test_convert_to_hudu_label_color_expands_three_digit_hex():
    assert convert_to_hudu_label_color("#f0a") == "#ff00aa"
    assert convert_to_hudu_label_color("abc") == "#aabbcc"


def test_convert_to_hudu_label_color_canonical_names():
    assert convert_to_hudu_label_color("red") == "#ff0000"
    assert convert_to_hudu_label_color("light blue") == "#add8e6"
    assert convert_to_hudu_label_color("grau") == "#808080"
    assert resolve_canonical_label_color_name("bleu marine") == "Blue"


def test_convert_to_hudu_label_color_rejects_unknown():
    with pytest.raises(HuduValidationError, match="Invalid color"):
        convert_to_hudu_label_color("not-a-color")


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


def test_labels_assign_accepts_hudu_collection():
    client = MagicMock()
    client.create = MagicMock(
        side_effect=[
            Label(client, HuduEndpoint.LABELS, {"id": 99}),
            Label(client, HuduEndpoint.LABELS, {"id": 100}),
        ]
    )
    res = LabelsResource(client)
    articles = HuduCollection([
        Article(client, HuduEndpoint.ARTICLES, {"id": 1}),
        Article(client, HuduEndpoint.ARTICLES, {"id": 2}),
    ])
    label_type = LabelType(client, HuduEndpoint.LABEL_TYPES, {"id": 3})

    applied = res.assign(articles, label_type)

    assert client.create.call_count == 2
    assert isinstance(applied, HuduCollection)
    assert applied.ids() == [99, 100]


def test_labels_assign_empty_collection_returns_empty_collection():
    client = MagicMock()
    res = LabelsResource(client)

    applied = res.assign(HuduCollection([]), 3)

    client.create.assert_not_called()
    assert applied == HuduCollection([])


def test_labels_strip_accepts_hudu_collection():
    client = MagicMock()
    client.get = MagicMock(
        return_value=[
            Label(client, HuduEndpoint.LABELS, {
                "id": 10,
                "labelable_type": "Article",
                "labelable_id": 1,
                "label_type_id": 8,
            }),
            Label(client, HuduEndpoint.LABELS, {
                "id": 11,
                "labelable_type": "Article",
                "labelable_id": 2,
                "label_type_id": 8,
            }),
        ]
    )
    client.delete = MagicMock(return_value=None)
    res = LabelsResource(client)

    articles = HuduCollection([
        Article(client, HuduEndpoint.ARTICLES, {"id": 1}),
        Article(client, HuduEndpoint.ARTICLES, {"id": 2}),
    ])
    removed = res.strip(articles, label_type=8)

    assert len(removed) == 2
    client.get.assert_called_once()
    assert client.delete.call_count == 2


def test_labels_strip_empty_collection_returns_empty_list():
    client = MagicMock()
    res = LabelsResource(client)

    removed = res.strip(HuduCollection([]))

    assert removed == []


def test_labels_list_for_collection_batches_by_labelable_type():
    client = MagicMock()
    client.get = MagicMock(
        return_value=[
            Label(client, HuduEndpoint.LABELS, {
                "id": 1,
                "labelable_type": "Article",
                "labelable_id": 10,
                "label_type_id": 3,
            }),
            Label(client, HuduEndpoint.LABELS, {
                "id": 2,
                "labelable_type": "Article",
                "labelable_id": 99,
                "label_type_id": 3,
            }),
            Label(client, HuduEndpoint.LABELS, {
                "id": 3,
                "labelable_type": "Article",
                "labelable_id": 11,
                "label_type_id": 3,
            }),
        ]
    )
    res = LabelsResource(client)
    articles = HuduCollection([
        Article(client, HuduEndpoint.ARTICLES, {"id": 10}),
        Article(client, HuduEndpoint.ARTICLES, {"id": 11}),
    ])

    labels = res.list_for_collection(articles, label_type_id=3)

    client.get.assert_called_once()
    assert isinstance(labels, HuduCollection)
    assert labels.ids() == [1, 3]


def test_labels_strip_collection_uses_single_list_per_type():
    client = MagicMock()
    client.get = MagicMock(
        return_value=[
            Label(client, HuduEndpoint.LABELS, {
                "id": 1,
                "labelable_type": "Article",
                "labelable_id": 10,
            }),
            Label(client, HuduEndpoint.LABELS, {
                "id": 2,
                "labelable_type": "Article",
                "labelable_id": 11,
            }),
        ]
    )
    client.delete = MagicMock(return_value=None)
    res = LabelsResource(client)
    articles = HuduCollection([
        Article(client, HuduEndpoint.ARTICLES, {"id": 10}),
        Article(client, HuduEndpoint.ARTICLES, {"id": 11}),
    ])

    removed = res.strip(articles)

    client.get.assert_called_once()
    assert len(removed) == 2
    assert client.delete.call_count == 2


def test_labels_strip_label_types_from_one_list():
    client = MagicMock()
    client.get = MagicMock(
        return_value=[
            Label(client, HuduEndpoint.LABELS, {
                "id": 1,
                "labelable_type": "Article",
                "labelable_id": 4,
                "label_type_id": 3,
            }),
            Label(client, HuduEndpoint.LABELS, {
                "id": 2,
                "labelable_type": "Article",
                "labelable_id": 4,
                "label_type_id": 8,
            }),
            Label(client, HuduEndpoint.LABELS, {
                "id": 3,
                "labelable_type": "Article",
                "labelable_id": 4,
                "label_type_id": 9,
            }),
        ]
    )
    client.delete = MagicMock(return_value=None)
    res = LabelsResource(client)
    article = Article(client, HuduEndpoint.ARTICLES, {"id": 4})
    types = [
        LabelType(client, HuduEndpoint.LABEL_TYPES, {"id": 3}),
        LabelType(client, HuduEndpoint.LABEL_TYPES, {"id": 8}),
    ]

    removed = res.strip_label_types_from(article, types)

    client.get.assert_called_once()
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


def test_label_types_create_normalizes_named_color():
    client = MagicMock()
    client.create = MagicMock(return_value={"id": 1})
    res = LabelTypesResource(client)

    res.create(
        {
            "name": "Status",
            "color": "light green",
            "applicable_record_types": ["Article"],
        }
    )

    payload = client.create.call_args[0][1]
    assert payload["color"] == "#90ee90"


def test_label_types_create_normalizes_hex_with_alpha():
    client = MagicMock()
    client.create = MagicMock(return_value={"id": 1})
    res = LabelTypesResource(client)

    res.create(
        {
            "name": "Status",
            "color": "#6136ff80",
            "applicable_record_types": ["Article"],
        }
    )

    payload = client.create.call_args[0][1]
    assert payload["color"] == "#6136ff"


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


def test_hudu_collection_add_label_applies_to_each_member():
    client = MagicMock()
    article_a = Article(client, HuduEndpoint.ARTICLES, {"id": 1})
    article_b = Article(client, HuduEndpoint.ARTICLES, {"id": 2})
    article_a.add_label = MagicMock(return_value=Label(client, HuduEndpoint.LABELS, {"id": 10}))
    article_b.add_label = MagicMock(return_value=Label(client, HuduEndpoint.LABELS, {"id": 11}))
    label_type = LabelType(client, HuduEndpoint.LABEL_TYPES, {"id": 3})

    articles = HuduCollection([article_a, article_b])
    applied = articles.add_label(label_type)

    article_a.add_label.assert_called_once_with(label_type, user_id=None)
    article_b.add_label.assert_called_once_with(label_type, user_id=None)
    assert isinstance(applied, HuduCollection)
    assert applied.ids() == [10, 11]


def test_hudu_collection_list_labels_flattens_by_default():
    client = MagicMock()
    client.labels = LabelsResource(client)
    client.get = MagicMock(
        return_value=[
            Label(client, HuduEndpoint.LABELS, {
                "id": 10,
                "labelable_type": "Article",
                "labelable_id": 1,
            }),
            Label(client, HuduEndpoint.LABELS, {
                "id": 11,
                "labelable_type": "Article",
                "labelable_id": 2,
            }),
        ]
    )
    article_a = Article(client, HuduEndpoint.ARTICLES, {"id": 1})
    article_b = Article(client, HuduEndpoint.ARTICLES, {"id": 2})

    labels = HuduCollection([article_a, article_b]).list_labels()

    assert isinstance(labels, HuduCollection)
    assert labels.ids() == [10, 11]
    client.get.assert_called_once()


def test_hudu_collection_strip_labels_single_item_delegates_per_object():
    client = MagicMock()
    client.labels = LabelsResource(client)
    client.labels.strip = MagicMock(return_value=["a"])
    article = Article(client, HuduEndpoint.ARTICLES, {"id": 1})

    removed = HuduCollection([article]).strip_labels()

    client.labels.strip.assert_called_once_with(to_object=article, label_type=None)
    assert removed == ["a"]


def test_hudu_collection_strip_labels_batches_large_collections():
    from hudu_magic.models import AssetPassword

    client = MagicMock()
    client.labels = LabelsResource(client)
    client.labels.strip = MagicMock(return_value=[])
    passwords = HuduCollection([
        AssetPassword(client, HuduEndpoint.ASSET_PASSWORDS, {"id": i})
        for i in range(5)
    ])

    passwords.strip_labels()

    client.labels.strip.assert_called_once_with(passwords, label_type=None)


def test_hudu_collection_label_type_assign_to_and_strip_from():
    client = MagicMock()
    client.labels = LabelsResource(client)
    client.get = MagicMock(return_value=[])
    client.delete = MagicMock(return_value=None)
    article = Article(client, HuduEndpoint.ARTICLES, {"id": 2})
    priority = LabelType(client, HuduEndpoint.LABEL_TYPES, {"id": 3})
    status = LabelType(client, HuduEndpoint.LABEL_TYPES, {"id": 4})
    priority.assign_to = MagicMock(return_value=Label(client, HuduEndpoint.LABELS, {"id": 10}))
    status.assign_to = MagicMock(return_value=Label(client, HuduEndpoint.LABELS, {"id": 11}))

    types = HuduCollection([priority, status])
    applied = types.assign_to(article, user_id=7)
    stripped = types.strip_from(article)

    priority.assign_to.assert_called_once_with(article, user_id=7)
    status.assign_to.assert_called_once_with(article, user_id=7)
    assert isinstance(applied, HuduCollection)
    assert applied.ids() == [10, 11]
    client.get.assert_called_once()
    assert stripped == []


def test_hudu_collection_for_record_type_filters_label_types():
    client = MagicMock()
    article_type = LabelType(
        client,
        HuduEndpoint.LABEL_TYPES,
        {"id": 1, "applicable_record_types": ["Article"]},
    )
    asset_type = LabelType(
        client,
        HuduEndpoint.LABEL_TYPES,
        {"id": 2, "applicable_record_types": ["Article", "Asset"]},
    )

    filtered = HuduCollection([article_type, asset_type]).for_record_type("Article")

    assert filtered.ids() == [1, 2]
    assert HuduCollection([article_type, asset_type]).for_record_type("Asset").ids() == [2]


def test_hudu_collection_delete_all_removes_labels():
    client = MagicMock()
    label_a = Label(client, HuduEndpoint.LABELS, {"id": 10})
    label_b = Label(client, HuduEndpoint.LABELS, {"id": 11})
    label_a.delete = MagicMock(return_value=None)
    label_b.delete = MagicMock(return_value=None)

    HuduCollection([label_a, label_b]).delete_all()

    label_a.delete.assert_called_once()
    label_b.delete.assert_called_once()
