from lynara.interfaces.utils import get_server


def test_get_server():
    headers = {"host": "lynara:8080"}
    assert get_server(headers) == ("lynara", 8080)

    headers = {"host": "lynara"}
    assert get_server(headers) == ("lynara", 80)

    headers = {"x-forwarded-port": "8080"}
    assert get_server(headers) == ("lynara", 8080)

    headers = {}
    assert get_server(headers) == ("lynara", 80)

    headers = {"host": "lynara:8080", "x-forwarded-port": "9090"}
    assert get_server(headers) == ("lynara", 8080)

    headers = {"host": "lynara", "x-forwarded-port": "9090"}
    assert get_server(headers) == ("lynara", 9090)

    headers = {"host": "lynara:8080", "x-forwarded-port": "9090"}
    assert get_server(headers) == ("lynara", 8080)

    headers = {"host": "lynara", "x-forwarded-port": "9090"}
    assert get_server(headers) == ("lynara", 9090)

    headers = {"host": "lynara:8080", "x-forwarded-port": "9090"}
    assert get_server(headers) == ("lynara", 8080)

    headers = {"host": "lynara", "x-forwarded-port": "9090"}
    assert get_server(headers) == ("lynara", 9090)

    headers = {"host": "lynara:8080", "x-forwarded-port": "9090"}
    assert get_server(headers) == ("lynara", 8080)

    headers = {"host": "lynara", "x-forwarded-port": "9090"}
    assert get_server(headers) == ("lynara", 9090)
