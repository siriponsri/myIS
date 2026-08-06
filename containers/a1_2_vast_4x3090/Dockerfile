# syntax=docker/dockerfile:1.7

ARG BASE_IMAGE
FROM ${BASE_IMAGE}

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1 \
    MYIS_REMOTE_MODE=a1_2_preflight_only

WORKDIR /opt/myis

# The Owner-built context supplies an offline wheelhouse and a complete
# SHA256SUMS file. The local coordinator verifies both before upload.
COPY runtime/requirements.v2.txt /opt/myis/runtime/requirements.v2.txt
COPY runtime/wheelhouse/ /opt/myis/runtime/wheelhouse/
RUN cd /opt/myis/runtime/wheelhouse \
    && sha256sum --check SHA256SUMS \
    && python -m pip install --no-index --find-links=. -r ../requirements.v2.txt

RUN python -c "import torch; assert torch.__version__ == '2.6.0+cu118'; assert torch.version.cuda == '11.8'"

CMD ["python", "--version"]
