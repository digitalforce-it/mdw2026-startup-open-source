import os

from markupsafe import Markup, escape

from odoo import http
from odoo.http import request

STATIC = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")

# Valori di ?utm_source= nel link (es. dalla bio di Instagram) -> nome della fonte in Odoo
SOURCES = {"instagram": "Instagram", "google": "Google Ads", "linkedin": "LinkedIn", "qr": "Volantino QR"}


class PausaLandingPage(http.Controller):

    @http.route("/pausa", type="http", auth="public", methods=["GET"], csrf=False, sitemap=False)
    def pausa_page(self, **kw):
        return self._serve("pausa.html")

    @http.route("/pausa/social", type="http", auth="public", methods=["GET"], csrf=False, sitemap=False)
    def pausa_social(self, **kw):
        return self._serve("pausa_social.html")

    @staticmethod
    def _serve(filename):
        with open(os.path.join(STATIC, filename), encoding="utf-8") as f:
            html = f.read()
        return request.make_response(html, headers=[("Content-Type", "text/html; charset=utf-8")])

    @http.route("/pausa/richiesta", type="http", auth="public", methods=["POST"], csrf=False, sitemap=False)
    def pausa_lead(self, **post):
        # Campo nascosto anti-spam: le persone non lo vedono, i bot lo compilano
        if post.get("website_url"):
            return request.redirect("/pausa?grazie=1#prova")

        name = (post.get("contact_name") or "").strip()[:100]
        email = (post.get("email") or "").strip()[:120]
        if not name or "@" not in email:
            return request.redirect("/pausa?errore=1#prova")

        company = (post.get("company") or "").strip()[:120]
        phone = (post.get("phone") or "").strip()[:40]
        size = (post.get("team_size") or "").strip()[:40]
        notes = (post.get("notes") or "").strip()[:2000]

        env = request.env
        source_key = (post.get("utm_source") or "").strip().lower()[:30]
        source_name = SOURCES.get(source_key, source_key.capitalize() if source_key else "Sito web")
        source = self._utm(env["utm.source"].sudo(), source_name)
        medium = self._utm(env["utm.medium"].sudo(), "Website")
        teams = env["crm.team"].sudo()
        team = teams.search([("name", "=", "Pausa")], limit=1) or teams.search([], limit=1)

        description = Markup("<p>Persone in ufficio: %s</p><p>%s</p>") % (
            size or "non indicato",
            Markup("<br/>").join(escape(line) for line in notes.splitlines()) if notes else "",
        )
        env["crm.lead"].sudo().create({
            "type": "lead",
            "name": f"Settimana di prova - {company or name}",
            "contact_name": name,
            "partner_name": company,
            "email_from": email,
            "phone": phone,
            "description": description,
            "source_id": source.id,
            "medium_id": medium.id,
            "team_id": team.id,
            "user_id": False,
        })
        return request.redirect("/pausa?grazie=1#prova")

    @staticmethod
    def _utm(model, name):
        rec = model.search([("name", "=ilike", name)], limit=1)
        return rec or model.create({"name": name})
