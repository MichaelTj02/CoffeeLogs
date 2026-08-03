from datetime import datetime, timedelta


def test_list_methods_is_empty_for_a_new_bean(client, make_bean):
    bean = make_bean()

    response = client.get(f"/beans/{bean.id}/methods")

    assert response.status_code == 200
    assert response.json() == []


def test_list_methods_is_ordered_oldest_first(client, make_bean, make_method):
    bean = make_bean()
    second = make_method(bean, name="AeroPress", created_at=datetime(2026, 3, 2))
    first = make_method(bean, name="V60", created_at=datetime(2026, 3, 1))

    ids = [method["id"] for method in client.get(f"/beans/{bean.id}/methods").json()]

    assert ids == [first.id, second.id]


def test_list_methods_only_returns_that_beans_methods(client, make_bean, make_method):
    bean = make_bean(name="Mine")
    other = make_bean(name="Theirs")
    mine = make_method(bean, name="V60")
    make_method(other, name="V60")

    ids = [method["id"] for method in client.get(f"/beans/{bean.id}/methods").json()]

    assert ids == [mine.id]


def test_list_methods_unknown_bean_is_404(client):
    response = client.get("/beans/999/methods")

    assert response.status_code == 404
    assert response.json()["detail"] == "Bean 999 not found"


def test_create_method_returns_201(client, make_bean):
    bean = make_bean()

    response = client.post(f"/beans/{bean.id}/methods", json={"name": "V60"})

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "V60"
    assert body["bean_id"] == bean.id
    assert body["attempts"] == []


def test_create_method_serializes_created_at_as_utc(client, make_bean):
    bean = make_bean()

    created_at = client.post(f"/beans/{bean.id}/methods", json={"name": "V60"}).json()["created_at"]

    assert created_at.endswith("Z") or created_at.endswith("+00:00")
    assert datetime.fromisoformat(created_at).utcoffset() == timedelta(0)


def test_create_method_unknown_bean_is_404(client):
    response = client.post("/beans/999/methods", json={"name": "V60"})

    assert response.status_code == 404


def test_create_duplicate_method_name_is_409(client, make_bean, make_method):
    bean = make_bean()
    make_method(bean, name="V60")

    response = client.post(f"/beans/{bean.id}/methods", json={"name": "V60"})

    assert response.status_code == 409
    assert "already has" in response.json()["detail"]
    assert "V60" in response.json()["detail"]


def test_same_method_name_on_another_bean_is_allowed(client, make_bean, make_method):
    bean = make_bean(name="Mine")
    other = make_bean(name="Theirs")
    make_method(bean, name="V60")

    response = client.post(f"/beans/{other.id}/methods", json={"name": "V60"})

    assert response.status_code == 201
    assert response.json()["bean_id"] == other.id


def test_create_method_rejects_empty_name(client, make_bean):
    bean = make_bean()

    assert client.post(f"/beans/{bean.id}/methods", json={"name": ""}).status_code == 422


def test_create_method_rejects_overlong_name(client, make_bean):
    bean = make_bean()

    response = client.post(f"/beans/{bean.id}/methods", json={"name": "x" * 51})

    assert response.status_code == 422


def test_create_method_ignores_bean_id_in_body(client, make_bean):
    bean = make_bean(name="Mine")
    other = make_bean(name="Theirs")

    response = client.post(
        f"/beans/{bean.id}/methods", json={"name": "V60", "bean_id": other.id}
    )

    assert response.status_code == 201
    assert response.json()["bean_id"] == bean.id
    assert client.get(f"/beans/{other.id}/methods").json() == []


def test_delete_method_returns_204_with_no_body(client, make_bean, make_method):
    method = make_method(make_bean())

    response = client.delete(f"/methods/{method.id}")

    assert response.status_code == 204
    assert response.content == b""


def test_delete_method_removes_it_from_the_bean(client, make_bean, make_method):
    bean = make_bean()
    method = make_method(bean)

    client.delete(f"/methods/{method.id}")

    assert client.get(f"/beans/{bean.id}/methods").json() == []


def test_delete_method_twice_is_404(client, make_bean, make_method):
    method = make_method(make_bean())

    client.delete(f"/methods/{method.id}")
    response = client.delete(f"/methods/{method.id}")

    assert response.status_code == 404
    assert response.json()["detail"] == f"Brew method {method.id} not found"


def test_delete_unknown_method_is_404(client):
    assert client.delete("/methods/999").status_code == 404
