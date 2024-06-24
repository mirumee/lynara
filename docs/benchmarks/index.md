# Benchmarks

We developed a benchmarking suite to test if Lynara causes any penalties to the load time of a Lambda. Lynara itself does not, but there are some interesting results worth sharing.

## Tests

We prepared four different applications doing the same thing: receiving a `POST` request with a `{"name": "Ana"}` payload and outputting a `"Hello Ana"` string.

!!! info "Notice"
    It's important to note that FastAPI and Django are doing a bit more than the "pure lambda" applications, such as checking if the HTTP method is indeed a `POST`, whereas the others do not.

=== "Pure Lambda"

    To set a baseline, we tested a basic Lambda:

    ```python linenums="1" 
    import json

    def lambda_handler(event, context):
        json_data = json.loads(event['body'])
        res = {
            "statusCode": 200,
            "headers": {
                "Content-Type": "*/*"
            },
            "body": f"Hello {json_data.get('name', 'Unknown')}"
        }
        return res
    ```

=== "Pure Async Lambda"

    A somewhat controversial setup forcing an async loop:

    ```python linenums="1" 
    import asyncio
    import json

    async def handler(event, context):
        json_data = json.loads(event['body'])
        res = {
            "statusCode": 200,
            "headers": {
                "Content-Type": "*/*"
            },
            "body": f"Hello {json_data.get('name', 'Unknown')}"
        }
        return res

    def lambda_handler(event, context):
        return asyncio.run(handler(event, context))
    ```

=== "FastAPI"

    ```python linenums="1" 
    import asyncio
    from fastapi import FastAPI
    from lynara import Lynara, APIGatewayProxyEventV1Interface, APIGatewayProxyEventV2Interface

    app = FastAPI()
    lynara = Lynara(app=app)

    @app.post("/hello")
    async def hello(payload: dict):
        return {"data": f"Hello {payload.get('name', 'Unknown')"}

    def lambda_handler_v2(event, context):
        return asyncio.run(lynara.run(event, context, APIGatewayProxyEventV2Interface))

    def lambda_handler_v1(event, context):
        return asyncio.run(lynara.run(event, context, APIGatewayProxyEventV1Interface))
    ```

=== "Starlette"

    ```python linenums="1" 
    import asyncio
    import json
    from starlette.applications import Starlette
    from starlette.responses import JSONResponse
    from starlette.routing import Route
    from lynara import Lynara, APIGatewayProxyEventV1Interface, APIGatewayProxyEventV2Interface

    async def hello(request):
        payload = await request.json()
        return JSONResponse({"data": f"Hello {payload.get('name', 'Unknown')}"})

    app = Starlette(routes=[Route('/hello', hello, methods=['POST'])])
    lynara = Lynara(app=app)

    def lambda_handler_v2(event, context):
        return asyncio.run(lynara.run(event, context, APIGatewayProxyEventV2Interface))

    def lambda_handler_v1(event, context):
        return asyncio.run(lynara.run(event, context, APIGatewayProxyEventV1Interface))
    ```

=== "Django"

    ```python linenums="1" 
    import asyncio
    import json
    import os
    import sys
    from django.conf import settings
    from django.core.asgi import get_asgi_application
    from django.http import JsonResponse
    from django.urls import path
    from django.utils.crypto import get_random_string
    from django.views.decorators.http import require_http_methods
    from lynara import Lynara, APIGatewayProxyEventV1Interface, APIGatewayProxyEventV2Interface

    settings.configure(
        DEBUG=(os.environ.get("DEBUG", "") == "1"),
        ALLOWED_HOSTS=["*"],
        ROOT_URLCONF=__name__,
        SECRET_KEY=get_random_string(50),
        MIDDLEWARE=["django.middleware.common.CommonMiddleware"],
    )

    @require_http_methods(["POST"])
    def hello_world(request):
        body = json.loads(request.body)
        return JsonResponse({"data": f"Hello {body.get('name', 'Unknown')}"})

    urlpatterns = [
        path("hello", hello_world),
    ]
    application = get_asgi_application()
    lynara = Lynara(app=application)

    def lambda_handler_v2(event, context):
        return asyncio.run(lynara.run(event, context, APIGatewayProxyEventV2Interface))

    def lambda_handler_v1(event, context):
        return asyncio.run(lynara.run(event, context, APIGatewayProxyEventV1Interface))
    ```

