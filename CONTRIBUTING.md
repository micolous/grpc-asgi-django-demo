# Contributing to gRPC ASGI Django demo

Thank you for your interest in contributing to this project!

This is based on a demo that I originally developed at a previous employer, who
were happy for any code _not_ related to their core business to be released as
open source.

The scope of this project is to prove that it is possible to run a Python ASGI
web application from inside of a Python gRPC server.

Generally speaking, the answer to any reported issue or feature request will be:

> _"Pull requests welcome."_

There's no ongoing maintenance plan for this repository, and I wasn't paid to
release any of this. It's just something I thought was novel, and may be useful
to someone else.

## Repository layout

- `.github`: GitHub settings
- `.vscode`: Visual Studio Code settings
- `docs`: Documentation and architecture overview
- `envoy`: Envoy configuration, used for gRPC-JSON transcoding
- `proto`: Protobuf/gRPC service descriptors and Python bindings
- `scripts`: Contains a setup script
- `server`: gRPC ASGI Django demo server

## Scope

There are _a lot_ of limitations in this tech demo, and I've cut a lot of this
down from what that internal project was in order to focus on the interesting
part (serving ASGI via HTTP-over-gRPC).

Things like linters, tests, type checks, API documentation, authentication and
production deployment were all removed.

I want to keep this demo _really_ simple, so there are many things which I
consider out of scope:

- Adding linters
- Adding TLS support
- Adding a frontend SPA
- Using other databases
- Not hard coding settings
- Publishing Docker images
- Adding OpenAPI schemas
- Running outside of Docker
- Adding cloud deployments
- Porting to other languages
- Tagging versioned releases
- Tidying up the build process
- Adding context files for LLMs
- Publishing to packages to PyPI
- Configuration files for other IDEs
- Building and testing everything in CI
- Significant changes to the tech stack
- Adding other gRPC-JSON transcoders
- Adding authentication and authorisation
- Building and running with Docker clones
- Adding other Python ASGI application servers
- Making the Django application do more things
- Translating documentation to other languages
- Anything which adds _more than one_ of something

There's no need to tell me about these, or to send PRs for them.

Remember: "tech demo"! :)

## Submitting issues

- Issues must be written in English.

- For [security issues, check here](./SECURITY.md).

- If you've found a bug, include a simple way to reproduce it. I don't have
  access to your code base, or your computer.

- [Be mindful of the scope](#scope) – this is a tech demo, it won't do
  everything!

- Don't report that a dependency is out of date. _Write a PR instead!_

- "How do I ..." type questions belong in other forums, such as:

  - [Django community][django]
  - [Envoy community][envoy]
  - [gRPC community][grpc]

- If you have a question about how something in _this_ repository works, please
  use [the discussions tab][discussions].

  The goal is that these will be answered by the documentation.

Issues and questions sent by email will attract my professional consulting
rates. :)

## Submitting PRs

- PR descriptions must be written in English.
- All contributions **must be your own work**.
- Automated PRs and the use of generative AI **is not welcome here**.
- Keep your PR small and simple. Focus on one issue at a time.
- Avoid mixing whitespace and formatting changes with your change.
- If you're fixing a bug and there's no existing issue, include a way to easily
  reproduce it and validate your fix.

Examples of welcomed contributions:

- Fixing [security issues](./SECURITY.md)
- Fixing documentation issues
- Updating outdated dependencies
- Upstreaming custom components (like parts of the build process)
- Fixing issues where I've implemented ASGI incorrectly (even if the issue
  _doesn't_ affect Django)

[discussions]: https://github.com/micolous/grpc-asgi-django-demo/discussions
[django]: https://www.djangoproject.com/community/
[envoy]: https://www.envoyproxy.io/community
[grpc]: https://grpc.io/community/
