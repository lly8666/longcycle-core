FROM python:3.12-slim AS builder

WORKDIR /build
COPY pyproject.toml README.md ./
COPY migrations ./migrations
COPY src ./src
RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip wheel --no-cache-dir --wheel-dir /wheels ".[postgres,s3]"

FROM python:3.12-slim AS runtime

RUN groupadd --system longcycle \
    && useradd --system --gid longcycle --create-home longcycle
COPY --from=builder /wheels /wheels
RUN python -m pip install --no-cache-dir --no-index --find-links=/wheels longcycle-core \
    && rm -rf /wheels

USER longcycle
WORKDIR /home/longcycle
ENTRYPOINT ["longcycle"]
CMD ["doctor"]
