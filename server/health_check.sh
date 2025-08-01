#!/bin/sh
# Run health checks against the server.
set -e

/app/server/.venv/bin/grpc-health-probe \
    -addr=localhost:8081 || exit 1
