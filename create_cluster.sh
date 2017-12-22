#!/usr/bin/env bash

gcloud container clusters create miosr \
    --zone=europe-west3-a \
    --project=arched-shuttle-189207 \
    --num-nodes=3 \
    --machine-type=g1-small
