"""API Gateway de SeniorVital.

Proxy inverso que redirige peticiones al microservicio
correspondiente según el prefijo de la ruta.
"""

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
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ROUTES = {
    "/auth/": "http://localhost:8001",
    "/catalog/": "http://localhost:8002",
    "/routines/": "http://localhost:8003",
    "/tracking/": "http://localhost:8004",
    "/dashboard/": "http://localhost:8005",
    "/notify/": "http://localhost:8006",
    "/storage/": "http://localhost:8002",
}

client = httpx.AsyncClient(base_url="http://localhost:8000", follow_redirects=True)


async def proxy_request(path: str, request: Request):
    """Reenvía la petición HTTP al microservicio destino.

    :param path: Ruta solicitada (sin el prefijo del gateway).
    :param request: Petición original entrante.
    :return: Respuesta del microservicio destino.
    """
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
    """Ruta comodín que captura todas las peticiones y las redirige.

    :param path: Ruta completa solicitada.
    :param request: Petición HTTP entrante.
    :return: Respuesta del proxy.
    """
    return await proxy_request("/" + path, request)
