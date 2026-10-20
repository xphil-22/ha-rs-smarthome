# RS SmartHome for Home Assistant

Unofficial Home Assistant integration for Wi-Fi smart plugs that are controlled with the
**RS-SmartHome** app (`com.risingsun.smarthome`, RisingSun). These plugs are sold under
several brand names, e.g. **Expertan** and **LUNVON**.

[![hacs][hacs-badge]][hacs-url]

> [!WARNING]
> This is a reverse-engineered, unofficial integration. It talks to the vendor's cloud
> exactly like the Android app does. If the vendor changes the API or the encryption key
> in an app update, it may stop working.

## Features

- Setup through the UI (Settings → Devices & services), no YAML
- One switch entity (device class `outlet`) per plug, new plugs are added automatically
- Plug shows as unavailable when it is offline in the cloud
- Automatic re-login when the session expires, re-auth dialog when the password changes
- Polls the cloud every 30 seconds (`cloud_polling`)

Tested with an Expertan Wi-Fi plug (device type 4) and RS-SmartHome app 5.7 on
Home Assistant 2026.9.

## Installation

### HACS (custom repository)

1. HACS → ⋮ → **Custom repositories**
2. Repository: `https://github.com/xphil-22/ha-rs-smarthome`, category: **Integration**
3. Install **RS SmartHome** and restart Home Assistant

### Manual

Copy `custom_components/rs_smarthome` into `<config>/custom_components/` and restart
Home Assistant.

## Configuration

1. **Settings → Devices & services → Add integration → RS SmartHome**
2. Log in with the e-mail address and password of your RS-SmartHome app account

The plugs must already be paired with the RS-SmartHome app. The app can keep being used
in parallel.

## Troubleshooting

| Error | Meaning |
|---|---|
| `invalid_auth` | Wrong e-mail or password |
| `cannot_connect` | The RS-SmartHome cloud is not reachable |

Debug logging:

```yaml
logger:
  logs:
    custom_components.rs_smarthome: debug
```

For testing the API outside of Home Assistant there is a small CLI in
[`tools/rs_cli.py`](tools/rs_cli.py).

## How it works

The protocol is documented in [docs/PROTOCOL.md](docs/PROTOCOL.md). In short: the app posts
`{"code": <api code>, "value": <AES-128-CBC encrypted JSON>}` to
`https://service.rs-smarthome.com:8433/AppService.asmx/Execute`. The static key and IV
were taken from the JavaScript bundle of the Android app (it is a Capacitor/Ionic app).

Thanks to the people in the
[Home Assistant community thread](https://community.home-assistant.io/t/integration-for-expertan-rs-smart-home/544942)
who documented the API codes.

---

## Deutsch (Kurzfassung)

Inoffizielle Home-Assistant-Integration für WLAN-Steckdosen, die mit der App
**RS-SmartHome** gesteuert werden (u. a. **Expertan**, **LUNVON**).

1. In HACS unter **Benutzerdefinierte Repositories** `https://github.com/xphil-22/ha-rs-smarthome`
   als **Integration** hinzufügen, installieren und HA neu starten
   (oder `custom_components/rs_smarthome` manuell nach `<config>/custom_components/` kopieren).
2. **Einstellungen → Geräte & Dienste → Integration hinzufügen → RS SmartHome**
3. Mit E-Mail und Passwort des RS-SmartHome-App-Kontos anmelden.

Jede Steckdose erscheint als Schalter. Die Steuerung läuft über die Cloud des Herstellers;
ändert dieser die API, kann die Integration ausfallen.

## License

MIT, see [LICENSE](LICENSE). Not affiliated with RisingSun, Expertan or LUNVON.

[hacs-badge]: https://img.shields.io/badge/HACS-Custom-41BDF5.svg
[hacs-url]: https://hacs.xyz/docs/faq/custom_repositories/
