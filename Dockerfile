FROM datastewardshipwizard/python-base:3.11-basic AS builder

WORKDIR /app

COPY . /app

RUN python -m pip wheel --no-cache-dir --wheel-dir=/app/wheels -r /app/requirements.txt \
 && python -m pip wheel --no-cache-dir --no-deps --wheel-dir=/app/wheels /app


FROM datastewardshipwizard/python-base:3.11-basic

ENV PATH="/home/user/.local/bin:$PATH"

# Setup non-root user
USER user

# Prepare dirs
WORKDIR /home/user

# Install Python packages
COPY --from=builder --chown=user:user /app/wheels /home/user/wheels
RUN pip install --break-system-packages --user --no-cache --no-index /home/user/wheels/*  \
 && rm -rf /home/user/wheels

# Run
CMD ["uvicorn", "dsw_seed_maker:app", \
        "--proxy-headers", \
        "--forwarded-allow-ips=*", \
        "--host=0.0.0.0", \
        "--port=8000"]
