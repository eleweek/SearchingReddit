#!/usr/bin/env bash
# TODO better way of finding gunicorn binary
sudo ./venv/bin/gunicorn web_ui:app -b 0.0.0.0:80 --access-logfile -
