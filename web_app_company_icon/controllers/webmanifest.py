# Copyright 2026 Biricon IT Services GmbH
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
import base64
import hashlib
import io

from PIL import Image

from odoo import http
from odoo.addons.web.controllers import webmanifest
from odoo.http import request

# size -> stock Odoo file that is served while neither a favicon nor a company logo exists
STOCK_ICONS = {
    32: "/web/static/img/favicon.ico",
    180: "/web/static/img/odoo-icon-ios.png",
    192: "/web/static/img/odoo-icon-192x192.png",
    512: "/web/static/img/odoo-icon-512x512.png",
}
PADDING = 0.08  # share of the edge that stays white around the image


def square_png(data, size):
    """Image bytes -> PNG bytes of ``size`` x ``size``: the image centered on white with a small margin."""
    img = Image.open(io.BytesIO(data))
    img.load()
    img = img.convert("RGBA")
    inner = int(size * (1 - 2 * PADDING))
    img.thumbnail((inner, inner), Image.LANCZOS)
    canvas = Image.new("RGBA", (size, size), (255, 255, 255, 255))
    canvas.alpha_composite(img, ((size - img.width) // 2, (size - img.height) // 2))
    out = io.BytesIO()
    canvas.convert("RGB").save(out, format="PNG", optimize=True)
    return out.getvalue()


class WebManifest(webmanifest.WebManifest):
    def _get_app_icon_source(self):
        """Raw bytes of the image to use: favicon of the current website, else the company logo; None for the
        Odoo default (a company that still has the default logo)."""
        favicon = None
        if "website" in request.env:  # request.website is not set on backend routes
            favicon = request.env["website"].sudo().get_current_website().favicon
        if favicon:
            return base64.b64decode(favicon)
        company = request.env.company.sudo()
        if company.logo and not company.uses_default_logo:
            return base64.b64decode(company.logo)
        return None

    def _get_webmanifest(self):
        manifest = super()._get_webmanifest()
        color = request.env.company.sudo().primary_color
        if color:
            manifest["theme_color"] = manifest["background_color"] = color
        source = self._get_app_icon_source()
        if source:
            # the version makes the manifest change whenever the image changes, which is what makes
            # browsers update an installed web app (the same way as for a changed app name)
            version = hashlib.sha1(source).hexdigest()[:10]
            manifest["icons"] = [{
                "src": f"/web/company_icon/{size}.png?v={version}",
                "sizes": f"{size}x{size}",
                "type": "image/png",
                "purpose": "any",
            } for size in (192, 512)]
        return manifest

    @http.route("/web/manifest.webmanifest", type="http", auth="public", methods=["GET"], readonly=True)
    def webmanifest(self):
        response = super().webmanifest()
        response.headers["Cache-Control"] = "no-cache"  # always revalidate: changes reach installed apps at once
        return response

    @http.route("/odoo/offline", type="http", auth="public", methods=["GET"], readonly=True)
    def offline(self):
        source = self._get_app_icon_source()
        png = None
        if source:
            try:
                png = square_png(source, 192)
            except Exception:  # noqa: BLE001
                png = None
        if not png:
            return super().offline()
        return request.render("web.webclient_offline", {"odoo_icon": base64.b64encode(png)})

    @http.route("/web/company_icon/<int:size>.png", type="http", auth="public", methods=["GET"], readonly=True)
    def company_icon(self, size, **kwargs):
        if size not in STOCK_ICONS:
            return request.not_found()
        source = self._get_app_icon_source()
        png = None
        if source:
            try:
                png = square_png(source, size)
            except Exception:  # noqa: BLE001 - broken or unsupported image: stock icon
                png = None
        if not png:
            return request.redirect(STOCK_ICONS[size], code=302, local=True)
        return request.make_response(png, [
            ("Content-Type", "image/png"),
            ("Cache-Control", "public, max-age=3600"),
        ])
