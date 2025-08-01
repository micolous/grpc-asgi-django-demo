import asyncio
import logging
from typing import Iterable, NoReturn, Optional, cast

from asgiref.typing import (
    ASGI3Application,
    ASGIReceiveCallable,
    ASGISendCallable,
    HTTPScope,
    HTTPRequestEvent,
    HTTPDisconnectEvent,
)
from google.api import httpbody_pb2
import grpc
from httpx import URL

from grpc_asgi_django_demo.proto.v1 import service_pb2, service_pb2_grpc

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.INFO)

_HTTP_DISCONNECT_EVENT: HTTPDisconnectEvent = {
    "type": "http.disconnect",
}

SERVICE_NAME = service_pb2.DESCRIPTOR.services_by_name["AsgiService"].full_name


def metadata_value_to_str(value: str | bytes) -> str:
    """
    Decodes a grpc.aio._typing.MetadataValue as Latin-1
    """
    if isinstance(value, str):
        return value
    else:
        return cast(bytes, value).decode("latin1")


def metadata_value_to_bytes(value: str | bytes) -> bytes:
    """
    Encodes a grpc.aio._typing.MetadataValue as Latin-1
    """
    if isinstance(value, str):
        return value.encode("latin1")
    else:
        return cast(bytes, value)


async def context_to_scope(
    context: grpc.aio.ServicerContext,
    content_type: str,
    port: int,
) -> HTTPScope | NoReturn:
    """
    Converts a gRPC `ServicerContext` containing an Envoy gRPC-JSON transcoder
    request into an [ASGI `HTTPScope`](https://asgi.readthedocs.io/en/latest/specs/www.html#http-connection-scope).

    **Security warning:** this function implicitly trusts all HTTP headers
    passed from the client, so can only be used with trusted upstream clients.

    This uses the following HTTP headers when setting up the `HTTPScope`:

    * `x-envoy-original-method` (required): HTTP request method (verb), eg:
      `GET`.
    * `x-envoy-original-path` (required): The full `raw_path` of the incoming
      HTTP request, as-is from the client (ie: including percent-encoded
      characters).
    * `x-forwarded-proto`: The forwarded protocol, either `http` or `https`. If
      not provided, defaults to `http`.
    * `x-forwarded-host`: The original `:authority` header (or `Host`) of the
      request. Defaults to `localhost:{port}` if not provided.

    These headers are still present in the final request passed to the ASGI
    application.

    Args:
        context: gRPC ServicerContext
        content_type: Content type of the HTTP request body.
        port: TCP port that the gRPC server is listening on, used as a default
            if missing from the `x-forwarded-host` header.

    Returns:
        `HTTPScope` on success

    Raises:
        Exception: On invalid inputs, and aborts the RPC with `context.abort()`.
    """
    method: Optional[str] = None
    scheme: str = "http"
    path: Optional[str] = None
    raw_path: Optional[bytes] = None
    query_string: bytes = b""
    headers: list[tuple[bytes, bytes]] = []
    authority: Optional[bytes] = None
    client: Optional[tuple[str, int]] = None

    _LOGGER.debug("Peer: %r", context.peer())
    peer_parts = context.peer().partition(",")[0].split(":", maxsplit=2)
    # Peer naming: https://github.com/grpc/grpc/blob/master/doc/naming.md
    # TODO: IPv6 addresses get escaped: https://github.com/grpc/grpc/issues/30852
    if len(peer_parts) >= 2 and peer_parts[0] in ("ipv4", "ipv6"):
        client = (peer_parts[1], int(peer_parts[2]) if len(peer_parts) >= 3 else 0)

    if content_type:
        headers.append((b"content-type", content_type.encode("latin1")))

    invocation_metadata = context.invocation_metadata()
    if invocation_metadata:
        for key, value in invocation_metadata:
            headers.append((key.encode("latin1"), metadata_value_to_bytes(value)))

            # Check for special Envoy headers
            # https://www.envoyproxy.io/docs/envoy/latest/configuration/http/http_filters/grpc_json_transcoder_filter.html#headers
            if key == "x-envoy-original-method" and method is None:
                method = metadata_value_to_str(value)
            elif key == "x-envoy-original-path" and path is None:
                # x-envoy-original-path is equivalent to raw_path
                raw_path = metadata_value_to_bytes(value)

                # Use httpx.URL to parse the other components.
                url = URL(raw_path=raw_path)
                path = url.path
                query_string = url.query
            elif key == "x-forwarded-proto":
                scheme = metadata_value_to_str(scheme)
            elif key == "x-forwarded-host":
                # TODO: pass `:authority` header when gRPC Python server library
                # supports it: https://github.com/grpc/grpc/issues/38906
                #
                # Envoy passes the original `:authority` header as
                # `x-forwarded-host`:
                # https://www.envoyproxy.io/docs/envoy/latest/configuration/http/http_conn_man/headers.html#x-forwarded-host
                #
                # Django can use that header too, but per ASGI spec, we need to
                # provide *something* here.
                authority = metadata_value_to_bytes(value)

    if not authority:
        _LOGGER.warning("Request missing x-forwarded-host header")
        server = ("localhost", port)
        authority = f"{server[0]}:{server[1]}".encode("latin1")
    else:
        # Use `x-forwarded-host` header (in `authority`) for `server`
        h, _, p = authority.decode("latin1").partition(":")
        server = (h, int(p) if p else port)

    # Authority header must be first
    headers.insert(0, (b":authority", authority))

    # Check presence of required headers
    if not method:
        return await context.abort(
            grpc.StatusCode.INVALID_ARGUMENT,
            "missing x-envoy-original-method",
        )
    if not scheme:
        return await context.abort(
            grpc.StatusCode.INVALID_ARGUMENT,
            "missing x-forwarded-proto",
        )
    if not raw_path or not path:
        return await context.abort(
            grpc.StatusCode.INVALID_ARGUMENT,
            "missing or invalid x-envoy-original-path",
        )

    # https://asgi.readthedocs.io/en/latest/specs/www.html#http-connection-scope
    return {
        "type": "http",
        "asgi": {
            "version": "3.0",
            # changes in newer versions only relevant to WebSockets
            "spec_version": "2.0",
        },
        # Envoy converts HTTP/1.1 requests into gRPC-over-HTTP/2
        "http_version": "2",
        "method": method,
        "scheme": scheme,
        "path": path,
        "raw_path": raw_path,
        "query_string": query_string,
        "root_path": "",
        "headers": headers,
        "client": client,
        "server": server,
        "extensions": {},
        # "state"
    }


