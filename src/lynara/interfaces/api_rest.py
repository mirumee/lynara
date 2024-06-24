from base64 import b64decode
from urllib.parse import urlencode

from lynara.interfaces.base import HTTPInterface
from lynara.interfaces.utils import get_server, strip_api_gateway_path
from lynara.types import ASGIApp, LambdaEvent, Message, Scope


class APIGatewayProxyEventV1Interface(HTTPInterface):
    """
    `sam local generate-event apigateway aws-proxy`
    """

    def __init__(
        self, app: ASGIApp, event: LambdaEvent, context, base_path: str | None = None
    ) -> None:
        super().__init__(app=app, event=event, context=context, base_path=base_path)
        self.lambda_response = {
            "isBase64Encoded": False,
            "statusCode": 200,
            "headers": {},
            "multiValueHeaders": {},
            "body": "",
        }
        body = self.event.get("body", b"")
        if not body:
            body = b""
        if self.event.get("isBase64Encoded"):
            body = b64decode(body)
        elif not isinstance(body, bytes):
            body = body.encode()
        self.app_queue.put_nowait(
            {
                "type": "http.request",
                "body": body,
                "more_body": False,
            }
        )

    @classmethod
    def match(cls, event: LambdaEvent) -> bool:
        return "resource" in event and "requestContext" in event

    def _handle_multi_value_headers_in_scope(self) -> dict[str, str]:
        headers = self.event.get("headers", {}) or {}
        headers = {k.lower(): v for k, v in headers.items()}
        if self.event.get("multiValueHeaders"):
            headers.update(
                {
                    k.lower(): ", ".join(v) if isinstance(v, list) else ""
                    for k, v in self.event.get("multiValueHeaders", {}).items()
                }
            )

        return headers

    def _encode_query_string(self) -> bytes:
        params = self.event.get("multiValueQueryStringParameters", {})
        if not params:
            params = self.event.get("queryStringParameters", {})
        if not params:
            return b""

        return urlencode(params, doseq=True).encode()

    @property
    def scope(self) -> Scope:
        headers = self._handle_multi_value_headers_in_scope()
        request_context = self.event["requestContext"]
        self._method = self.event["httpMethod"]
        return {
            "type": "http",
            "method": self._method,
            "http_version": "1.1",
            "headers": [[k.encode(), v.encode()] for k, v in headers.items()],
            "path": strip_api_gateway_path(
                self.event["path"],
                base_path=self.base_path,
            ),
            "raw_path": None,
            "root_path": "",
            "scheme": headers.get("x-forwarded-proto", "https"),
            "query_string": self._encode_query_string(),
            "server": get_server(headers=headers),
            "client": (request_context.get("identity", {}).get("sourceIp"), 0),
            "asgi": {
                "version": "3.0",
                "spec_version": "2.3",
            },
        }

    async def receive(self) -> Message:
        return await self.app_queue.get()

    def _handle_multi_value_headers(
        self, response_headers: list[tuple[bytes, bytes]]
    ) -> tuple[dict[str, str], dict[str, list[str]]]:
        headers: dict[str, str] = {}
        multi_value_headers: dict[str, list[str]] = {}

        for key, value in response_headers:
            decoded_key = key.decode().lower()
            decoded_value = value.decode()

            if decoded_key in multi_value_headers:
                multi_value_headers[decoded_key].append(decoded_value)
            elif decoded_key in headers:
                multi_value_headers[decoded_key] = [
                    headers.pop(decoded_key),
                    decoded_value,
                ]
            else:
                headers[decoded_key] = decoded_value

        return headers, multi_value_headers

    async def send(self, message: Message) -> None:
        if message["type"] == "http.response.start":
            self.lambda_response["statusCode"] = message["status"]
            headers, multi_value_headers = self._handle_multi_value_headers(
                message.get("headers", [])
            )
            self.lambda_response["headers"] = headers
            self.lambda_response["multiValueHeaders"] = multi_value_headers

        elif message["type"] == "http.response.body":
            self.lambda_response["body"] += message.get("body", b"").decode()
            more_body = message.get("more_body", False)

            if not more_body:
                await self.app_queue.put({"type": "http.disconnect"})

        else:
            raise ValueError(f"Unknown message type: {message['type']}")
