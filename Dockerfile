ARG DEV=true

# Builer Image
FROM python:3.10-buster as builder

RUN pip install poetry==1.4.2

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app

COPY pyproject.toml poetry.lock ./
RUN touch README.md

RUN if [ "$DEV" = "true" ]; then \
        poetry install --no-root && rm -rf $POETRY_CACHE_DIR; \
    else \
        poetry install --no-root --no-dev && rm -rf $POETRY_CACHE_DIR; \
    fi


# Runtime Image
FROM python:3.10-slim-buster as runtime

COPY Image-ExifTool-12.70.tar.gz ./

RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y \
    git \
    git-lfs \
    libzbar0 \
    make \
    libgdal-dev \
    gcc \
    libffi-dev \
    libssl-dev \
    perl \
    libgl1-mesa-glx \
    libglib2.0-0 && \
    git lfs install && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN tar -xvzf Image-ExifTool-12.70.tar.gz && \
    cd Image-ExifTool-12.70/ && \
    perl Makefile.PL && \
    make test && \
    make install && \
    cd .. && \
    rm -rf Image-ExifTool-12.70/ Image-ExifTool-12.70.tar.gz 

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}
COPY ms_preprocessing ./ms_preprocessing

# CMD ["sh"]
RUN pip install jupyter
ENTRYPOINT ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root"]