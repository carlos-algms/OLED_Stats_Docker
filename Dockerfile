FROM python:alpine as builder

ENV VIRTUAL_ENV=/opt/venv

RUN python -m venv $VIRTUAL_ENV

ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN apk add --no-cache \
  i2c-tools \
  libgpiod-dev \
  gcc \
  libc-dev \
  linux-headers \
  py3-pillow \
  zlib-dev \
  jpeg-dev \
  freetype-dev

RUN pip3 install --upgrade \
  RPI.GPIO \
  adafruit-circuitpython-ssd1306 \
  Pillow

FROM python:alpine as runner

COPY --from=builder /opt/venv /opt/venv

RUN apk add --no-cache \
  procps

ENV VIRTUAL_ENV=/opt/venv

RUN python -m venv $VIRTUAL_ENV

ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /opt/stats

COPY PixelOperator.ttf lineawesome-webfont.ttf stats.py /opt/stats/

ENTRYPOINT [ "python", "stats.py" ]
