# Comparisons with other approaches

_In this document:_

- [Connect RPC](#connect-rpc)
- [Sonora](#sonora)

This commentary was written in August 2025, based on some of the things I looked
at in early 2025. Things will probably change in future, and I haven't captured
all the alternatives. :)

## Connect RPC

[Connect RPC][connectrpc] is a [gRPC-Web-like protocol][connectrpc-protocol]
for building clients and servers, which supports Protobuf and JSON as message
serialisation formats.

Back when I originally wrote this code (early 2025), the
[Python Connect RPC library][connectrpc-py] didn't support writing servers -
there was only a Golang and Node.JS server framework.

[_Fairly recently_][connectrpc-wsgi] (2025-06-30), Connect RPC added support for
running as a WSGI server for the Connect RPC protocol. It has _a lot_ of
differences with ordinary gRPC servers and this demo:

- Connect RPC for Python requires a WSGI protocol server.
  [ASGI support is planned][connectrpc-asgi].

  As a result of targetting ASGI/WSGI,
  [there is no plan to support gRPC][connectrpc-no-grpc]
  ([unlike the Golang version, which does][connectrpc-grpc]).

  This demo runs as a regular gRPC server which accepts TCP connections.

- Connect RPC for Python's WSGI server implementation is a complete WSGI
  application, not middleware (contrast with [Sonora](#sonora)). It needs
  additional code to work to turn it into a middleware that can run alongside
  another WSGI application (like Django) in the same Python process.

  There are [plans to better integrate Connect RPC with ASGI applications][connectrpc-no-grpc].

  This demo can serve an ASGI application using HTTP-over-gRPC, in the same
  Python process.

- Connect RPC for Python only supports HTTP/1.1, so won't support full-duplex
  streaming RPCs. Unlike the Golang version,
  [there are no plans to support HTTP/2][connectrpc-http2], because of "Python's
  immature support for HTTP/2".

  gRPC for Python supports full-duplex streaming RPCs over HTTP/2 on both client
  and server.

- Connect RPC's Python client and server APIs are _completely incompatible_ with
  gRPC's, needing [its own `protoc` plugin][connectrpc-gen] (which, like gRPC's,
  [is published on PyPI][connect-python]).

  The _only_ API that Connect RPC and gRPC share is Protobuf message definitions
  (`*_pb2.py`).

- Connect RPC servers don't need a transcoding proxy server to support browser
  clients.

At present, Connect RPC for Python is fairly immature and doesn't interoperate
with gRPC SDKs, clients or servers, making migration either from or to it very
difficult. It also doesn't (yet) interoperate with other Python web frameworks.

## Sonora

[Sonora][] is an ASGI and WSGI implementation of the [gRPC-Web][] protocol
(which unlike gRPC, _can_ work with any ASGI or WSGI protocol server). It only
supports Protobuf message serialisation (not JSON).

Both Sonora and this demo can run along side another ASGI/WSGI application (like
Django) in the same Python process, but they work quite differently:

- Sonora is an ASGI/WSGI middleware, intercepting gRPC-Web requests before they
  hit your ASGI/WSGI application (which otherwise operates normally).

- This demo acts as an ASGI protocol server for HTTP-over-gRPC requests, passing
  those off to your ASGI application.

Otherwise, servicers (service implementations) in Sonora are written the same
way as in regular gRPC servers, and use the same `protoc` plugins. Sonora's
ASGI/WSGI middleware is an extension of the `grpc.Server` and `grpc.aio.Server`
classes, making it easy to migrate a gRPC server from or to Sonora.

Sonora has some differences with this demo:

- Sonora needs an ASGI or WSGI protocol server to work.

  This demo runs as a regular gRPC server which accepts TCP connections.

- Sonora doesn't need a transcoding proxy to support browser clients.

- Running inside ASGI/WSGI limits Sonora to the features those protocol servers
  provide.

  You don't get things like cancellation, deadlines/timeouts, ATLS, mTLS...

- Sonora uses gRPC-Web, which only has JavaScript clients. There is no reverse
  gRPC-Web to gRPC or gRPC-Web to gRPC-JSON transcoder (at present).

  This demo uses gRPC, which supports many languages. This can be
  [transcoded to gRPC-Web][grpc-web-transcode] or gRPC-JSON.

- This demo only supports `async` gRPC servicers and ASGI.

  Sonora _also_ supports synchronous gRPC servicers and WSGI.

At present, Sonora makes reasonable efforts to interoperate with gRPC SDKs, but
only supports gRPC-Web, which only really supports browser-based applications.

[connect-python]: https://pypi.org/project/connect-python/
[connectrpc]: https://connectrpc.com/
[connectrpc-asgi]: https://github.com/connectrpc/connect-python/blob/34e009e25b16637a1945ec42c4e6069dde8cd466/README.md?plain=1#L397
[connectrpc-gen]: https://github.com/connectrpc/connect-python/blob/main/src/connectrpc/protoc_gen_connect_python/main.py
[connectrpc-grpc]: https://connectrpc.com/docs/go/grpc-compatibility
[connectrpc-http2]: https://connectrpc.com/docs/governance/rfc/python-implementation#non-goals
[connectrpc-no-grpc]: https://connectrpc.com/docs/governance/rfc/python-implementation#justification-for-not-supporting-grpc-on-the-server
[connectrpc-py]: https://github.com/connectrpc/connect-python
[connectrpc-protocol]: https://connectrpc.com/docs/protocol
[connectrpc-wsgi]: https://github.com/connectrpc/connect-python/pull/4
[grpc-http2]: https://github.com/grpc/grpc/blob/master/doc/PROTOCOL-HTTP2.md
[grpc-web]: https://github.com/grpc/grpc/blob/master/doc/PROTOCOL-WEB.md
[grpc-web-transcode]: https://www.envoyproxy.io/docs/envoy/latest/configuration/http/http_filters/grpc_web_filter
[sonora]: https://github.com/public/sonora
