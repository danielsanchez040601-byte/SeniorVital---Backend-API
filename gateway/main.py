import os
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
import httpx

app = FastAPI(
    title="SeniorVital API Gateway",
    version="1.0.0",
    docs_url="/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ROUTES = {
    "/auth/": "http://127.0.0.1:8001",
    "/catalog/": "http://127.0.0.1:8002",
    "/routines/": "http://127.0.0.1:8003",
    "/tracking/": "http://127.0.0.1:8004",
    "/dashboard/": "http://127.0.0.1:8005",
    "/notify/": "http://127.0.0.1:8006",
    "/storage/": "http://127.0.0.1:8002",
}

client = httpx.AsyncClient(base_url="http://127.0.0.1:8000", follow_redirects=True)


async def proxy_request(path: str, request: Request):
    target_base = None
    for prefix, base in ROUTES.items():
        if path.startswith(prefix):
            target_base = base
            break
    if not target_base:
        return Response(status_code=502, content='{"detail":"No route found"}')

    target_url = f"{target_base}{path}"
    body = await request.body()
    headers = dict(request.headers)
    headers.pop("host", None)

    try:
        resp = await client.request(
            method=request.method,
            url=target_url,
            content=body,
            headers=headers,
            params=request.query_params,
        )
        return Response(
            content=resp.content,
            status_code=resp.status_code,
            headers=dict(resp.headers),
        )
    except httpx.RequestError:
        return Response(
            status_code=502,
            content='{"detail":"Service unavailable"}',
        )


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def catch_all(path: str, request: Request):
    return await proxy_request("/" + path, request)
