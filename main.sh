#!/usr/bin/env bash

export $(egrep -v '^#' .env | xargs)

if [[ -z "${ROOT_PATH}" ]]; then
    uvicorn app.server:APP --host 0.0.0.0 --port $PORT
else
    uvicorn app.server:APP --host 0.0.0.0 --port $PORT --root-path $ROOT_PATH
fi
