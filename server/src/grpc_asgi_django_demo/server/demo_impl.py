import grpc

from grpc_asgi_django_demo.proto.v1 import service_pb2, service_pb2_grpc


SERVICE_NAME = service_pb2.DESCRIPTOR.services_by_name["DemoService"].full_name


class DemoServiceImpl(service_pb2_grpc.DemoServiceServicer):
    async def Add(
        self,
        request: service_pb2.AddRequest,
        context: grpc.aio.ServicerContext,
    ) -> service_pb2.AddResponse:
        # Add some server-side error conditions
        if request.a == 0 and request.b == 0:
            return await context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                "`a` and/or `b` must be set",
            )

        if request.a < 0 or request.b < 0:
            return await context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                "`a` and `b` must be positive",
            )

        return service_pb2.AddResponse(
            o=request.a + request.b,
        )
