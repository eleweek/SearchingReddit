#!/usr/bin/env bash
# TODO better way of finding gunicorn binary
./venv/bin/gunicorn -w 3 web_ui:app -b 0.0.0.0:80
