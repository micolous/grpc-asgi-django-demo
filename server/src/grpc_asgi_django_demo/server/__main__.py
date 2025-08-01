"""
gRPC ASGI Django demo server implementation.
"""

import argparse
import asyncio
import logging

from django.conf import settings
import grpc
from grpc_health.v1 import health, health_pb2, health_pb2_grpc
from grpc_reflection.v1alpha import reflection

from grpc_asgi_django_demo.proto.v1 import service_pb2_grpc
from .django.asgi import application
from . import asgi_impl, demo_impl

_cleanup_coroutines = []


async def start() -> None:
    """Starts the server."""
    logging.info("Starting server...")
    server = grpc.aio.server()
    # Import here, because Django does some initialisation
    from django.contrib.staticfiles.handlers import ASGIStaticFilesHandler  # type: ignore

    asgi = ASGIStaticFilesHandler(application)

    health_servicer = health.aio.HealthServicer()  # type: ignore

    service_pb2_grpc.add_DemoServiceServicer_to_server(
        demo_impl.DemoServiceImpl(),
        server,
    )
    await health_servicer.set(
        demo_impl.SERVICE_NAME,
        health_pb2.HealthCheckResponse.SERVING,
    )

    port = server.add_insecure_port(
        settings.GRPC_BIND_ADDR,
    )

    service_pb2_grpc.add_AsgiServiceServicer_to_server(
        asgi_impl.AsgiServiceImpl(asgi_application=asgi, port=port),
        server,
    )
    await health_servicer.set(
        asgi_impl.SERVICE_NAME,
        health_pb2.HealthCheckResponse.SERVING,
    )

    health_pb2_grpc.add_HealthServicer_to_server(health_servicer, server)

    reflection.enable_server_reflection(
        [
            demo_impl.SERVICE_NAME,
            health.SERVICE_NAME,
            reflection.SERVICE_NAME,
        ],
        server,
    )

    async def graceful_shutdown():
        logging.info("Shutting down...")
        await server.stop(5)

    _cleanup_coroutines.append(graceful_shutdown())

    await server.start()
    logging.info("Server is listening at port :%d", port)
    await server.wait_for_termination()


def main():
    """Main entrypoint."""
    parser = argparse.ArgumentParser()
    _ = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(start())
    except KeyboardInterrupt:
        pass
    finally:
        if _cleanup_coroutines:
            loop.run_until_complete(*_cleanup_coroutines)
        loop.close()


if __name__ == "__main__":
    main()
