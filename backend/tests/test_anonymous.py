import pytest

# Authenticating the shared `client` fixture removed every anonymous request from the other
# test files, so the 401 contract is asserted here over the whole data surface.
DATA_ENDPOINTS = [
    ("GET", "/beans"),
    ("POST", "/beans"),
    ("GET", "/beans/{bean_id}"),
    ("PATCH", "/beans/{bean_id}/favourite"),
    ("DELETE", "/beans/{bean_id}"),
    ("GET", "/beans/{bean_id}/methods"),
    ("POST", "/beans/{bean_id}/methods"),
    ("DELETE", "/methods/{method_id}"),
    ("GET", "/methods/{method_id}/attempts"),
    ("POST", "/methods/{method_id}/attempts"),
    ("DELETE", "/attempts/{attempt_id}"),
]

ADDRESSED_ENDPOINTS = [(verb, path) for verb, path in DATA_ENDPOINTS if "{" in path]


@pytest.mark.parametrize(("verb", "path"), DATA_ENDPOINTS)
def test_data_endpoints_reject_anonymous_requests(
    anon_client, make_bean, make_method, make_attempt, verb, path
):
    bean = make_bean()
    method = make_method(bean)
    attempt = make_attempt(method)
    url = path.format(bean_id=bean.id, method_id=method.id, attempt_id=attempt.id)

    response = anon_client.request(verb, url, json={})

    assert response.status_code == 401


@pytest.mark.parametrize(("verb", "path"), ADDRESSED_ENDPOINTS)
def test_anonymous_requests_are_401_before_404(anon_client, verb, path):
    url = path.format(bean_id=999, method_id=999, attempt_id=999)

    response = anon_client.request(verb, url, json={})

    assert response.status_code == 401


def test_health_stays_public(anon_client):
    response = anon_client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
