"""Constants for RS SmartHome."""

from datetime import timedelta

DOMAIN = "rs_smarthome"
MANUFACTURER = "RisingSun / RS SmartHome"

API_URL = "https://service.rs-smarthome.com:8433/AppService.asmx/Execute"
# Taken from the RS-SmartHome Android app 5.7 (assets/public/main.*.js)
AES_KEY = b"YAOb+cjChf34qxWZ"
AES_IV = b"VG9x1XfbCQZgDFf1"
APP_VERSION = "5.7"
CUSTOMER_ID = 1
LANGUAGE_DE = 49

CODE_LOGIN = 21001
CODE_DEVICES = 21101
CODE_SWITCH = 21190
CODE_SWITCH_MULTI = 21401  # device types 7 and 8
RESULT_OK = 1
RESULT_TOKEN_EXPIRED = -100

CMD_ON = 1
CMD_OFF = 2

SCAN_INTERVAL = timedelta(seconds=30)
