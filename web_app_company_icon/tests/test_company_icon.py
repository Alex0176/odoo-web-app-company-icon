# Copyright 2026 Biricon IT Services GmbH
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
import base64
import io

from PIL import Image

from odoo import Command
from odoo.tests import HttpCase, tagged


def _png(width, height, color):
    out = io.BytesIO()
    Image.new("RGB", (width, height), color).save(out, format="PNG")
    return base64.b64encode(out.getvalue())


@tagged("post_install", "-at_install")
class TestCompanyIcon(HttpCase):
    def setUp(self):
        super().setUp()
        self.company = self.env.company
        self.website = self.env["website"].sudo().get_current_website() if "website" in self.env else None
        if self.website:
            self.website.favicon = False

    def test_default_logo_keeps_the_odoo_icon(self):
        self.company.logo = self.company._get_logo()
        self.company.primary_color = False
        self.assertTrue(self.company.uses_default_logo)
        manifest = self.url_open("/web/manifest.webmanifest").json()
        self.assertNotEqual(manifest["theme_color"], "#123456")
        self.assertTrue(all(icon["src"].startswith("/web/static/img/") for icon in manifest["icons"]))
        res = self.url_open("/web/company_icon/192.png", allow_redirects=False)
        self.assertEqual(res.status_code, 302)
        self.assertTrue(res.headers["Location"].endswith("/web/static/img/odoo-icon-192x192.png"))

    def test_wide_company_logo_becomes_a_white_square(self):
        self.company.logo = _png(400, 100, (200, 0, 0))
        manifest = self.url_open("/web/manifest.webmanifest").json()
        self.assertEqual([i["src"] for i in manifest["icons"]],
                         ["/web/company_icon/192.png", "/web/company_icon/512.png"])
        res = self.url_open("/web/company_icon/192.png")
        self.assertEqual(res.headers["Content-Type"], "image/png")
        img = Image.open(io.BytesIO(res.content))
        self.assertEqual(img.size, (192, 192))
        self.assertEqual(img.getpixel((2, 2)), (255, 255, 255), "white margin")
        self.assertEqual(img.getpixel((96, 96)), (200, 0, 0), "logo in the middle")
        self.assertEqual(img.getpixel((96, 20)), (255, 255, 255), "wide logo does not fill the height")

    def test_website_favicon_wins_over_logo(self):
        if not self.website:
            self.skipTest("website not installed")
        self.company.logo = _png(400, 100, (200, 0, 0))
        self.website.favicon = _png(64, 64, (0, 0, 200))
        res = self.url_open("/web/company_icon/512.png")
        img = Image.open(io.BytesIO(res.content))
        self.assertEqual(img.size, (512, 512))
        self.assertEqual(img.getpixel((256, 256)), (0, 0, 200))

    def test_only_known_sizes(self):
        self.assertEqual(self.url_open("/web/company_icon/77.png", allow_redirects=False).status_code, 404)

    def test_backend_page_points_to_the_icons(self):
        self.company.logo = _png(400, 100, (200, 0, 0))
        self.env["res.users"].create({
            "name": "Icon Test", "login": "icon_test_user", "password": "icon-test-Pass-42",
            "group_ids": [Command.set([self.env.ref("base.group_user").id])],
        })
        self.authenticate("icon_test_user", "icon-test-Pass-42")
        html = self.url_open("/odoo").text
        self.assertIn('rel="apple-touch-icon" href="/web/company_icon/180.png"', html)
        self.assertIn('href="/web/company_icon/32.png"', html)

    def test_company_color_is_the_app_color(self):
        self.company.primary_color = "#123456"
        manifest = self.url_open("/web/manifest.webmanifest").json()
        self.assertEqual(manifest["theme_color"], "#123456")
        self.assertEqual(manifest["background_color"], "#123456")
        self.env["res.users"].create({
            "name": "Color Test", "login": "color_test_user", "password": "color-test-Pass-42",
            "group_ids": [Command.set([self.env.ref("base.group_user").id])],
        })
        self.authenticate("color_test_user", "color-test-Pass-42")
        self.assertIn('<meta name="theme-color" content="#123456"', self.url_open("/odoo").text)
