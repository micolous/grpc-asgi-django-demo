#!/bin/bash
# Generate a `.env` file with default options.
#
# Requires `openssl` in your PATH.
set -e

if ! which openssl > /dev/null
then
    echo 'Error: this script requires `openssl` in your PATH.'
    exit 1
fi

if [ ! -e "docker-compose.yml" ]
then
    echo 'Error: this script must be run from the root of the repository.'
    exit 1
fi

umask 077

if [ -e ".env" ]
then
    echo 'Loading existing settings from .env'
    source .env
else
    echo 'Creating new .env file'
    touch .env
fi

# Populate any missing settings
if [ -z "${SECRET_KEY}" ]
then
    SECRET_KEY="$(openssl rand -base64 32 | tr /+ _-)"
    echo "SECRET_KEY=\"${SECRET_KEY}\"" >> .env
fi
