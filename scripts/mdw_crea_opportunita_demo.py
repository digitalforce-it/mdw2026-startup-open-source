#!/usr/bin/env python3
"""
MDW 2026 - Scenario 2: pipeline commerciale demo in Odoo (Community 19) via API XML-RPC.

Cosa crea, per le 20 aziende demo gia' presenti:
  - ~45 opportunita' CRM distribuite sulle fasi della pipeline
      Nuovo / Qualificato / Proposta / Vinto, piu' alcune Perse con motivo
  - per ogni opportunita' in Proposta: un preventivo inviato (Vendite)
  - per ogni opportunita' Vinta: un ordine di vendita confermato
  - attivita' di follow-up ("Richiamare per il preventivo"), alcune gia' scadute:
    sono i preventivi "che sto per perdere" da mostrare in sala
  - 6 prodotti servizio (con IVA vendite predefinita) usati nelle righe dei preventivi

Uso:
  python3 mdw_crea_opportunita_demo.py --dry-run   # mostra il piano, non scrive nulla
  python3 mdw_crea_opportunita_demo.py             # crea davvero

PRIMA DI LANCIARLO: fai un backup del database.
Le opportunita' create hanno "Riferito da" = MDW-DEMO, per ritrovarle.
"""

import random
import sys
import xmlrpc.client
from datetime import date, timedelta

# ------------------------------------------------------------------
# CONFIGURAZIONE: da compilare (come per lo script delle fatture)
# ------------------------------------------------------------------
URL = "http://localhost:8069"
DB = "mdw"
USER = "il-tuo-login"
API_KEY = "incolla-qui-la-chiave-api"

SEED = 2027
MARKER = "MDW-DEMO"

COMPANIES = [
    ("mdw_demo_company_01", "Navigli Advisory Partners S.r.l."),
    ("mdw_demo_company_02", "Brera Cosmetica Lab S.r.l."),
    ("mdw_demo_company_03", "Telvia Sistemi S.p.A."),
    ("mdw_demo_company_04", "Ingrosso Lambro S.r.l."),
    ("mdw_demo_company_05", "Farmaceutica Sempione S.p.A."),
    ("mdw_demo_company_06", "Dolce Ticinese S.r.l."),
    ("mdw_demo_company_07", "Edilnova Città Studi S.r.l."),
    ("mdw_demo_company_08", "Valvotecnica Lombarda S.p.A."),
    ("mdw_demo_company_09", "Utensilmeccanica Bovisa S.r.l."),
    ("mdw_demo_company_10", "Dietalba Nutrizione S.r.l."),
    ("mdw_demo_company_11", "Studio Politecnico Leonardo Associati"),
    ("mdw_demo_company_12", "Polimeri Martesana S.p.A."),
    ("mdw_demo_company_13", "Filature Isola S.r.l."),
    ("mdw_demo_company_14", "Odontomed Ripamonti S.r.l."),
    ("mdw_demo_company_15", "Agrochimica Porta Romana S.r.l."),
    ("mdw_demo_company_16", "Sartoria Moscova Milano S.r.l."),
    ("mdw_demo_company_17", "Lanterna Comunicazione S.r.l."),
    ("mdw_demo_company_18", "Elettromotori Greco S.p.A."),
    ("mdw_demo_company_19", "Metrolab Precisione S.r.l."),
    ("mdw_demo_company_20", "Codeforma Software S.r.l."),
]

# Offerte: (codice prodotto, nome prodotto/opportunita', valore min, valore max, tag)
OFFERS = [
    ("MDW-ERP", "Implementazione gestionale", 12000, 45000, "Gestionale"),
    ("MDW-ECOM", "Sito e-commerce B2B", 8000, 25000, "Sito web"),
    ("MDW-ADS", "Campagna Google Ads annuale", 4000, 12000, "Google Ads"),
    ("MDW-MIGR", "Migrazione dati e formazione", 3000, 9000, "Formazione"),
    ("MDW-MOD", "Modulo personalizzato", 5000, 18000, "Gestionale"),
    ("MDW-ASS", "Contratto di assistenza annuale", 2400, 7200, "Consulenza"),
]

# Quante opportunita' per fase
STAGE_PLAN = [("nuovo", 10), ("qualificato", 10), ("proposta", 12), ("vinto", 8), ("perso", 5)]

LOST_REASONS = ["Prezzo troppo alto", "Scelto un concorrente", "Progetto rimandato"]


def short(name):
    return name.replace(" S.r.l.", "").replace(" S.p.A.", "")


