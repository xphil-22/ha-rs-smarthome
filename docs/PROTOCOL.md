# RS-SmartHome cloud protocol

Reverse-engineered from the Android app `com.risingsun.smarthome` version 5.7.
The app is a Capacitor/Ionic app, so all logic lives in
`assets/public/main.*.js` inside the APK (decompile with `jadx` or just unzip).

## Endpoint

| Region | URL |
|---|---|
| DE-1 (default) | `https://service.rs-smarthome.com:8433/AppService.asmx/Execute` |
| US-1 | `https://us1.service.rs-smarthome.com:8433/AppService.asmx/Execute` |

All requests are `POST` with `Content-Type: application/json`.

## Envelope

Request:

```json
{"code": 21001, "value": "<base64 ciphertext>"}
```

Response:

```json
{"d": "<base64 ciphertext>"}
```

`value` and `d` are JSON documents encrypted with **AES-128-CBC, PKCS7 padding**, base64
encoded. Key and IV are static strings in the app (`this.crypt` in `main.*.js`):

```
key = "YAOb+cjChf34qxWZ"
iv  = "VG9x1XfbCQZgDFf1"
```

(Both are used as UTF-8 bytes.) The decrypted response always has the form
`{"Result": <int>, "Data": <any>}`. `Result == 1` means success.

## Login – code `21001`

```json
{
  "loginname": "user@example.com",
  "password": "<plain password>",
  "type": 2001,
  "token": "",
  "CustomerID": 1,
  "Language": 49,
  "AppVersion": "5.7"
}
```

`type` is `2001` on Android and `1001` on iOS. `Language` is a phone country code
(44 en, 33 fr, 49 de, 39 it, 34 es, 86 zh). On success `Data` contains the user object
(`ID`, `AccountID`, `LoginName`, …). The server also sets a session cookie.

## Device list – code `21101`

Value: the `AccountID` from the login (a bare JSON value, not an object).

`Data` is a list of devices:

| Field | Meaning |
|---|---|
| `ID` | Device id |
| `Mac` | MAC, e.g. `00-04-A3-xx-xx-xx` |
| `Name` | Name set in the app |
| `Type` | Device type (a plain Wi-Fi plug reports `4`; types 7/8 need code `21401`) |
| `PowerState` | `1` on, `2` off |
| `IsOnline` | `true` / `false` |
| `Status` | Device status |

## Switch – code `21190`

```json
{"id": 123456, "mac": "00-04-A3-xx-xx-xx", "cmd": 1}
```

`cmd`: `1` on, `2` off. Device types 7 and 8 use code `21401` with an additional
`"index": 0`. A successful response looks like `{"Result": 1, "Data": [1, …]}`.

## Expired session

If a response has `Result == -100`, the app logs in again and repeats the request with the
**negated** code and a wrapped value:

```json
{"code": -21101, "value": AES({"token": "<JSON string of login Data>", "data": "<JSON string of original value>"})}
```

## Other codes seen in the app

`20100`, `21191`, `21193`, `21900`, `23010`, `24002`, `24003`, `24005` (gateways, timers,
scenes, …) – not implemented here. The app also contains MQTT-over-WebSocket settings
(`service.rs-smarthome.com:8083/mqtt`), but MQTT is disabled in version 5.7.