The test was conducted with Locust making POST requests to AWS Lambdas from an M1 MacBook Pro with 1000 concurrent users. The Lambda setup:

- Default 1000 concurrent lambda invocation per account cap
- 128MB Memory
- x86 runtime
- Zip upload (no containers)

## Results

!!! warning "Limited tests"

    The test machine could not exhaust the capabilities of AWS. These benchmarks set some expectations but should not be used for cost savings or other financial decisions. You should do your own measurements for your specific application.

Use the tabs below to view the data in charts.

=== "Table"

    <table>
        <thead>
            <tr>
                <th role="columnheader">Setup</th>
                <th role="columnheader">Proxy</th>
                <th role="columnheader">RPS <small>(higher is better)</small></th>
                <th role="columnheader">Lambda Concurrent Executions <small>(lower is better)</small></th>
                <th role="columnheader">First Response After <small>(lower is better)</small></th>
                <th role="columnheader">Efficiency per Invocation <small>(higher is better)</small></th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Pure Lambda</td>
                <td>V1 (API Gateway)</td>
                <td>2865.1</td>
                <td>324</td>
                <td>avg 0.43s (max 0.47s, min 0.39s)</td>
                <td>8.42</td>
            </tr>
            <tr class="benchmarks-best-result">
                <td>Pure Lambda</td>
                <td>V2 (Function URL)</td>
                <td>2884.3</td>
                <td>264</td>
                <td>avg 0.49s (max 0.56s, min 0.44s)</td>
                <td>10.92</td>
            </tr>
            <tr>
                <td>Lynara + Starlette</td>
                <td>V1 (API Gateway)</td>
                <td>2806.6</td>
                <td>327</td>
                <td>avg 0.66s (max 0.79s, min 0.18s)</td>
                <td>7.54</td>
            </tr>
            <tr>
                <td>Lynara + Starlette</td>
                <td>V2 (Function URL)</td>
                <td>2845.7</td>
                <td>328</td>
                <td>avg 0.67s (max 0.81s, min 0.20s)</td>
                <td>8.67</td>
            </tr>
            <tr>
                <td>Lynara + FastAPI</td>
                <td>V1 (API Gateway)</td>
                <td>2769.4</td>
                <td>362</td>
                <td>avg 1.50s (max 1.69s, min 1.17s)</td>
                <td>7.65</td>
            </tr>
            <tr>
                <td>Lynara + FastAPI</td>
                <td>V2 (Function URL)</td>
                <td>2871.1</td>
                <td>317</td>
                <td>avg 1.54s (max 1.76s, min 1.23s)</td>
                <td>9.05</td>
            </tr>
            <tr class="benchmarks-worst-result">
                <td>Lynara + Django</td>
                <td>V1 (API Gateway)</td>
                <td>2560.8</td>
                <td>684</td>
                <td>avg 1.34s (max 1.44s, min 1.08s)</td>
                <td>3.74</td>
            </tr>
            <tr>
                <td>Lynara + Django</td>
                <td>V2 (Function URL)</td>
                <td>2751.0</td>
                <td>638</td>
                <td>avg 1.44s (max 1.56s, min 1.33s)</td>
                <td>4.31</td>
            </tr>
            <tr>
                <td>Pure Async Lambda</td>
                <td>V1 (API Gateway)</td>
                <td>2752.9</td>
                <td>339</td>
                <td>avg 0.55s (max 0.74s, min 0.48s)</td>
                <td>8.12</td>
            </tr>
            <tr>
                <td>Pure Async Lambda</td>
                <td>V2 (Function URL)</td>
                <td>2906.7</td>
                <td>307</td>
                <td>avg 0.54s (max 0.84s, min 0.25s)</td>
                <td>9.46</td>
            </tr>
        </tbody>
    </table>


