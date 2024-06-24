# Lynara

Lynara lets you run your ASGI (Starlette, FastAPI, Django) applications in a serverless runtime like AWS Lambda. It closely follows what Uvicorn does with the exception that there's no long-lived loop and instead a Lambda event is translated to an ASGI HTTP event and served to the application accordingly.

To use Lynara in an AWS Lambda handler you can:

```python
import asyncio
from lynara import Lynara, APIGatewayProxyEventV2Interface


app = FastAPI()
lynara = Lynara(app=app)

def lambda_handler(event, context):
    return asyncio.run(lynara.run(event, context, APIGatewayProxyEventV2Interface))

```

Lynara will produce a dictionary with an AWS Lambda HTTP response for your handler to respond with.


## Development

Get Hatch (pipx is a good option): https://hatch.pypa.io/latest/install/#pipx.

```
pipx install hatch
```

Install all Python versions: 

```
hatch python install all
```

### Running tests

> https://hatch.pypa.io/1.10/tutorials/testing/overview/#passing-arguments

For development you might find the following useful to use with `pdb`:
```
hatch test -- -s -n 0 --log-cli-level
```

To run a single test:
```
hatch -v test -- "tests/test_fastapi.py::test_fastapi_app_lifespan[on]"
```

For HTML coverage report 
```
hatch test -- --cov --cov-report=html
```

## Contributing

Make sure to run tests, static checks and `mypy` before submitting a change:

```
hatch run check
```

## Writing docs

```
hatch docs:serve
```
