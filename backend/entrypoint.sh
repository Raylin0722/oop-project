#!/bin/sh

SECRET_FILE="/app/.secret_key"

if [ ! -f "$SECRET_FILE" ]; then
    python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())' > "$SECRET_FILE"
fi
export DJANGO_SECRET_KEY=$(cat "$SECRET_FILE")
exec "$@"