def http_body_to_asgi_request(request: httpbody_pb2.HttpBody) -> HTTPRequestEvent:
    """
    Converts a `HttpBody` into an
    [ASGI `HTTPRequestEvent`](https://asgi.readthedocs.io/en/latest/specs/www.html#request-receive-event).
    """
    return {
        "type": "http.request",
        "body": request.data,
        # TODO: handle chunked encoding
        "more_body": False,
    }


class Recv:
    """
    HTTP request lifecycle message queue for an ASGI application.

    This has four states:

    1. **Initial state:** pending `HTTPRequestEvent`
    2. Waiting for `Recv.disconnect()` signal from the server
    3. Waiting for `Recv.disconnect()` signal to be consumed by the application
    4. **Final state:** `Recv.disconnect()` signal has been consumed
    """

    def __init__(self, request_event: HTTPRequestEvent):
        """
        Provides HTTP request lifecycle events to an ASGI application as an
        `ASGIReceiveCallable`.

        Args:
            request_event: `HTTPRequestEvent` to provide to the application on
                its first call (`Recv.__call__`).
        """
        self._request_event: Optional[HTTPRequestEvent] = request_event
        self._disconnect_signal: Optional[asyncio.Event] = asyncio.Event()

    async def __call__(self) -> HTTPRequestEvent | HTTPDisconnectEvent:
        """
        Provide HTTP request lifecycle events to an ASGI application.

        The first call will provide a `HTTPRequestEvent` immediately.

        The second call will wait for the ASGI server to call
        `Recv.disconnect()`, and then provide a `HTTPDisconnectEvent`.

        After `HTTPDisconnectEvent` has been consumed by at least one blocked
        call, further calls to this function will immediately raise
        `RuntimeError`.

        ### Concurrency

        If multiple tasks call this function while waiting for a disconnection
        signal, they will *all* wait for `Recv.disconnect()` and receive a
        `HTTPDisconnectEvent`.
        """
        if self._request_event is not None:
            e = self._request_event
            self._request_event = None
            return e
        if self._disconnect_signal is not None:
            await self._disconnect_signal.wait()
            self._disconnect_signal = None
            return _HTTP_DISCONNECT_EVENT

        raise RuntimeError("Invalid ASGI receiver queue state")

    def disconnect(self):
        """
        Signal to the ASGI application that the HTTP client has disconnected.

        Raises:
            RuntimeError: if the ASGI application has already consumed a
                disconnect signal.
        """
        if self._disconnect_signal is None:
            raise RuntimeError("Invalid ASGI receiver queue state")
        self._disconnect_signal.set()


