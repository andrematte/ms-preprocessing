ARG DEV=true

# Builder Image
FROM python:3.10-buster AS builder

RUN pip install poetry==1.4.2

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=0 \
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
FROM python:3.10-slim-buster AS runtime

COPY Image-ExifTool-12.70.tar.gz ./

RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y \
    git \
    git-lfs \
    libzbar0 \
    make \
    g++ \
    build-essential \
    libgdal-dev \
    gdal-bin \
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

WORKDIR /app

# Copy dependencies from builder stage
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

RUN pip install setuptools==58.0.0
RUN pip install gdal==2.4.0

# Copy the application code
# COPY ms_preprocessing ./ms_preprocessing

# Install Jupyter globally
RUN pip install jupyter
ENTRYPOINT ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root"]
# ENTRYPOINT ["sh"]