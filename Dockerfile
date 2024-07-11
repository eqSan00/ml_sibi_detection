FROM python:3.11.9-slim-bullseye AS builder
WORKDIR /app

RUN --mount=target=/var/lib/apt/lists,type=cache,sharing=locked \
    --mount=target=/var/cache/apt,type=cache,sharing=locked \
    rm -f /etc/apt/apt.conf.d/docker-clean \
    && apt-get update \
    && apt-get -y --no-install-recommends install \
    ffmpeg libsm6 libxext6 -y

RUN python3 -m venv venv
ENV VIRTUAL_ENV=/app/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY requirements.txt requirements.txt
RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements.txt


FROM python:3.11.9-slim-bullseye AS runner
WORKDIR /app
COPY --from=builder /app/venv venv
COPY static/ temp/ templates/ app.py model.h5 requirements.txt ./

ENV VIRTUAL_ENV=/app/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV FLASK_APP=app/app.py

EXPOSE 8000
CMD ["gunicorn", "--bind" , ":8000", "app:app"]