class AsgiServiceImpl(service_pb2_grpc.AsgiServiceServicer):
    def __init__(self, asgi_application: ASGI3Application, port: int):
        self._app = asgi_application
        self._port = port

    async def _call(
        self, scope: HTTPScope, recv: ASGIReceiveCallable, send: ASGISendCallable
    ) -> None:
        await self._app(scope, recv, send)

    async def Handler(
        self,
        request: httpbody_pb2.HttpBody,
        context: grpc.aio.ServicerContext,
    ) -> httpbody_pb2.HttpBody:
        # We're using a "custom" handler, so "Http()" is everything.
        # However, there's nothing in the spec to pass the original method
        # across - only Envoy extensions.
        #
        # This implicitly trusts the proxy headers.
        scope = await context_to_scope(context, request.content_type, self._port)

        _LOGGER.debug("Request headers: %r", scope["headers"])

        # Create receive and send queue that we'll send to the application
        receive_q = Recv(http_body_to_asgi_request(request))
        send_q = asyncio.Queue()

        # Call the application
        _LOGGER.debug("Calling ASGI application...")

        response = httpbody_pb2.HttpBody()

        async with asyncio.TaskGroup() as tg:
            initial_metadata_task: Optional[asyncio.Task[None]] = None
            app_task = tg.create_task(self._call(scope, receive_q, send_q.put))

            started = False
            more_body = True
            _LOGGER.debug("Waiting for server to respond...")
            while True:
                evt = await send_q.get()
                _LOGGER.debug("Got event %r", evt["type"])
                if evt["type"] == "http.response.start":
                    if started:
                        raise ValueError(
                            "app sent http.response.start when we've already started"
                        )
                    started = True

                    headers: list[tuple[str, bytes]] = []
                    headers.append(("x-http-code", str(evt["status"]).encode("latin1")))

                    # Headers
                    asgi_headers: Iterable[tuple[bytes, bytes]] = evt.get("headers", [])
                    for k, v in asgi_headers:
                        # Spec says "header names must be lowercased", but Django doesn't do this
                        # gRPC requires them to be lowercased
                        k = k.decode().lower()
                        if k == "content-type":
                            response.content_type = v.decode()
                            continue

                        headers.append((k, v))
                    _LOGGER.debug("Sending metadata: %r", headers)
                    initial_metadata_task = tg.create_task(
                        context.send_initial_metadata(headers)
                    )
                elif evt["type"] == "http.response.body":
                    if not more_body:
                        raise ValueError(
                            "app sent http.response.body when it said !more_body"
                        )
                    more_body = evt.get("more_body", False)
                    response.data += evt.get("body", b"")
                else:
                    _LOGGER.warning("unknown event type: %r", evt["type"])

                send_q.task_done()
                if not more_body:
                    break

            # Tell the app we're finished with it
            _LOGGER.debug("Signalling client disconnect...")
            receive_q.disconnect()

            # Ensure initial metadata was sent to the client
            if initial_metadata_task is not None:
                await initial_metadata_task

            _LOGGER.debug("Waiting for app_task to finish...")
            await app_task

        _LOGGER.debug("Returning response...")
        return response
