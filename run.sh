#!/usr/bin/with-contenv bashio

# shellcheck disable=SC1091

bashio::log.info "Starting Meteoblue Weather Add-on..."

# Get configuration
CONFIG_PATH=/data/options.json
API_KEY=$(bashio::config 'api_key')

if [ -z "$API_KEY" ]; then
    bashio::log.error "API key not configured!"
    bashio::exit.nok
fi

# Get Home Assistant API token
HASSIO_TOKEN="${SUPERVISOR_TOKEN}"
if [ -z "$HASSIO_TOKEN" ]; then
    bashio::log.error "Cannot access Home Assistant API"
    bashio::exit.nok
fi

bashio::log.info "Configuration loaded successfully"
bashio::log.info "Starting weather service..."

# Run the Python script
python3 /meteoblue.py