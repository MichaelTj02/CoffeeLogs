from datetime import UTC, datetime, timedelta


def test_create_attempt_returns_201(client, make_bean, make_method):
    method = make_method(make_bean())

    response = client.post(
        f"/methods/{method.id}/attempts",
        json={
            "brewed_at": "2026-04-01T07:30:00Z",
            "dose_grams": 18,
            "yield_grams": 300,
            "rating": 4,
            "notes": "even extraction",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["brew_method_id"] == method.id
    assert body["dose_grams"] == 18
    assert body["yield_grams"] == 300
    assert body["rating"] == 4
    assert body["notes"] == "even extraction"


def test_create_attempt_unknown_method_is_404(client):
    response = client.post("/methods/999/attempts", json={"dose_grams": 18, "yield_grams": 300})

    assert response.status_code == 404
    assert response.json()["detail"] == "Brew method 999 not found"


def test_omitted_brewed_at_defaults_to_now(client, make_bean, make_method):
    method = make_method(make_bean())

    brewed_at = client.post(
        f"/methods/{method.id}/attempts", json={"dose_grams": 18, "yield_grams": 300}
    ).json()["brewed_at"]

    assert abs(datetime.fromisoformat(brewed_at) - datetime.now(UTC)) < timedelta(minutes=5)


def test_null_brewed_at_defaults_to_now(client, make_bean, make_method):
    method = make_method(make_bean())

    brewed_at = client.post(
        f"/methods/{method.id}/attempts",
        json={"brewed_at": None, "dose_grams": 18, "yield_grams": 300},
    ).json()["brewed_at"]

    assert abs(datetime.fromisoformat(brewed_at) - datetime.now(UTC)) < timedelta(minutes=5)


def test_offset_brewed_at_is_normalized_to_the_same_instant(client, make_bean, make_method):
    method = make_method(make_bean())

    brewed_at = client.post(
        f"/methods/{method.id}/attempts",
        json={"brewed_at": "2026-04-01T12:00:00+02:00", "dose_grams": 18, "yield_grams": 300},
    ).json()["brewed_at"]

    assert datetime.fromisoformat(brewed_at) == datetime(2026, 4, 1, 10, 0, tzinfo=UTC)


def test_naive_brewed_at_is_treated_as_utc(client, make_bean, make_method):
    method = make_method(make_bean())

    brewed_at = client.post(
        f"/methods/{method.id}/attempts",
        json={"brewed_at": "2026-04-01T12:00:00", "dose_grams": 18, "yield_grams": 300},
    ).json()["brewed_at"]

    assert datetime.fromisoformat(brewed_at) == datetime(2026, 4, 1, 12, 0, tzinfo=UTC)
    assert brewed_at.endswith("Z") or brewed_at.endswith("+00:00")


def test_empty_string_brewed_at_is_422(client, make_bean, make_method):
    method = make_method(make_bean())

    response = client.post(
        f"/methods/{method.id}/attempts",
        json={"brewed_at": "", "dose_grams": 18, "yield_grams": 300},
    )

    assert response.status_code == 422


def test_dose_of_zero_is_422(client, make_bean, make_method):
    method = make_method(make_bean())

    response = client.post(
        f"/methods/{method.id}/attempts", json={"dose_grams": 0, "yield_grams": 300}
    )

    assert response.status_code == 422


def test_dose_above_one_thousand_is_422(client, make_bean, make_method):
    method = make_method(make_bean())

    response = client.post(
        f"/methods/{method.id}/attempts", json={"dose_grams": 1001, "yield_grams": 300}
    )

    assert response.status_code == 422


def test_yield_of_zero_is_422(client, make_bean, make_method):
    method = make_method(make_bean())

    response = client.post(
        f"/methods/{method.id}/attempts", json={"dose_grams": 18, "yield_grams": 0}
    )

    assert response.status_code == 422


def test_yield_above_five_thousand_is_422(client, make_bean, make_method):
    method = make_method(make_bean())

    response = client.post(
        f"/methods/{method.id}/attempts", json={"dose_grams": 18, "yield_grams": 5001}
    )

    assert response.status_code == 422


def test_rating_of_zero_is_422(client, make_bean, make_method):
    method = make_method(make_bean())

    response = client.post(
        f"/methods/{method.id}/attempts",
        json={"dose_grams": 18, "yield_grams": 300, "rating": 0},
    )

    assert response.status_code == 422


def test_rating_above_five_is_422(client, make_bean, make_method):
    method = make_method(make_bean())

    response = client.post(
        f"/methods/{method.id}/attempts",
        json={"dose_grams": 18, "yield_grams": 300, "rating": 6},
    )

    assert response.status_code == 422


def test_missing_dose_is_422(client, make_bean, make_method):
    method = make_method(make_bean())

    response = client.post(f"/methods/{method.id}/attempts", json={"yield_grams": 300})

    assert response.status_code == 422


def test_omitted_rating_is_null(client, make_bean, make_method):
    method = make_method(make_bean())

    body = client.post(
        f"/methods/{method.id}/attempts", json={"dose_grams": 18, "yield_grams": 300}
    ).json()

    assert body["rating"] is None
    assert body["notes"] is None


def test_create_attempt_ignores_brew_method_id_in_body(client, make_bean, make_method):
    bean = make_bean()
    method = make_method(bean, name="V60")
    other = make_method(bean, name="AeroPress")

    response = client.post(
        f"/methods/{method.id}/attempts",
        json={"brew_method_id": other.id, "dose_grams": 18, "yield_grams": 300},
    )

    assert response.status_code == 201
    assert response.json()["brew_method_id"] == method.id
    assert client.get(f"/methods/{other.id}/attempts").json() == []


def test_list_attempts_is_ordered_newest_first(client, make_bean, make_method, make_attempt):
    method = make_method(make_bean())
    older = make_attempt(method, brewed_at=datetime(2026, 4, 1, 7, 0))
    newer = make_attempt(method, brewed_at=datetime(2026, 4, 2, 7, 0))

    ids = [attempt["id"] for attempt in client.get(f"/methods/{method.id}/attempts").json()]

    assert ids == [newer.id, older.id]


def test_list_attempts_breaks_timestamp_ties_by_id_desc(
    client, make_bean, make_method, make_attempt
):
    method = make_method(make_bean())
    same_moment = datetime(2026, 4, 1, 7, 0)
    first = make_attempt(method, brewed_at=same_moment)
    second = make_attempt(method, brewed_at=same_moment)

    ids = [attempt["id"] for attempt in client.get(f"/methods/{method.id}/attempts").json()]

    assert ids == [second.id, first.id]


def test_list_attempts_only_returns_that_methods_attempts(
    client, make_bean, make_method, make_attempt
):
    bean = make_bean()
    method = make_method(bean, name="V60")
    other = make_method(bean, name="AeroPress")
    mine = make_attempt(method)
    make_attempt(other)

    ids = [attempt["id"] for attempt in client.get(f"/methods/{method.id}/attempts").json()]

    assert ids == [mine.id]


def test_list_attempts_unknown_method_is_404(client):
    assert client.get("/methods/999/attempts").status_code == 404


def test_delete_attempt_returns_204_with_no_body(client, make_bean, make_method, make_attempt):
    attempt = make_attempt(make_method(make_bean()))

    response = client.delete(f"/attempts/{attempt.id}")

    assert response.status_code == 204
    assert response.content == b""


def test_delete_attempt_twice_is_404(client, make_bean, make_method, make_attempt):
    attempt = make_attempt(make_method(make_bean()))

    client.delete(f"/attempts/{attempt.id}")
    response = client.delete(f"/attempts/{attempt.id}")

    assert response.status_code == 404
    assert response.json()["detail"] == f"Brew attempt {attempt.id} not found"


def test_delete_unknown_attempt_is_404(client):
    assert client.delete("/attempts/999").status_code == 404
