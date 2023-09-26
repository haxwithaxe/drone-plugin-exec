#!/bin/bash

set -e


CONTEXT="$(dirname "$(dirname "$(realpath "$0")")")"

docker build \
	--progress plain \
	-f $CONTEXT/docker/Dockerfile \
	-t drone-plugin-exec:latest \
	$@ \
	$CONTEXT 2>&1
