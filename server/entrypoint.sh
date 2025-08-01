#!/bin/sh
set -eux

# Create / update database
gadd-manage migrate

exec grpc-asgi-django-demo-server
