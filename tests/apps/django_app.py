from django.conf import settings
from django.core.asgi import get_asgi_application
from django.http import HttpResponse
from django.urls import path

settings.configure(
    DEBUG=True,
    SECRET_KEY="thisisthesecretkey",
    ALLOWED_HOSTS=["*"],
    ROOT_URLCONF=__name__,
)


def index(request):
    return HttpResponse("Hello, world!")


urlpatterns = [
    path("django/", index),
]

django_asgi_app = get_asgi_application()


if __name__ == "__main__":
    import asyncio

    from lynara import APIGatewayProxyEventV2Interface, Lynara

    lynara = Lynara(app=django_asgi_app)
    response = asyncio.run(
        lynara.run(
            event={
                "version": "2.0",
                "routeKey": "$default",
                "rawPath": "/django/",
                "rawQueryString": (
                    "parameter1=value1&" "parameter1=value2&" "parameter2=value"
                ),
                "cookies": ["cookie1", "cookie2"],
                "headers": {"Header1": "value1", "Header2": "value1,value2"},
                "queryStringParameters": {
                    "parameter1": "value1,value2",
                    "parameter2": "value",
                },
                "requestContext": {
                    "domainName": "id.execute-api.us-east-1.amazonaws.com",
                    "domainPrefix": "id",
                    "http": {
                        "method": "GET",
                        "path": "/django/",
                        "protocol": "HTTP/1.1",
                        "sourceIp": "192.168.0.1/32",
                        "userAgent": "agent",
                    },
                    "requestId": "id",
                    "routeKey": "$default",
                    "stage": "$default",
                    "time": "12/Mar/2020:19:03:58 +0000",
                    "timeEpoch": 1583348638390,
                },
                "body": "eyJ0ZXN0IjoiYm9keSJ9",
                "pathParameters": {"parameter1": "value1"},
                "isBase64Encoded": True,
                "stageVariables": {
                    "stageVariable1": "value1",
                    "stageVariable2": "value2",
                },
            },
            context=None,
            interface_class=APIGatewayProxyEventV2Interface,
        )
    )
