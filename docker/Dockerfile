FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV GITHUB_WORKSPACE=/workspace
WORKDIR /workspace

# Basic CI runner setup
RUN apt-get update && apt-get install -y sudo git curl ca-certificates

# Create GitHub-like user
RUN useradd -ms /bin/bash runner && \
    echo "runner ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers
USER runner

# 1. Copy only the tools folder + build_config first (layer cache important)
COPY tools tools
COPY build_config build_config

# 2. Install system dependencies (from your script)
RUN ./tools/linux_1_get-dependencies

# 3. Build openscenegraph IF NOT CACHED
RUN if [ ! -d /tmp/OpenSceneGraph-install ]; then \
    ./tools/unix_2a_build-osg ; \
    fi

# 4. Build simbody IF NOT CACHED
RUN if [ ! -d /tmp/simbody-install ]; then \
    ./tools/unix_2b_build-simbody ; \
    fi

# 5. Build opensim3 IF NOT CACHED
RUN if [ ! -d /tmp/opensim3-install ]; then \
    ./tools/unix_2c_build-opensim3 ; \
    fi

# 6. Copy rest of repo after dependencies (maximizes cache)
COPY . .

# Provide run command
COPY docker/run.sh /usr/local/bin/run
RUN chmod +x /usr/local/bin/run
