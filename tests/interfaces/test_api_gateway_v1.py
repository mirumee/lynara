from lynara import APIGatewayProxyEventV1Interface


async def test_init_no_body(fastapi_app, lambda_events):
    lambda_event = lambda_events["api_gw_v2"]
    lambda_event["body"] = None
    interface = APIGatewayProxyEventV1Interface(
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
    interface = APIGatewayProxyEventV1Interface(
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
    interface = APIGatewayProxyEventV1Interface(
        fastapi_app, lambda_event, context=None, base_path="/path/to"
    )

    assert await interface.app_queue.get() == {
        "type": "http.request",
        "body": b"Hello, world!",
        "more_body": False,
    }


async def test_scope(fastapi_app, lambda_events):
    lambda_event = lambda_events["api_gw_v1"]
    lambda_event["httpMethod"] = "GET"
    interface = APIGatewayProxyEventV1Interface(
        fastapi_app, lambda_event, None, base_path="/path/to"
    )
    scope = interface.scope

    assert scope["type"] == "http"
    assert scope["method"] == "GET"
    assert scope["path"] == "/resource"
    assert scope["query_string"] == b"foo=bar"
    assert scope["headers"] == [
        [
            b"accept",
            b"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*"
            b";q=0.8",
        ],
        [
            b"accept-encoding",
            b"gzip, deflate, sdch",
        ],
        [
            b"accept-language",
            b"en-US,en;q=0.8",
        ],
        [
            b"cache-control",
            b"max-age=0",
        ],
        [
            b"cloudfront-forwarded-proto",
            b"https",
        ],
        [
            b"cloudfront-is-desktop-viewer",
            b"true",
        ],
        [
            b"cloudfront-is-mobile-viewer",
            b"false",
        ],
        [
            b"cloudfront-is-smarttv-viewer",
            b"false",
        ],
        [
            b"cloudfront-is-tablet-viewer",
            b"false",
        ],
        [
            b"cloudfront-viewer-country",
            b"US",
        ],
        [
            b"host",
            b"0123456789.execute-api.us-east-1.amazonaws.com",
        ],
        [
            b"upgrade-insecure-requests",
            b"1",
        ],
        [
            b"user-agent",
            b"Custom User Agent String",
        ],
        [
            b"via",
            b"1.1 08f323deadbeefa7af34d5feb414ce27.cloudfront.net (CloudFront)",
        ],
        [
            b"x-amz-cf-id",
            b"cDehVQoZnx43VYQb9j2-nvCh-9z396Uhbp027Y2JvkCPNLmGJHqlaA==",
        ],
        [
            b"x-forwarded-for",
            b"127.0.0.1, 127.0.0.2",
        ],
        [
            b"x-forwarded-port",
            b"443",
        ],
        [
            b"x-forwarded-proto",
            b"https",
        ],
    ]


async def test_match(lambda_events):
    lambda_event = lambda_events["api_gw_v1"]
    assert APIGatewayProxyEventV1Interface.match(lambda_event) is True
    lambda_event = lambda_events["api_gw_v2"]
    assert APIGatewayProxyEventV1Interface.match(lambda_event) is False


async def test_receive(fastapi_app, lambda_events):
    lambda_event = lambda_events["api_gw_v1"]
    interface = APIGatewayProxyEventV1Interface(
        fastapi_app, lambda_event, None, base_path="/path/to"
    )
    message = await interface.receive()
    assert message["type"] == "http.request"
    assert message["body"] == b'{"test":"body"}'
    assert not message["more_body"]


async def test_send_response_headers(fastapi_app, lambda_events):
    lambda_event = lambda_events["api_gw_v1"]
    interface = APIGatewayProxyEventV1Interface(
        fastapi_app, lambda_event, None, base_path="/path/to"
    )

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

    assert interface.lambda_response["statusCode"] == 200
    assert interface.lambda_response["headers"]["content-type"] == "application/json"
    assert "set-cookie" in interface.lambda_response["multiValueHeaders"]
    assert interface.lambda_response["multiValueHeaders"]["set-cookie"] == [
        "cookie1=value1",
        "cookie2=value2",
    ]


async def test_send_response_body(fastapi_app, lambda_events):
    lambda_event = lambda_events["api_gw_v1"]
    interface = APIGatewayProxyEventV1Interface(
        fastapi_app, lambda_event, None, base_path="/path/to"
    )

    await interface.send(
        {
            "type": "http.response.body",
            "body": b'{"Hello": "World"}',
            "more_body": False,
        }
    )

    assert interface.lambda_response["body"] == '{"Hello": "World"}'


async def test_full_response(fastapi_app, lambda_events):
    lambda_event = lambda_events["api_gw_v1"]
    lambda_event["httpMethod"] = "GET"
    interface = APIGatewayProxyEventV1Interface(
        fastapi_app, lambda_event, None, base_path="/path/to"
    )

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
    assert response["multiValueHeaders"]["set-cookie"] == [
        "cookie1=value1",
        "cookie2=value2",
    ]
    assert response["body"] == '{"Hello":"World"}'
