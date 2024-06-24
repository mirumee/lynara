from unittest.mock import call

import pytest

from lynara import APIGatewayProxyEventV2Interface, Lynara
from lynara.types import LifespanMode


@pytest.mark.parametrize(
    "lifespan_mode",
    [
        "on",
        "auto",
    ],
)
async def test_fastapi_app_lifespan(
    lifespan_mode, lambda_events, mock_lifespan, fastapi_app
):
    lambda_event = lambda_events["api_gw_v2"]
    lambda_event["requestContext"]["http"]["method"] = "GET"
    lambda_event["requestContext"]["http"]["path"] = "/fastapi/"
    lambda_event["path"] = "/fastapi/"
    lynara = Lynara(fastapi_app, LifespanMode(lifespan_mode))
    response = await lynara.run(lambda_event, None, APIGatewayProxyEventV2Interface)

    assert response["statusCode"] == 200
    assert response["body"] == '"Hello, world!"'
    mock_lifespan.assert_has_calls(
        [call(fastapi_app, "startup"), call(fastapi_app, "shutdown")]
    )
    assert response["cookies"] == ["cookie=test; Path=/; SameSite=lax"]
    assert response["headers"] == {
        "content-length": "15",
        "content-type": "application/json",
        "x-custom-header": "test",
    }


async def test_fastapi_app_lifespan_off(lambda_events, mock_lifespan, fastapi_app):
    lambda_event = lambda_events["api_gw_v2"]
    lambda_event["requestContext"]["http"]["method"] = "GET"
    lambda_event["requestContext"]["http"]["path"] = "/fastapi/"
    lambda_event["path"] = "/fastapi/"
    lynara = Lynara(fastapi_app, LifespanMode.OFF)
    response = await lynara.run(lambda_event, None, APIGatewayProxyEventV2Interface)

    assert response["statusCode"] == 200
    assert response["body"] == '"Hello, world!"'
    mock_lifespan.assert_not_called()
