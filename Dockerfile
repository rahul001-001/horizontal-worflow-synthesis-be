# syntax=docker/dockerfile:1.7
FROM python:3.11-slim

ARG DEBIAN_FRONTEND=noninteractive

ARG SECRET_KEY=""
ENV SECRET_KEY=${SECRET_KEY}

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    python3-opencv \
    libgomp1 \
 && rm -rf /var/lib/apt/lists/*

ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    YOLO_CONFIG_DIR=/tmp/Ultralytics \
    OPENCV_VIDEOIO_PRIORITY_FFMPEG=1000 \
    OPENCV_FFMPEG_WRITER_OPTIONS="video_codec;libx264|preset;veryfast|crf;23|pix_fmt;yuv420p"

RUN python -m venv "$VIRTUAL_ENV" && pip install --upgrade pip setuptools wheel

WORKDIR /app

COPY requirements.txt .
RUN awk 'BEGIN{IGNORECASE=1} !/^opencv-python(-headless|-contrib)?([=<>!].*)?$/ {print}' \
      requirements.txt > requirements.filtered.txt \
 && pip install --no-cache-dir -r requirements.filtered.txt

RUN python - <<'PY'
import site, pathlib
pth = pathlib.Path(site.getsitepackages()[0]) / "_system_cv2.pth"
pth.write_text("/usr/lib/python3/dist-packages\n/usr/lib/python3.11/dist-packages\n")
print("Linked system cv2 via", pth)
PY

COPY . .

EXPOSE 8000
CMD ["python","manage.py","runserver","0.0.0.0:8000"]













