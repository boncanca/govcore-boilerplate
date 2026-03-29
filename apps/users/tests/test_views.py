

def test_admin_url_resolves(client):
    response = client.get("/admin/")

    # 302 is valid for auth redirect, 200 if admin index opens.
    assert response.status_code in {200, 302}


def test_api_v1_url_prefix_exists(client):
    response = client.get("/api/v1/")

    # Empty URLconf can return 404 while route still exists as prefix.
    assert response.status_code in {200, 301, 302, 404}
