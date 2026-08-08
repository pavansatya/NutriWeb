FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1

# Only build-essential is needed now. The previous image also pulled
# libgl1-mesa-glx and ffmpeg for torch/faiss, which are no longer dependencies.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY . .

# The catalog is NOT baked into the image. Either build it locally with
#   python pipeline/01_download.py && python pipeline/02_curate.py && python pipeline/03_score.py
# or set NUTRIWEB_CATALOG_REPO to a Hugging Face dataset repo and it will be
# fetched at startup. The old image downloaded a static cleaned_data.csv from a
# GCS bucket, which is the stale data source this rebuild removed.

EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
