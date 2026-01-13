ARG BUILD_FROM
FROM $BUILD_FROM

ENV LANG C.UTF-8

# Install Python and required packages
RUN apk add --no-cache \
    python3 \
    py3-pip \
    tzdata \
    && pip3 install --no-cache-dir \
    aiohttp \
    paho-mqtt \
    python-dateutil \
    pytz

# Copy application files
COPY run.sh /
COPY meteoblue.py /
RUN chmod a+x /run.sh

CMD [ "/run.sh" ]