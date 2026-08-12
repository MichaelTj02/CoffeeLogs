import pytest


@pytest.fixture
def other_user(make_user):
    return make_user(email="rival@example.com")


@pytest.fixture
def other_client(make_client, other_user):
    return make_client(other_user)


def test_listing_beans_excludes_other_users_beans(client, other_client, make_bean):
    make_bean(name="Mine")

    assert other_client.get("/beans").json() == []
    assert [bean["name"] for bean in client.get("/beans").json()] == ["Mine"]


def test_reading_another_users_bean_is_404(other_client, make_bean):
    bean = make_bean()

    response = other_client.get(f"/beans/{bean.id}")

    # The same detail as a bean that never existed: anything else is an existence oracle.
    assert response.status_code == 404
    assert response.json()["detail"] == f"Bean {bean.id} not found"


def test_favouriting_another_users_bean_is_404_and_changes_nothing(
    client, other_client, make_bean
):
    bean = make_bean()

    response = other_client.patch(f"/beans/{bean.id}/favourite", json={"is_favourite": True})

    assert response.status_code == 404
    assert response.json()["detail"] == f"Bean {bean.id} not found"
    assert client.get(f"/beans/{bean.id}").json()["is_favourite"] is False


def test_creating_a_method_under_another_users_bean_is_404(client, other_client, make_bean):
    bean = make_bean()

    response = other_client.post(f"/beans/{bean.id}/methods", json={"name": "V60"})

    assert response.status_code == 404
    assert response.json()["detail"] == f"Bean {bean.id} not found"
    assert client.get(f"/beans/{bean.id}/methods").json() == []


def test_creating_an_attempt_under_another_users_method_is_404(
    client, other_client, make_bean, make_method
):
    method = make_method(make_bean())

    response = other_client.post(
        f"/methods/{method.id}/attempts", json={"dose_grams": 18, "yield_grams": 300}
    )

    assert response.status_code == 404
    assert response.json()["detail"] == f"Brew method {method.id} not found"
    assert client.get(f"/methods/{method.id}/attempts").json() == []


def test_listing_another_users_methods_and_attempts_is_404(
    other_client, make_bean, make_method
):
    bean = make_bean()
    method = make_method(bean)

    assert other_client.get(f"/beans/{bean.id}/methods").status_code == 404
    assert other_client.get(f"/methods/{method.id}/attempts").status_code == 404


def test_deleting_another_users_bean_is_404_and_keeps_it(client, other_client, make_bean):
    bean = make_bean()

    response = other_client.delete(f"/beans/{bean.id}")

    assert response.status_code == 404
    assert response.json()["detail"] == f"Bean {bean.id} not found"
    assert client.get(f"/beans/{bean.id}").status_code == 200


def test_deleting_another_users_method_is_404_and_keeps_it(
    client, other_client, make_bean, make_method
):
    bean = make_bean()
    method = make_method(bean)

    response = other_client.delete(f"/methods/{method.id}")

    assert response.status_code == 404
    assert response.json()["detail"] == f"Brew method {method.id} not found"
    assert [body["id"] for body in client.get(f"/beans/{bean.id}/methods").json()] == [method.id]


def test_deleting_another_users_attempt_is_404_and_keeps_it(
    client, other_client, make_bean, make_method, make_attempt
):
    method = make_method(make_bean())
    attempt = make_attempt(method)

    response = other_client.delete(f"/attempts/{attempt.id}")

    assert response.status_code == 404
    assert response.json()["detail"] == f"Brew attempt {attempt.id} not found"
    assert [body["id"] for body in client.get(f"/methods/{method.id}/attempts").json()] == [
        attempt.id
    ]


def test_creating_a_bean_ignores_a_user_id_in_the_body(client, other_client, other_user):
    response = client.post(
        "/beans", json={"name": "Mine", "roaster": "Local", "user_id": other_user.id}
    )

    assert response.status_code == 201
    assert "user_id" not in response.json()
    assert other_client.get("/beans").json() == []
    assert [bean["id"] for bean in client.get("/beans").json()] == [response.json()["id"]]


def test_each_user_may_name_a_method_the_same(client, other_client, other_user, make_bean):
    mine = make_bean(name="Mine")
    theirs = make_bean(name="Theirs", user_id=other_user.id)

    assert client.post(f"/beans/{mine.id}/methods", json={"name": "V60"}).status_code == 201
    assert other_client.post(f"/beans/{theirs.id}/methods", json={"name": "V60"}).status_code == 201
