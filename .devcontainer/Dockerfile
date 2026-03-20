FROM ubuntu:24.04

RUN apt-get update && apt-get install -y \
    curl git unzip xz-utils build-essential python3 python3-pip nodejs npm \
    && rm -rf /var/lib/apt/lists/*

RUN npm install -g pnpm

RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:/root/.elan/bin:${PATH}"

RUN curl https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh -sSf | sh -s -- -y
