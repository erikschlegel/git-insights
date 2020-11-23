# Find the Dockerfile for mcr.microsoft.com/azure-functions/python:3.0-python3.8-core-tools at this URL
# https://github.com/Azure/azure-functions-docker/blob/master/host/3.0/buster/amd64/python/python38/python38-core-tools.Dockerfile

ARG BASE_IMAGE_TAG=3.0-python3.8-core-tools
FROM mcr.microsoft.com/azure-functions/python:$BASE_IMAGE_TAG

ARG TERRAFORM_VERSION=0.13.4
RUN wget -O /tmp/terraform.zip \
    https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip
RUN unzip -d /usr/local/bin/ /tmp/terraform.zip && rm /tmp/terraform.zip

RUN python -m venv .venv && . .venv/bin/activate
