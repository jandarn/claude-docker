FROM ubuntu:24.04

ARG DEBIAN_FRONTEND=noninteractive
ARG NODE_VERSION=22.22.2
ARG UID=1000
ARG GID=1000
ARG USERNAME

# Base OS packages and quality-of-life CLI tools for coding sessions.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash-completion \
        ca-certificates \
        curl \
        dnsutils \
        fd-find \
        gcc \
        g++ \
        git \
        git-lfs \
        gnupg \
        iputils-ping \
        jq \
        less \
        libc6-dev \
        make \
        nano \
        netcat-openbsd \
        openssh-client \
        procps \
        python3 \
        python3-pip \
        ripgrep \
        sudo \
        tini \
        tree \
        unzip \
        vim \
        xz-utils \
        zip \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js directly from official binaries to avoid distro npm packaging issues.
RUN set -eux; \
    arch="$(dpkg --print-architecture)"; \
    case "$arch" in \
      amd64) node_arch="x64" ;; \
      arm64) node_arch="arm64" ;; \
      *) echo "Unsupported architecture: $arch"; exit 1 ;; \
    esac; \
    curl -fsSLO "https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-linux-${node_arch}.tar.xz"; \
    tar -xJf "node-v${NODE_VERSION}-linux-${node_arch}.tar.xz" -C /usr/local --strip-components=1 --no-same-owner; \
    rm -f "node-v${NODE_VERSION}-linux-${node_arch}.tar.xz"; \
    node --version; \
    npm --version

# Install Claude using the official setup script; fallback to npm package if needed.
RUN set -eux; \
        curl -fsSL https://claude.ai/install.sh | bash || true; \
    command -v claude

# Create a non-root user that mirrors host UID/GID when provided.
RUN set -eux; \
    : "${USERNAME:?USERNAME build arg must be set (from .env)}"; \
    if getent group "${GID}" >/dev/null; then \
        group_name="$(getent group "${GID}" | cut -d: -f1)"; \
    else \
        groupadd --gid "${GID}" "${USERNAME}"; \
        group_name="${USERNAME}"; \
    fi; \
    if id -u "${UID}" >/dev/null 2>&1; then \
        user_name="$(getent passwd "${UID}" | cut -d: -f1)"; \
        usermod -d "/home/${USERNAME}" -m "${user_name}" || true; \
        usermod -l "${USERNAME}" "${user_name}" || true; \
        usermod -g "${group_name}" "${USERNAME}" || true; \
    else \
        useradd --uid "${UID}" --gid "${group_name}" --create-home --shell /bin/bash "${USERNAME}"; \
    fi; \
    mkdir -p "/home/${USERNAME}/.config/claude" "/home/${USERNAME}/.claude/debug"; \
    chown -R "${UID}:${GID}" "/home/${USERNAME}"

ENV HOME=/home/${USERNAME}
ENV WORKSPACE=/home/${USERNAME}
ENV TERM=xterm-256color

WORKDIR /home/${USERNAME}
USER ${USERNAME}

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["/bin/bash"]
