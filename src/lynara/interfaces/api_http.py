from base64 import b64decode

from lynara.interfaces.base import HTTPInterface
from lynara.interfaces.utils import get_server, strip_api_gateway_path
from lynara.types import ASGIApp, LambdaEvent, Message, Scope


class APIGatewayProxyEventV2Interface(HTTPInterface):
    def __init__(
        self, app: ASGIApp, event: LambdaEvent, context, base_path: str | None = None
    ) -> None:
        super().__init__(app=app, event=event, context=context, base_path=base_path)
        self.lambda_response = {
            "cookies": [],
            "isBase64Encoded": False,
            "statusCode": 200,
            "body": "",
            "headers": {},
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
        return event.get("version") == "2.0" and "requestContext" in event

    @property
    def scope(self) -> Scope:
        headers = {k.lower(): v for k, v in self.event.get("headers", {}).items()}
        request_context = self.event["requestContext"]
        path = request_context["http"]["path"]
        self._method = request_context["http"]["method"]

        return {
            "type": "http",
            "asgi": {
                "version": "3.0",
                "spec_version": "2.3",
            },
            "http_version": "1.1",
            "method": self._method,
            "scheme": headers.get("x-forwarded-proto", "https"),
            "path": strip_api_gateway_path(path, base_path=self.base_path),
            "raw_path": None,
            "query_string": self.event.get("rawQueryString", "").encode(),
            "root_path": "",
            "headers": [(k.encode(), v.encode()) for k, v in headers.items()],
            "client": (request_context["http"]["sourceIp"], 0),
            "server": get_server(headers=headers),
        }

    async def receive(self) -> Message:
        return await self.app_queue.get()

    async def send(self, message: Message) -> None:
        if message["type"] == "http.response.start":
            self.lambda_response["statusCode"] = message["status"]
            for key, value in message.get("headers", []):
                if key.decode().lower() == "set-cookie":
                    self.lambda_response["cookies"].append(value.decode())
                else:
                    self.lambda_response["headers"][key.decode()] = value.decode()

        elif message["type"] == "http.response.body":
            self.lambda_response["body"] += message.get("body", b"").decode()
            more_body = message.get("more_body", False)

            if not more_body:
                await self.app_queue.put({"type": "http.disconnect"})

        else:
            raise ValueError(f"Unknown message type: {message['type']}")