# ------------------------------------------------------------------
# PIANO (deterministico)
# ------------------------------------------------------------------
def build_plan(today):
    rnd = random.Random(SEED)
    slots = [s for s, n in STAGE_PLAN for _ in range(n)]
    rnd.shuffle(slots)
    plan = []
    for i, stage in enumerate(slots):
        ext_id, company = COMPANIES[i % len(COMPANIES)]
        code, offer, lo, hi, tag = rnd.choice(OFFERS)
        value = round(rnd.uniform(lo, hi) / 100) * 100
        opp = {
            "ext_id": ext_id, "company": company, "stage": stage,
            "name": f"{offer} - {short(company)}", "offer_code": code, "tag": tag,
            "value": value, "activity": None, "quote_date": None, "deadline": None,
        }
        if stage == "nuovo":
            opp["probability"] = 10
            opp["deadline"] = today + timedelta(days=rnd.randint(45, 120))
            opp["activity"] = ("Primo contatto: capire il bisogno", today + timedelta(days=rnd.randint(1, 10)))
        elif stage == "qualificato":
            opp["probability"] = 30
            opp["deadline"] = today + timedelta(days=rnd.randint(30, 90))
            opp["activity"] = ("Preparare il preventivo", today + timedelta(days=rnd.randint(-3, 7)))
        elif stage == "proposta":
            opp["probability"] = 60
            sent_ago = rnd.randint(5, 50)
            opp["quote_date"] = today - timedelta(days=sent_ago)
            # preventivi vecchi = scadenza passata e richiamata in ritardo: "sto per perderlo"
            if sent_ago > 25:
                opp["deadline"] = today - timedelta(days=rnd.randint(1, 15))
                opp["activity"] = ("Richiamare per il preventivo", today - timedelta(days=rnd.randint(5, 20)))
            else:
                opp["deadline"] = today + timedelta(days=rnd.randint(10, 40))
                opp["activity"] = ("Richiamare per il preventivo", today + timedelta(days=rnd.randint(1, 10)))
        elif stage == "vinto":
            opp["probability"] = 100
            opp["quote_date"] = today - timedelta(days=rnd.randint(20, 120))
        else:  # perso
            opp["probability"] = 0
            opp["lost_reason"] = rnd.choice(LOST_REASONS)
            opp["quote_date"] = today - timedelta(days=rnd.randint(30, 150))
        plan.append(opp)
    return plan


def print_summary(plan, today):
    print(f"\nOpportunita' pianificate: {len(plan)}")
    for stage, _ in STAGE_PLAN:
        items = [o for o in plan if o["stage"] == stage]
        print(f"  {stage:<12} {len(items):>3}   valore {sum(o['value'] for o in items):>10,.0f} EUR")
    risk = [o for o in plan if o["stage"] == "proposta" and o["deadline"] < today]
    print(f"\nPreventivi a rischio (scaduti, richiamata in ritardo): {len(risk)}")
    for o in risk:
        print(f"  {o['name']:<60} {o['value']:>8,.0f} EUR  inviato il {o['quote_date']}")


# ------------------------------------------------------------------
# ODOO
# ------------------------------------------------------------------
class Odoo:
    def __init__(self):
        common = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/common")
        self.uid = common.authenticate(DB, USER, API_KEY, {})
        if not self.uid:
            sys.exit("Login fallito: controlla URL, DB, USER e API_KEY.")
        self.models = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/object", allow_none=True)

    def call(self, model, method, args, kw=None):
        try:
            return self.models.execute_kw(DB, self.uid, API_KEY, model, method, args, kw or {})
        except xmlrpc.client.Fault as e:
            if "cannot marshal None" in str(e):
                return True
            raise


def find_partner(odoo, ext_id, name):
    xml = odoo.call("ir.model.data", "search_read",
                    [[("model", "=", "res.partner"), ("name", "=", ext_id)]], {"fields": ["res_id"], "limit": 1})
    if xml:
        return xml[0]["res_id"]
    ids = odoo.call("res.partner", "search", [[("name", "=", name), ("is_company", "=", True)]], {"limit": 1})
    return ids[0] if ids else None


def get_or_create(odoo, model, domain, vals):
    ids = odoo.call(model, "search", [domain], {"limit": 1, "context": {"active_test": False}})
    return ids[0] if ids else odoo.call(model, "create", [vals])


