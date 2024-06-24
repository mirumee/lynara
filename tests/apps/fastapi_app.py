from fastapi import FastAPI, Response


def get_fast_api_app(lifespan_func=None):
    fastapi_asgi_app = FastAPI(lifespan=lifespan_func)

    @fastapi_asgi_app.get("/fastapi/")
    @fastapi_asgi_app.get("/resource")
    async def read_root(response: Response):
        response.set_cookie(key="cookie", value="test")
        response.headers["X-Custom-Header"] = "test"
        return "Hello, world!"

    return fastapi_asgi_app


if __name__ == "__main__":
    import asyncio

    from lynara import APIGatewayProxyEventV1Interface, Lynara

    lynara = Lynara(app=get_fast_api_app())
    response = asyncio.run(
        lynara.run(
            event={
                "version": "1.0",
                "resource": "/dev/fastapi/",
                "path": "/dev/fastapi/",
                "httpMethod": "GET",
                "headers": {"header1": "value1", "header2": "value2"},
                "multiValueHeaders": {
                    "header3": ["value3"],
                    "header4": ["value4", "value5"],
                },
                "queryStringParameters": {
                    "parameter1": "value1",
                    "parameter2": "value",
                },
                "multiValueQueryStringParameters": {
                    "parameter1": ["value1", "value2"],
                    "parameter2": ["value"],
                },
                "requestContext": {
                    "accountId": "123456789012",
                    "apiId": "id",
                    "authorizer": {"claims": None, "scopes": None},
                    "domainName": "id.execute-api.us-east-1.amazonaws.com",
                    "domainPrefix": "id",
                    "extendedRequestId": "request-id",
                    "httpMethod": "GET",
                    "identity": {
                        "accessKey": None,
                        "accountId": None,
                        "caller": None,
                        "cognitoAuthenticationProvider": None,
                        "cognitoAuthenticationType": None,
                        "cognitoIdentityId": None,
                        "cognitoIdentityPoolId": None,
                        "principalOrgId": None,
                        "sourceIp": "192.0.2.1",
                        "user": None,
                        "userAgent": "user-agent",
                        "userArn": None,
                        "clientCert": {
                            "clientCertPem": "CERT_CONTENT",
                            "subjectDN": "www.example.com",
                            "issuerDN": "Example issuer",
                            "serialNumber": (
                                "a1:a1:a1:a1:a1:a1:a1:a1:a1:a1:a1:a1:a1:a1:a1:a1"
                            ),
                            "validity": {
                                "notBefore": "May 28 12:30:02 2019 GMT",
                                "notAfter": "Aug  5 09:36:04 2021 GMT",
                            },
                        },
                    },
                    "path": "/dev/fastapi/",
                    "protocol": "HTTP/1.1",
                    "requestId": "id=",
                    "requestTime": "04/Mar/2020:19:15:17 +0000",
                    "requestTimeEpoch": 1583349317135,
                    "resourceId": None,
                    "resourcePath": "/dev/fastapi/",
                    "stage": "dev",
                },
                "pathParameters": None,
                "stageVariables": None,
                "body": "Hello from Lambda!",
                "isBase64Encoded": False,
            },
            context=None,
            interface_class=APIGatewayProxyEventV1Interface,
            base_path="/dev",
        )
    )
    print(response)  # noqa: T201
