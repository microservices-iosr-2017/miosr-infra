#!/usr/bin/env bash

# Based on https://github.com/kubernetes/kubernetes/issues/27081

if [ -z "$1" ]; then
    echo "You must pass service name as first argument"
    exit 1
else
    SRV_NAME="$1"
fi

kubectl patch deployment "$SRV_NAME"-deployment -p \
  "{\"spec\":{\"template\":{\"metadata\":{\"annotations\":{\"date\":\"`date +'%s'`\"}}}}}"