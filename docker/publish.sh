#!/bin/bash
# Publish the latest build as the current git tag or the value of the
#   environment variable $TAG

set -e

DEST_IMAGE="haxwithaxe/drone-plugin-exec"
SRC_IMAGE="drone-plugin-exec"
TAG=${1:-${TAG:-$(git tag --points-at HEAD)}}

if [[ -z $TAG ]]; then
	echo No tag set. Either set the \$TAG environment variable or add a tag to HEAD. 1>&2
	exit 1
fi

if [[ "$TAG" != *"-"* ]]; then
	echo Tagging ${SRC_IMAGE}:latest as ${DEST_IMAGE}:latest
	docker image tag ${SRC_IMAGE}:latest ${DEST_IMAGE}:latest
fi
echo Tagging ${SRC_IMAGE}:latest as ${DEST_IMAGE}:$TAG
docker image tag ${SRC_IMAGE}:latest ${DEST_IMAGE}:$TAG
if [[ "$TAG" != *"-"* ]]; then
	echo Pushing ${DEST_IMAGE}:latest
	docker image push ${DEST_IMAGE}:latest
fi
echo Pushing ${DEST_IMAGE}:$TAG
docker image push ${DEST_IMAGE}:$TAG
