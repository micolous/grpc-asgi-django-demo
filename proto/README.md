# Protobuf descriptors for gRPC ASGI Django Demo

This contains the Protobuf/gRPC service descriptors for the gRPC ASGI Django
demo, and a Python bindings package.

The Python bindings are in the package `grpc_asgi_django_demo.proto`.

The build process is entirely managed with [`hatch-protobuf`][0] and
a custom build hook (to build the `FileDescriptorSet` and enable type hints).

The gRPC service is defined in [`proto/.../service.proto`][3].

## Building

This package can be built with [`uv`][1].

You can build a `sdist` (containing only sources) and `wheel` (containing the
`service.proto` file, generated `_pb2.py` bindings and the service's
`FileDescriptorSet`) with:

```sh
uv build
```

You can build a local virtualenv vith:

```sh
uv sync
```

## `protoc` `site-packages` compatibility

When installing in _non-editable mode_, this package copies the `.proto` files
to your Python `site-packages` directory.

This lets you call `protoc` with `--proto_path` pointing at your `site-packages`
directory, so any other Python Protobuf bindings which `import`s this package's
`.proto` files only needs to depend on the Python package when building.

See [`hatch-protobuf`'s documentation for more details][2].

[0]: https://github.com/nanoporetech/hatch-protobuf/
[1]: https://docs.astral.sh/uv/
[2]: https://github.com/nanoporetech/hatch-protobuf/blob/main/README.md#import-proto-files-from-site-packages
[3]: ./proto/grpc_asgi_django_demo/proto/v1/service.proto
