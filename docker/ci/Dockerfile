# Build separately from application CI. The base is the maintained internal
# Python/Docker/scanner tool image; source inventory is recorded in docs/ci.md.
FROM forgejo.moseisley.es/wind/readradar-ci@sha256:865eef6e4fdba8c3b26cf5d102ba553b3f29a8d59eb04d36cc26c16176936d3b

USER root
ENV PATH="/opt/readingview-node/bin:$PATH"
RUN mkdir -p /opt/readingview-node /opt/readingview-pnpm /tmp/readingview-ci-tools \
    && curl --fail --show-error --location --retry 3 \
      https://nodejs.org/dist/v24.19.0/node-v24.19.0-linux-x64.tar.xz \
      -o /tmp/readingview-ci-tools/node.tar.xz \
    && echo '14b342e71204f811bde6153be8e04b62aef63c236fef92b55f9c83154b409647  /tmp/readingview-ci-tools/node.tar.xz' | sha256sum --check \
    && tar -xJf /tmp/readingview-ci-tools/node.tar.xz --strip-components=1 -C /opt/readingview-node \
    && curl --fail --show-error --location --retry 3 \
      https://registry.npmjs.org/pnpm/-/pnpm-10.32.1.tgz \
      -o /tmp/readingview-ci-tools/pnpm.tgz \
    && echo 'a706938f0e89ac1456b6563eab4edf1d1faf3368d1191fc5c59790e96dc918e4456ab2e67d613de1043d2e8c81f87303e6b40d4ffeca9df15ef1ad567348f2be  /tmp/readingview-ci-tools/pnpm.tgz' | sha512sum --check \
    && tar -xzf /tmp/readingview-ci-tools/pnpm.tgz --strip-components=1 -C /opt/readingview-pnpm \
    && ln -s /opt/readingview-pnpm/bin/pnpm.cjs /opt/readingview-node/bin/pnpm \
    && ln -s /opt/readingview-pnpm/bin/pnpx.cjs /opt/readingview-node/bin/pnpx \
    && rm -rf /tmp/readingview-ci-tools

RUN pip install --no-cache-dir --no-deps uv==0.13.5

RUN node --version && pnpm --version && uv --version \
    && test "$(node --version)" = v24.19.0 \
    && test "$(pnpm --version)" = 10.32.1 \
    && test "$(uv --version | cut -d ' ' -f 2)" = 0.13.5 \
    && python3 --version && git --version && docker --version \
    && docker buildx version && gitleaks version && trivy --version && jq --version

ENV UV_PYTHON_DOWNLOADS=never
WORKDIR /workspace
