# Introduction

Lynara is a tool that allows running Python ASGI applications in an AWS Lambda runtime.

When writing Lynara, we closely followed what [Uvicorn](https://www.uvicorn.org/) does to fulfill its role as an ASGI server. However, instead of running in a long-lived loop serving many requests, Lynara receives an AWS event, passes it to the application, and stops.

## Quickstart

Install Lynara:

=== "Poetry"

    ```
    poetry add lynara
    ```

=== "pip"

    ```
    pip install lynara
    ```

Use Lynara with your ASGI application:

```python title="app.py" linenums="1" 
import asyncio
from lynara import Lynara, APIGatewayProxyEventV2Interface
from fastapi import FastAPI

app = FastAPI()# (1)!
lynara = Lynara(app=app)

def lambda_handler(event, context):
    return asyncio.run(
        lynara.run(event, context, APIGatewayProxyEventV2Interface)
    )
```

1. The `app` is loaded once for every cold start.

## Rationale

We wanted to quickly deploy small and scalable Python applications on Lambdas. Our goal was to support small [FastAPI](https://fastapi.tiangolo.com/) applications with a few endpoints, but not as small as a single lambda handler. Leveraging [Starlette](https://www.starlette.io/) or [FastAPI](https://fastapi.tiangolo.com/) in a serverless runtime was an appealing idea. Although there are existing solutions like [Mangum](https://github.com/jordaneremieff/mangum) and [aws-lambda-web-adapter](https://github.com/awslabs/aws-lambda-web-adapter), they did not meet our needs.

Another aspect is being able to jump off a serverless environment as Lambdas are cheaper than Fargates and EC2s only up to a certain point. Here's a neat [AWS Cost Estimator](https://www.aws-geek.com/?config=eyJsYW1iZGFQYXJhbXMiOnsiYXZnUmVzcG9uc2VUaW1lSW5NcyI6MTAwLCJyZXF1ZXN0cyI6MjAwMCwiaW50ZXJ2YWwiOiJtaW51dGUiLCJsYW1iZGFTaXplIjoxMjgsImZyZWVUaWVyIjpmYWxzZX0sImZhcmdhdGVQYXJhbXMiOnsiZmFyZ2F0ZUNvbmZpZyI6eyJ2Q1BVIjoyLCJtZW1vcnkiOjR9LCJudW1iZXJPZlRhc2tzIjoyLCJhcHBSdW5uZXJDb25maWciOnsiZW5hYmxlZCI6dHJ1ZSwicnBtUGVyVGFzayI6NjAwMH19LCJlYzJQYXJhbXMiOnsiaW5zdGFuY2VUeXBlIjoidDMubWVkaXVtIiwibnVtYmVyT2ZJbnN0YW5jZXMiOjJ9LCJldmVudHNQYXJhbXMiOnsiaW50ZXJ2YWwiOiJob3VyIiwiZXZlbnRzIjo1MDAwMDAwLCJjb25zdW1lcnMiOjEsImF2Z1BheWxvYWRTaXplIjo1MDAwLCJzaGFyZHMiOjd9fQ==) that might help you understand the costs.

What started as an evening experiment has resulted in a functional tool. Please star it on GitHub, share feedback, and follow the project if you're interested.

## Others from Mirumee

- [Smyth](https://github.com/mirumee/smyth) - A tool improving the Lambda developer experience
- [Ariadne](https://ariadnegraphql.org/) - Schema-first, Python GraphQL server
- [Ariadne Codegen](https://github.com/mirumee/ariadne-codegen) - GraphQL Python code generator
