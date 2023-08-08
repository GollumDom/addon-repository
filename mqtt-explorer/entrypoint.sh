#!/bin/sh
[ -e "/data/settings.json" ] && echo '{"ConnectionManager_connections":{"mqtt.eclipse.org":{"configVersion":1,"certValidation":true,"clientId":"mqtt-explorer-ce4f0fc6","id":"mqtt.eclipse.org","name":"homeassitant","encryption":false,"subscriptions":[{"topic":"#","qos":0},{"topic":"$SYS/#","qos":0}],"type":"mqtt","host":"core-mosquitto.local.hass.io","port":1883,"protocol":"mqtt","changeSet":{"password":""},"username":"","password":""}}}' > /data/settings.json

"$@"