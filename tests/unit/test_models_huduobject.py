from unittest.mock import MagicMock

import pytest

from hudu_magic.endpoints import HuduEndpoint
from hudu_magic.models import Article, HuduObject


def test_huduobject_getattr_and_dict_access():
    client = MagicMock()
    data = {"id": 5, "name": "Hello"}
    obj = Article(client, HuduEndpoint.ARTICLES, data)
    assert obj.id == 5
    assert obj.name == "Hello"
    assert obj.get("missing", "d") == "d"


def test_huduobject_repr_contains_class_and_id():
    client = MagicMock()
    obj = Article(client, HuduEndpoint.ARTICLES, {"id": 3, "name": "N"})
    assert "Article" in repr(obj)
    assert "3" in repr(obj)
    assert "N" in repr(obj)


def test_huduobject_unknown_attribute():
    client = MagicMock()
    obj = Article(client, HuduEndpoint.ARTICLES, {"id": 1})
    with pytest.raises(AttributeError):
        _ = obj.no_such_field


def test_huduobject_setattr_writes_through_to_data_for_save():
    client = MagicMock()
    client.update = MagicMock(
        return_value=Article(
            client, HuduEndpoint.ARTICLES_ID, {"id": 5, "name": "Updated"}
        )
    )
    obj = HuduObject(
        client, HuduEndpoint.ARTICLES, {"id": 5, "name": "Hello", "content": "x"}
    )

    obj.name = "Updated"
    assert obj.name == "Updated"
    assert obj._data["name"] == "Updated"
    assert "name" not in obj.__dict__

    obj.save()

    client.update.assert_called_once()
    _endpoint, item_id, payload = client.update.call_args[0]
    assert item_id == 5
    assert payload["name"] == "Updated"


def test_huduobject_setattr_rejects_readonly_id_property():
    client = MagicMock()
    obj = Article(client, HuduEndpoint.ARTICLES, {"id": 1, "name": "A"})
    with pytest.raises(AttributeError):
        obj.id = 99
    assert obj.id == 1
    assert obj._data["id"] == 1
