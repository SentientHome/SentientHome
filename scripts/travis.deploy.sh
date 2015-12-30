#!/bin/bash
set -ev
docker login -e="$DOCKER_EMAIL" -u="$DOCKER_USERNAME" -p="$DOCKER_PASSWORD"
docker push "$DOCKER_USERNAME"/sentienthome
