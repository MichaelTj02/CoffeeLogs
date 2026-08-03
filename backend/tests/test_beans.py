from datetime import UTC, datetime, timedelta


def test_create_bean_full_payload(client):
    response = client.post(
        "/beans",
        json={
            "name": "Kenya Kirinyaga",
            "roaster": "Origin",
            "origin": "Kenya",
            "roast_date": "2026-07-20",
            "price": 14.5,
            "notes": "blackcurrant",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["id"] > 0
    assert body["name"] == "Kenya Kirinyaga"
    assert body["origin"] == "Kenya"
    assert body["roast_date"] == "2026-07-20"
    assert body["price"] == 14.5
    assert body["notes"] == "blackcurrant"
    assert body["is_favourite"] is False
    assert body["method_count"] == 0


def test_create_bean_minimal_payload(client):
    response = client.post("/beans", json={"name": "House Blend", "roaster": "Local"})

    assert response.status_code == 201
    body = response.json()
    assert body["origin"] is None
    assert body["roast_date"] is None
    assert body["price"] is None
    assert body["notes"] is None


def test_create_bean_without_name_is_422(client):
    response = client.post("/beans", json={"roaster": "Local"})

    assert response.status_code == 422


def test_create_bean_with_empty_roast_date_is_422(client):
    response = client.post(
        "/beans", json={"name": "House Blend", "roaster": "Local", "roast_date": ""}
    )

    assert response.status_code == 422


def test_create_bean_with_price_above_range_is_422(client):
    response = client.post(
        "/beans", json={"name": "House Blend", "roaster": "Local", "price": 10000}
    )

    assert response.status_code == 422


def test_create_bean_with_negative_price_is_422(client):
    response = client.post("/beans", json={"name": "House Blend", "roaster": "Local", "price": -1})

    assert response.status_code == 422


def test_created_at_is_serialized_as_utc(client):
    created_at = client.post("/beans", json={"name": "House Blend", "roaster": "Local"}).json()[
        "created_at"
    ]

    assert created_at.endswith("Z") or created_at.endswith("+00:00")
    assert datetime.fromisoformat(created_at).utcoffset() == timedelta(0)


def test_list_beans_is_empty_initially(client):
    response = client.get("/beans")

    assert response.status_code == 200
    assert response.json() == []


def test_list_beans_sorts_favourites_first_then_newest(client, make_bean):
    old_favourite = make_bean(
        name="Old favourite", is_favourite=True, created_at=datetime(2026, 1, 1)
    )
    new_plain = make_bean(name="New plain", created_at=datetime(2026, 6, 1))
    new_favourite = make_bean(
        name="New favourite", is_favourite=True, created_at=datetime(2026, 7, 1)
    )

    ids = [bean["id"] for bean in client.get("/beans").json()]

    assert ids == [new_favourite.id, old_favourite.id, new_plain.id]


def test_list_beans_sort_recent_ignores_favourites(client, make_bean):
    old_favourite = make_bean(
        name="Old favourite", is_favourite=True, created_at=datetime(2026, 1, 1)
    )
    new_plain = make_bean(name="New plain", created_at=datetime(2026, 6, 1))

    ids = [bean["id"] for bean in client.get("/beans", params={"sort": "recent"}).json()]

    assert ids == [new_plain.id, old_favourite.id]


def test_list_beans_breaks_timestamp_ties_by_id_desc(client, make_bean):
    same_moment = datetime(2026, 5, 5, 9, 30)
    first = make_bean(name="First", created_at=same_moment)
    second = make_bean(name="Second", created_at=same_moment)

    ids = [bean["id"] for bean in client.get("/beans", params={"sort": "recent"}).json()]

    assert ids == [second.id, first.id]


def test_list_beans_respects_limit(client, make_bean):
    make_bean(name="One", created_at=datetime(2026, 1, 1))
    newest = make_bean(name="Two", created_at=datetime(2026, 2, 1))

    body = client.get("/beans", params={"limit": 1}).json()

    assert [bean["id"] for bean in body] == [newest.id]


def test_list_beans_rejects_limit_below_one(client):
    assert client.get("/beans", params={"limit": 0}).status_code == 422


def test_list_beans_rejects_limit_above_two_hundred(client):
    assert client.get("/beans", params={"limit": 201}).status_code == 422


def test_list_beans_rejects_unknown_sort(client):
    assert client.get("/beans", params={"sort": "oldest"}).status_code == 422


def test_bean_detail_nests_methods_and_attempts(client, make_bean, make_method, make_attempt):
    bean = make_bean()
    method = make_method(bean, name="AeroPress")
    attempt = make_attempt(method, rating=4)

    response = client.get(f"/beans/{bean.id}")

    assert response.status_code == 200
    body = response.json()
    assert body["method_count"] == 1
    assert [method_body["name"] for method_body in body["brew_methods"]] == ["AeroPress"]
    assert [attempt_body["id"] for attempt_body in body["brew_methods"][0]["attempts"]] == [
        attempt.id
    ]


def test_bean_detail_counts_every_method(client, make_bean, make_method):
    bean = make_bean()
    make_method(bean, name="V60")
    make_method(bean, name="AeroPress")

    assert client.get(f"/beans/{bean.id}").json()["method_count"] == 2


def test_bean_detail_unknown_id_is_404(client):
    response = client.get("/beans/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Bean 999 not found"


def test_patch_favourite_toggles_on_and_off(client, make_bean):
    bean = make_bean()

    turned_on = client.patch(f"/beans/{bean.id}/favourite", json={"is_favourite": True})
    assert turned_on.status_code == 200
    assert turned_on.json()["is_favourite"] is True

    turned_off = client.patch(f"/beans/{bean.id}/favourite", json={"is_favourite": False})
    assert turned_off.json()["is_favourite"] is False


def test_patch_favourite_unknown_id_is_404(client):
    response = client.patch("/beans/999/favourite", json={"is_favourite": True})

    assert response.status_code == 404


def test_patch_favourite_rejects_non_boolean(client, make_bean):
    bean = make_bean()

    response = client.patch(f"/beans/{bean.id}/favourite", json={"is_favourite": "maybe"})

    assert response.status_code == 422


def test_patch_favourite_requires_the_field(client, make_bean):
    bean = make_bean()

    assert client.patch(f"/beans/{bean.id}/favourite", json={}).status_code == 422


def test_delete_bean_returns_204_with_no_body(client, make_bean):
    bean = make_bean()

    response = client.delete(f"/beans/{bean.id}")

    assert response.status_code == 204
    assert response.content == b""


def test_delete_bean_then_fetch_is_404(client, make_bean):
    bean = make_bean()

    client.delete(f"/beans/{bean.id}")

    assert client.get(f"/beans/{bean.id}").status_code == 404


def test_delete_unknown_bean_is_404(client):
    assert client.delete("/beans/999").status_code == 404


def test_created_at_defaults_to_now(client):
    created_at = client.post("/beans", json={"name": "House Blend", "roaster": "Local"}).json()[
        "created_at"
    ]

    assert abs(datetime.fromisoformat(created_at) - datetime.now(UTC)) < timedelta(minutes=5)
