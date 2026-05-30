def test_admin_pages_redirect_to_login_when_logged_out(client):
    admin_response = client.get("/admin", follow_redirects=False)
    knowledge_response = client.get("/knowledge-admin", follow_redirects=False)

    assert admin_response.status_code == 303
    assert admin_response.headers["location"] == "/login"
    assert knowledge_response.status_code == 303
    assert knowledge_response.headers["location"] == "/login"


def test_default_admin_login_and_logout(client):
    response = client.get("/login")

    assert response.status_code == 200
    assert "后台登录" in response.text

    response = client.post(
        "/login",
        data={
            "username": "admin",
            "password": "admin123",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/admin"

    admin_response = client.get("/admin")
    knowledge_response = client.get("/knowledge-admin")

    assert admin_response.status_code == 200
    assert "退出登录" in admin_response.text
    assert knowledge_response.status_code == 200
    assert "退出登录" in knowledge_response.text

    response = client.get("/logout", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/login"
    assert client.get("/admin", follow_redirects=False).headers["location"] == "/login"


def test_invalid_admin_login_does_not_create_session(client):
    response = client.post(
        "/login",
        data={
            "username": "admin",
            "password": "incorrect",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/login?error=1"
    assert client.get("/admin", follow_redirects=False).headers["location"] == "/login"


def test_admin_credentials_can_be_configured_with_environment_variables(
    client,
    monkeypatch,
):
    monkeypatch.setenv("ADMIN_USERNAME", "operator")
    monkeypatch.setenv("ADMIN_PASSWORD", "secure-password")

    default_login = client.post(
        "/login",
        data={
            "username": "admin",
            "password": "admin123",
        },
        follow_redirects=False,
    )

    assert default_login.headers["location"] == "/login?error=1"

    configured_login = client.post(
        "/login",
        data={
            "username": "operator",
            "password": "secure-password",
        },
        follow_redirects=False,
    )

    assert configured_login.headers["location"] == "/admin"
    assert client.get("/admin").status_code == 200


def test_chat_page_and_docs_remain_public(client):
    assert client.get("/").status_code == 200
    assert client.get("/docs").status_code == 200
