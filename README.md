# Odoo Web App Company Icon

Odoo 19.0 addon by **Biricon IT Services GmbH** (LGPL-3).

| Module | Description |
|---|---|
| [web_app_company_icon](web_app_company_icon/) | Uses the favicon of the website, or else the company logo, as icon of the installable Odoo web app (home screen, taskbar) and as browser tab icon of the backend, and the primary color of the company as app color, instead of Odoo's icon and purple. |

## What it does

In Odoo 19 only the *name* of the web app can be changed (*Settings > General Settings > Web App Name*); the icons are
fixed files of the `web` module. This module serves the icons from your own images:

- the web app manifest (`/web/manifest.webmanifest`) lists `/web/company_icon/192.png` and `/512.png`,
- the iOS touch icon and the browser tab icon of the backend point to `/web/company_icon/180.png` and `/32.png`.

Source of the image: the favicon of the website that answers the request, otherwise the company logo. The image is
centered on a white square with a small margin, so wide logos work. As long as neither a favicon nor a custom company
logo exists, the Odoo icons stay. Uninstalling the module restores the Odoo icons.

The color of the app (manifest `theme_color` / `background_color` and the `theme-color` meta tag of the backend) is the
primary color of the company, if one is set.

Installed web apps update like after a changed app name: the icon URLs in the manifest carry a version of the image,
so the manifest changes whenever the logo, favicon or company color changes, and it is never cached. Browsers check it
when the app is started (Chrome about once a day, Android updates the app silently). iOS keeps the icon of the day of
installation. The module contains Python code: restart Odoo after installing it.

## Requirements

- Odoo 19.0 (standard module `web`; `website` is used if installed)

## Installation

1. Put `web_app_company_icon` into the addons path.
2. Update the apps list, install *Web App Company Icon* and restart Odoo.

## Tests

```
odoo-bin -d <database> -i web_app_company_icon --test-tags /web_app_company_icon --stop-after-init
```

## License

LGPL-3.0 or later, see [LICENSE](LICENSE).
