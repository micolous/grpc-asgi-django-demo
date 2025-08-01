# gRPC ASGI Django demo

A proof-of-concept environment to run a complete Django application _inside_ a
Python gRPC server.

While one could _just_ use Django for its non-HTTP features (like its
[ORM][orm]) and call them from another binary, this demo takes it a step further
by sending [HTTP-over-gRPC requests][grpc-http] to
[Django's ASGI handler][django-asgi], in the same way that an
[ASGI protocol server][asgi-proto] (like [daphne][] or [uvicorn][]) would.

Regular HTTP clients (like web browsers) access the service via
[Envoy's gRPC-JSON transcoder][grpc-json], which is configured with
[`google.api.http` annotations][aip-127].

This is much simpler than trying to extend the ASGI spec to support gRPC
framing.

While this demo targets Django, this _could_ also work with other
ASGI-compatible Python web frameworks - but this is left as an exercise for the
reader. :)

> [!WARNING]
>
> This code is "tech demo" quality, and intentionally
> [quite limited](#limitations). It's intended to be a discussion point for
> starting _another_ project, rather than a stand-alone project that you should
> put into production.
>
> This comes with no warranties of any kind, is not actively maintained, and
> probably has security bugs.

## Documentation

- **Start here:** [run the demo environment with Docker Compose](./docs/demo.md)
- **Deep dive:** [architecture overview](./docs/architecture.md), including
  concepts, request flows, and limitations of this demo
- **Got issues, ideas or PRs?** [Contributing to the project](./CONTRIBUTING.md)
- **Found a security bug?** [Security policy](./SECURITY.md)

## License

The code in this repository is licensed under your choice of the
[Apache 2.0](./COPYING.APACHE-2) or
[3-clause BSD license](./COPYING.BSD-3-CLAUSE).

Any [contributions](./CONTRIBUTING.md) made to the project must be your own
work, and shall be licensed under the same terms.

The Docker images in this project contain software distributed under various
other licenses. Of note:

- `asgiref` is distributed under a 3-clause BSD license
- Django is distributed under a 3-clause BSD license
- Envoy is distributed under the Apache 2.0 license
- [`grpc-health-probe`][grpc-health-probe] is distributed under the Apache 2.0
  license

[aip-127]: https://google.aip.dev/127
[asgi-proto]: https://asgi.readthedocs.io/en/latest/specs/main.html#overview
[daphne]: https://github.com/django/daphne
[django-asgi]: https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
[grpc-json]: https://www.envoyproxy.io/docs/envoy/latest/configuration/http/http_filters/grpc_json_transcoder_filter
[grpc-health-probe]: https://github.com/grpc-ecosystem/grpc-health-probe
[grpc-http]: https://www.envoyproxy.io/docs/envoy/latest/configuration/http/http_filters/grpc_json_transcoder_filter#sending-arbitrary-content
[orm]: https://docs.djangoproject.com/en/5.2/topics/db/models/
[uvicorn]: https://www.uvicorn.org/
