FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    wget \
    libgl1-mesa-glx \
    ffmpeg \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Optional: Install faiss if not in requirements.txt
RUN pip install faiss-cpu

# GCP dataset (replace with your actual bucket URL)
RUN mkdir -p data
RUN wget -O data/food_products.csv "https://storage.googleapis.com/bucket-quickstart_nutriweb-455422/nutriweb_project/cleaned_data.csv"

COPY . .

EXPOSE 8501
