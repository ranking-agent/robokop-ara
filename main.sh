#!/usr/bin/env bash
export $(egrep -v '^#' .env | xargs)
uvicorn app.server:APP --host 0.0.0.0 --port $PORT