def main():
    dry = "--dry-run" in sys.argv
    today = date.today()
    plan = build_plan(today)
    print_summary(plan, today)
    if dry:
        print("\n--dry-run: nessuna modifica fatta in Odoo.")
        return

    odoo = Odoo()
    noctx = {"context": {"active_test": False}}

    if odoo.call("crm.lead", "search_count", [[("referred", "=", MARKER)]], noctx):
        sys.exit(f"\nIn Odoo ci sono gia' opportunita' {MARKER}: script fermato per non duplicarle.")

    # Aziende e un contatto per ciascuna
    partners, contacts = {}, {}
    for ext_id, name in COMPANIES:
        pid = find_partner(odoo, ext_id, name)
        if not pid:
            sys.exit(f"Azienda non trovata: {name}")
        partners[ext_id] = pid
        child = odoo.call("res.partner", "search", [[("parent_id", "=", pid)]], {"limit": 1})
        contacts[ext_id] = child[0] if child else pid

    # Fasi della pipeline, in ordine
    stages = odoo.call("crm.stage", "search_read", [[]], {"fields": ["name", "is_won"], "order": "sequence, id"})
    open_stages = [s["id"] for s in stages if not s["is_won"]]
    won_stage = [s["id"] for s in stages if s["is_won"]]
    if len(open_stages) < 3 or not won_stage:
        sys.exit(f"Fasi CRM inattese: {[s['name'] for s in stages]}")
    stage_ids = {"nuovo": open_stages[0], "qualificato": open_stages[1], "proposta": open_stages[2]}
    print("Fasi usate:", [s["name"] for s in stages])

    # IVA vendite predefinita
    company_id = odoo.call("res.users", "read", [[odoo.uid]], {"fields": ["company_id"]})[0]["company_id"][0]
    tax = odoo.call("res.company", "read", [[company_id]], {"fields": ["account_sale_tax_id"]})[0]["account_sale_tax_id"]
    tax_ids = [tax[0]] if tax else []

    # Prodotti servizio
    products = {}
    for code, offer, lo, hi, _ in OFFERS:
        vals = {"name": offer, "default_code": code, "type": "service", "list_price": (lo + hi) / 2,
                "sale_ok": True, "taxes_id": [(6, 0, tax_ids)]}
        tmpl = get_or_create(odoo, "product.template", [("default_code", "=", code)], vals)
        products[code] = odoo.call("product.product", "search", [[("product_tmpl_id", "=", tmpl)]], {"limit": 1})[0]

    tags = {t: get_or_create(odoo, "crm.tag", [("name", "=", t)], {"name": t}) for t in {o[4] for o in OFFERS}}
    reasons = {r: get_or_create(odoo, "crm.lost.reason", [("name", "=", r)], {"name": r}) for r in LOST_REASONS}

    lead_model = odoo.call("ir.model", "search", [[("model", "=", "crm.lead")]], {"limit": 1})[0]
    call_type = odoo.call("ir.model.data", "search_read",
                          [[("module", "=", "mail"), ("name", "=", "mail_activity_data_call")]], {"fields": ["res_id"]})
    activity_type = call_type[0]["res_id"] if call_type else False

    print(f"\nCreo {len(plan)} opportunita'...")
    errors = 0
    for opp in plan:
        try:
            vals = {
                "type": "opportunity", "name": opp["name"],
                "partner_id": contacts[opp["ext_id"]],
                "expected_revenue": opp["value"], "probability": opp["probability"],
                "tag_ids": [(6, 0, [tags[opp["tag"]]])],
                "user_id": odoo.uid, "referred": MARKER,
                "stage_id": stage_ids.get(opp["stage"], open_stages[2]),
            }
            if opp["deadline"]:
                vals["date_deadline"] = opp["deadline"].isoformat()
            lead_id = odoo.call("crm.lead", "create", [vals])

            order_id = None
            if opp["quote_date"]:
                order_id = odoo.call("sale.order", "create", [{
                    "partner_id": partners[opp["ext_id"]],
                    "opportunity_id": lead_id,
                    "date_order": f"{opp['quote_date'].isoformat()} 10:00:00",
                    "validity_date": (opp["quote_date"] + timedelta(days=30)).isoformat(),
                    "order_line": [(0, 0, {"product_id": products[opp["offer_code"]], "product_uom_qty": 1,
                                           "price_unit": opp["value"]})],
                }])
                if opp["stage"] == "proposta" or opp["stage"] == "perso":
                    odoo.call("sale.order", "write", [[order_id], {"state": "sent"}])

            if opp["stage"] == "vinto":
                odoo.call("sale.order", "action_confirm", [[order_id]])
                odoo.call("crm.lead", "action_set_won", [[lead_id]])
            elif opp["stage"] == "perso":
                odoo.call("sale.order", "write", [[order_id], {"state": "cancel"}])
                odoo.call("crm.lead", "write", [[lead_id], {"lost_reason_id": reasons[opp["lost_reason"]],
                                                            "active": False, "probability": 0}])

            if opp["activity"] and activity_type:
                summary, due = opp["activity"]
                odoo.call("mail.activity", "create", [{
                    "res_model_id": lead_model, "res_id": lead_id, "activity_type_id": activity_type,
                    "summary": summary, "date_deadline": due.isoformat(), "user_id": odoo.uid,
                }])
            print(f"  {opp['stage']:<12} {opp['name'][:55]:<55} ok")
        except Exception as e:  # noqa: BLE001
            errors += 1
            print(f"  {opp['stage']:<12} {opp['name'][:55]:<55} ERRORE: {e}")

    print(f"\nFatto. Errori: {errors}. In Odoo: CRM > Pipeline; Vendite > Preventivi.")


if __name__ == "__main__":
    main()
