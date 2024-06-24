from base64 import b64decode

import pytest

from lynara import APIGatewayProxyEventV2Interface
from tests.apps.fastapi_app import get_fast_api_app


async def test_init_no_body(fastapi_app, lambda_events):
    lambda_event = lambda_events["api_gw_v2"]
    lambda_event["body"] = None
    interface = APIGatewayProxyEventV2Interface(
        fastapi_app, lambda_event, context=None, base_path="/path/to"
    )

    assert await interface.app_queue.get() == {
        "type": "http.request",
        "body": b"",
        "more_body": False,
    }


async def test_init_non_base64_body(fastapi_app, lambda_events):
    lambda_event = lambda_events["api_gw_v2"]
    lambda_event["isBase64Encoded"] = False
    lambda_event["body"] = "Hello, world!"
    interface = APIGatewayProxyEventV2Interface(
        fastapi_app, lambda_event, context=None, base_path="/path/to"
    )

    assert await interface.app_queue.get() == {
        "type": "http.request",
        "body": b"Hello, world!",
        "more_body": False,
    }


async def test_init_bytes_body(fastapi_app, lambda_events):
    lambda_event = lambda_events["api_gw_v2"]
    lambda_event["isBase64Encoded"] = False
    lambda_event["body"] = b"Hello, world!"
    interface = APIGatewayProxyEventV2Interface(
        fastapi_app, lambda_event, context=None, base_path="/path/to"
    )

    assert await interface.app_queue.get() == {
        "type": "http.request",
        "body": b"Hello, world!",
        "more_body": False,
    }


async def test_scope(fastapi_app, lambda_events):
    lambda_event = lambda_events["api_gw_v2"]
    interface = APIGatewayProxyEventV2Interface(
        fastapi_app, lambda_event, context=None, base_path="/path/to"
    )

    scope = interface.scope

    assert scope["type"] == "http"
    assert scope["method"] == "POST"
    assert scope["path"] == "/resource"
    assert scope["query_string"] == (
        b"parameter1=value1&parameter1=value2&parameter2=value"
    )
    assert scope["headers"] == [
        (b"header1", b"value1"),
        (b"header2", b"value1,value2"),
    ]
    assert scope["client"] == ("192.168.0.1/32", 0)
    assert scope["server"] == ("lynara", 80)


async def test_match(lambda_events):
    lambda_event = lambda_events["api_gw_v2"]
    assert APIGatewayProxyEventV2Interface.match(lambda_event) is True
    lambda_event = lambda_events["api_gw_v1"]
    assert APIGatewayProxyEventV2Interface.match(lambda_event) is False


async def test_receive(lambda_events):
    lambda_event = lambda_events["api_gw_v2"]
    app = get_fast_api_app()
    interface = APIGatewayProxyEventV2Interface(app, lambda_event, context=None)

    message = await interface.receive()
    assert message["type"] == "http.request"
    assert message["body"] == b64decode(lambda_event["body"])
    assert not message["more_body"]


async def test_send_response_headers(fastapi_app, lambda_events):
    lambda_event = lambda_events["api_gw_v2"]
    interface = APIGatewayProxyEventV2Interface(fastapi_app, lambda_event, context=None)

    await interface.send(
        {
            "type": "http.response.start",
            "status": 200,
            "headers": [
                (b"content-type", b"application/json"),
            ],
        }
    )

    assert interface.lambda_response["statusCode"] == 200
    assert interface.lambda_response["headers"]["content-type"] == "application/json"


async def test_send_response_body(fastapi_app, lambda_events):
    lambda_event = lambda_events["api_gw_v2"]
    interface = APIGatewayProxyEventV2Interface(fastapi_app, lambda_event, context=None)

    await interface.send(
        {
            "type": "http.response.body",
            "body": b'{"message":"Hello, world!"}',
            "more_body": False,
        }
    )
    assert interface.lambda_response["body"] == '{"message":"Hello, world!"}'


async def test_send_response_body_more_body(fastapi_app, lambda_events):
    lambda_event = lambda_events["api_gw_v2"]
    interface = APIGatewayProxyEventV2Interface(fastapi_app, lambda_event, context=None)
    await interface.app_queue.get()

    await interface.send(
        {
            "type": "http.response.body",
            "body": b'{"message":"Hello, world!"}',
            "more_body": True,
        }
    )
    assert interface.lambda_response["body"] == '{"message":"Hello, world!"}'
    assert interface.app_queue.qsize() == 0


async def test_full_response(fastapi_app, lambda_events):
    lambda_event = lambda_events["api_gw_v2"]
    lambda_event["requestContext"]["http"]["method"] = "GET"
    interface = APIGatewayProxyEventV2Interface(
        fastapi_app, lambda_event, context=None, base_path="/path/to"
    )
    await interface.app_queue.get()

    await interface.send(
        {
            "type": "http.response.start",
            "status": 200,
            "headers": [
                (b"content-type", b"application/json"),
                (b"set-cookie", b"cookie1=value1"),
                (b"set-cookie", b"cookie2=value2"),
            ],
        }
    )
    await interface.send(
        {
            "type": "http.response.body",
            "body": b'{"Hello":"World"}',
            "more_body": False,
        }
    )

    response = interface.lambda_response

    assert response["statusCode"] == 200
    assert response["headers"]["content-type"] == "application/json"
    assert response["body"] == '{"Hello":"World"}'
    assert response["cookies"] == ["cookie1=value1", "cookie2=value2"]
    assert await interface.app_queue.get() == {
        "type": "http.disconnect",
    }


async def test_send_unknown_type(fastapi_app, lambda_events):
    lambda_event = lambda_events["api_gw_v2"]
    interface = APIGatewayProxyEventV2Interface(fastapi_app, lambda_event, context=None)

    with pytest.raises(ValueError):
        await interface.send(
            {
                "type": "unknown.type",
            }
        )
