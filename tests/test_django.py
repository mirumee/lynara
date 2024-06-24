import pytest

from lynara import APIGatewayProxyEventV2Interface, Lynara


@pytest.mark.parametrize(
    "lifespan_mode",
    [
        "off",
        "auto",
    ],
)
async def test_django_app_lifespan_auto(lifespan_mode, lambda_events, django_app):
    lambda_event = lambda_events["api_gw_v2"]
    lambda_event["requestContext"]["http"]["method"] = "GET"
    lambda_event["requestContext"]["http"]["path"] = "/django/"
    lambda_event["path"] = "/django/"
    lynara = Lynara(django_app, lifespan_mode=lifespan_mode)
    response = await lynara.run(lambda_event, None, APIGatewayProxyEventV2Interface)
    assert response["statusCode"] == 200
    assert response["body"] == "Hello, world!"


async def test_django_app_lifespan_on(lambda_events, django_app):
    lambda_event = lambda_events["api_gw_v2"]
    lambda_event["requestContext"]["http"]["method"] = "GET"
    lambda_event["requestContext"]["http"]["path"] = "/django/"
    lambda_event["path"] = "/django/"
    lynara = Lynara(django_app, "on")
    with pytest.raises(ValueError) as cm:
        await lynara.run(lambda_event, None, APIGatewayProxyEventV2Interface)

    assert (
        str(cm.value) == "Django can only handle ASGI/HTTP connections, not lifespan."
    )