=== "RPS / Efficiency"

    Measuring the cost of ownership of such Lambdas, we can see that (unless we're using Django) we are able to achieve similar traffic throughput at a similar cost when using the ASGI frameworks as we would with a "Pure" Lambda.

    ```vegalite
    {
        "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
        "background": "#00000000",
        "height": 500,
        "data": {
            "url": "data.json",
            "format": {
                "type": "json"
            }
        },
        "resolve": {"scale": {"y": "independent"}},
        "layer": [
            {
                "mark": {
                    "type": "bar",
                    "clip": true
                },
                "encoding": {
                    "x": {
                        "axis": {
                            "titleFontSize": 24,
                            "labelFontSize": 20
                        },
                        "field": "setup",
                        "title": "Setup"
                    },
                    "y": {
                        "axis": {
                            "titleFontSize": 24,
                            "labelFontSize": 20
                        },
                        "field": "rps",
                        "title": "Requests Per Second",
                        "type": "quantitative",
                        "scale": {
                            "domain": [
                                2500,
                                2950
                            ],
                            "zero": false
                        }
                    },
                    "xOffset": {
                        "field": "proxy"
                    },
                    "color": {
                        "field": "proxy",
                        "labelFontSize": 20
                    }
                }
            },
            {
                "mark": {
                    "type": "line",
                    "stroke": "#f1c36f"
                },
                "encoding": {
                    "x": {
                        "field": "setup"
                    },
                    "xOffset": {
                        "field": "proxy"
                    },
                    "y": {
                        "axis": {
                            "titleFontSize": 24,
                            "labelFontSize": 20
                        },
                        "field": "efficiencyPerInvocation",
                        "type": "quantitative",
                        "title": "Efficiency"
                    }
                }
            }
        ]
    }
    ```

=== "RPS / Executions"

    Django not only handled the least amount of traffic but was also the most costly.

    ```vegalite
    {
        "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
        "background": "#00000000",
        "height": 500,
        "data": {
            "url": "data.json",
            "format": {
                "type": "json"
            }
        },
        "resolve": {"scale": {"y": "independent"}},
        "layer": [
            {
                "mark": {
                    "type": "bar",
                    "clip": true
                },
                "encoding": {
                    "x": {
                        "axis": {
                            "titleFontSize": 24,
                            "labelFontSize": 20
                        },
                        "field": "setup",
                        "title": "Setup"
                    },
                    "y": {
                        "axis": {
                            "titleFontSize": 24,
                            "labelFontSize": 20
                        },
                        "field": "rps",
                        "title": "Requests Per Second",
                        "type": "quantitative",
                        "scale": {
                            "domain": [
                                2500,
                                2950
                            ],
                            "zero": false
                        }
                    },
                    "xOffset": {
                        "field": "proxy"
                    },
                    "color": {
                        "field": "proxy",
                        "labelFontSize": 20
                    }
                }
            },
            {
                "mark": {
                    "type": "line",
                    "stroke": "#e6695b"
                },
                "encoding": {
                    "x": {
                        "field": "setup"
                    },
                    "xOffset": {
                        "field": "proxy"
                    },
                    "y": {
                        "axis": {
                            "titleFontSize": 24,
                            "labelFontSize": 20
                        },
                        "field": "lambdaConcurrentExecutions",
                        "type": "quantitative",
                        "title": "Executions"
                    }
                }
            }
        ]
    }
    ```

=== "First Response"

    Response times are best and most consistent for the most basic Lambda. Starlette was not far behind, whereas Django and FastAPI took the longest to start.

    ```vegalite
    {
        "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
        "background": "#00000000",
        "height": 500,
        "data": {
            "url": "data.json",
            "format": {
                "type": "json"
            }
        },
        "encoding": {
            "x": {
                "axis": {
                    "domain": false,
                    "titleFontSize": 24,
                    "labelFontSize": 20
                },
                "field": "setup",
                "title": "Setup"
            },
            "xOffset": {
                "field": "proxy"
            },
            "y": {
                "type": "quantitative",
                "scale": {"domain": [0, 2]},
                "axis": {"title": "Time (s)", 
                            "titleFontSize": 24,
                            "labelFontSize": 20}
            },
            "color": {
                "field": "proxy",
                "labelFontSize": 20
            }
        },
        "layer": [
            {
                "mark": {
                    "type": "point",
                    "shape": "square",
                    "color": "#fff",
                    "size": 100
                },
                "encoding": {
                    "y": {
                        "field": "firstResponseAfter.avg"
                    }
                }
            },
            {
                "mark": {
                    "type": "bar",
                    "clip": true,
                    "width": 3,
                    "color": "#fff"
                },
                "encoding": {
                    "y": {
                        "field": "firstResponseAfter.min"
                    },
                    "y2": {
                        "field": "firstResponseAfter.max"
                    }
                }
            }
        ]
    }
    ```

    There is a clear penalty on the cold start time when "bigger" frameworks need to load for the first time. This tells us that there should be a good reason to use a heavier framework, such as time to market or a team's ability to use a certain framework.
