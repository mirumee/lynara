# Interfaces

Interfaces are classes responsible for the translation of a Lambda event into an ASGI event or request. Those also fulfill the ASGI contract by providing the `scope` data and `receive` and `send` coroutines. 

Currently supported AWS Events are:

| Event                    | Description         |
| ------------------------ | ------------------- |
| AWS API Gateway Proxy V2 | Referred to as HTTP [^1]. |
| AWS API Gateway Proxy V1 | Referred to as REST [^1]. |
| Lambda function URL      | Supported as it's the same as the V2 gateway payload [^2]. |

[^1]: https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-develop-integrations-lambda.html
[^2]: https://docs.aws.amazon.com/lambda/latest/dg/urls-invocation.html#urls-payloads

## Inner workings

### Initialization

An instantiated interface is provided with the instance of the ASGI app, the lambda event and lambda context. Builds the body of the request that will be sent to the application and queues it in it's `app_queue`.

Also here is where the default response body returned by the lambda will start to take shape.

```python title="my_interface.py" linenums="1"
from lynara import HTTPInterface
from lynara.types import ASGIApp, LambdaEvent


class MyEventInterface(HTTPInterface):

    def __init__(self, app: ASGIApp, event: LambdaEvent, context) -> None:
        super().__init__(app, event, context)
        self.lambda_response = {
            "cookies": [],
            "isBase64Encoded": False,
            "statusCode": 200,
            "body": "",
            "headers": {},
        }

        body = b"body generated from event and context"

        self.app_queue.put_nowait(# (1)!
            {
                "type": "http.request",
                "body": body,
                "more_body": False,
            }
        )
```

1. The `self.app_queue` is the medium use to transfer messages from and to your ASGI application. Here is a beginning of a HTTP request prepared for the application to pick up when ready. 

### Scope

Having the event and context on `self` generate a [ASGI HTTP Connection Scope](https://asgi.readthedocs.io/en/latest/specs/www.html#http-connection-scope). You need to carefully check which data is available in the Lambda event and map it to the scope object.

```python title="my_interface.py" linenums="27"
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
```

### Receive

This is the coroutine used by the application when it's ready to **receive** a request. The dict that was prepared on initialization will be "sent to the application" here. This is the only body your application will receive - which is exactly what you are after in the single event - single lifetime environment like a lambda. 

!!! info "Note about the single event - single lifetime"

    This is not tested yet but in theory it would be possible to handle batch events with Lynara as well, taking SQS for an example - if an event with many messages in a batch would be queued here, then each message could be received by the ASGI app as a request (assuming that an HTTP scope can be made out of an SQS event).

```python title="my_interface.py" linenums="52"
    async def receive(self) -> Message:
        return await self.app_queue.get()
```


### Send

Coroutine used by the application to write a response. It can be invoked many times for one request with the response headers and the body which can be chunked. Finally it queues a `http.disconnect` message that informs the application that the client (our lambda handler) is done with it.

```python title="my_interface.py" linenums="55"
    async def send(self, message: Message) -> None:
        if message["type"] == "http.response.start":
            self.lambda_response["statusCode"] = message["status"]
            for key, value in message.get("headers", []):
                if key.decode().lower() == "set-cookie":#(1)!
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

```

1. API Gateway V2 needs cookies in a separate response field so we need to extract those here

This is where your interface would build the lambda response.


### Match

This class method will be used in the future in a guessing mechanism that could infer the interface based on the shape of the incoming event.
