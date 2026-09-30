#!/usr/bin/env python3
"""
MDW 2026 - Crea fatture demo in Odoo (Community 19) via API XML-RPC.

Cosa fa:
  1. trova le 20 aziende demo gia' importate (per ID esterno o per nome)
  2. crea ~160 fatture cliente degli ultimi 6 mesi, con righe di servizi
  3. le conferma in ordine di data
  4. registra i pagamenti: puntuali, in ritardo, parziali o assenti,
     secondo il "profilo pagatore" di ogni cliente
  -> risultato: una vista "Chi non ha pagato" realistica da mostrare in sala.

Uso:
  python mdw_crea_fatture_demo.py --dry-run   # mostra il piano, non scrive nulla
  python mdw_crea_fatture_demo.py             # crea davvero le fatture

PRIMA DI LANCIARLO: duplica il database (Gestione database > Duplica) e lavora
sulla copia, oppure tieni un backup. Le fatture confermate non si cancellano
con un clic.
Tutte le fatture create hanno Riferimento "MDW-DEMO-nnn", per ritrovarle.
"""

import random
import sys
import xmlrpc.client
from datetime import date, timedelta

# ------------------------------------------------------------------
# CONFIGURAZIONE: da compilare
# ------------------------------------------------------------------
URL = "https://il-tuo-odoo.example.com"   # indirizzo di Odoo, senza / finale
DB = "mdw"                                 # nome del database
USER = "admin@example.com"                 # login dell'utente
API_KEY = "incolla-qui-la-chiave-api"      # Preferenze > Sicurezza account > Nuova chiave API

SEED = 2026            # stesso seed = stesse fatture a ogni esecuzione
MONTHS_BACK = 6        # periodo coperto dalle fatture
VAT_RATE = 22.0        # aliquota IVA da applicare (se trovata in Odoo)
REF_PREFIX = "MDW-DEMO"

# ------------------------------------------------------------------
# AZIENDE DEMO (dal file mdw_contatti_demo_milano_1.xlsx) e profilo pagatore
#   buono  = paga puntuale
#   lento  = paga spesso in ritardo, qualcosa resta aperto
#   cattivo = molte fatture scadute e non pagate (la storia da raccontare)
# ------------------------------------------------------------------
COMPANIES = [
    ("mdw_demo_company_01", "Navigli Advisory Partners S.r.l.", "buono"),
    ("mdw_demo_company_02", "Brera Cosmetica Lab S.r.l.", "lento"),
    ("mdw_demo_company_03", "Telvia Sistemi S.p.A.", "buono"),
    ("mdw_demo_company_04", "Ingrosso Lambro S.r.l.", "cattivo"),
    ("mdw_demo_company_05", "Farmaceutica Sempione S.p.A.", "buono"),
    ("mdw_demo_company_06", "Dolce Ticinese S.r.l.", "lento"),
    ("mdw_demo_company_07", "Edilnova Città Studi S.r.l.", "cattivo"),
    ("mdw_demo_company_08", "Valvotecnica Lombarda S.p.A.", "buono"),
    ("mdw_demo_company_09", "Utensilmeccanica Bovisa S.r.l.", "buono"),
    ("mdw_demo_company_10", "Dietalba Nutrizione S.r.l.", "buono"),
    ("mdw_demo_company_11", "Studio Politecnico Leonardo Associati", "buono"),
    ("mdw_demo_company_12", "Polimeri Martesana S.p.A.", "lento"),
    ("mdw_demo_company_13", "Filature Isola S.r.l.", "buono"),
    ("mdw_demo_company_14", "Odontomed Ripamonti S.r.l.", "buono"),
    ("mdw_demo_company_15", "Agrochimica Porta Romana S.r.l.", "lento"),
    ("mdw_demo_company_16", "Sartoria Moscova Milano S.r.l.", "cattivo"),
    ("mdw_demo_company_17", "Lanterna Comunicazione S.r.l.", "buono"),
    ("mdw_demo_company_18", "Elettromotori Greco S.p.A.", "lento"),
    ("mdw_demo_company_19", "Metrolab Precisione S.r.l.", "buono"),
    ("mdw_demo_company_20", "Codeforma Software S.r.l.", "buono"),
]

# Servizi fatturati: (descrizione, prezzo minimo, prezzo massimo)
SERVICES = [
    ("Consulenza e analisi dei processi aziendali", 800, 3500),
    ("Canone mensile assistenza gestionale", 250, 900),
    ("Sviluppo modulo personalizzato", 1500, 6500),
    ("Formazione utenti (giornata)", 600, 1200),
    ("Hosting e manutenzione server", 150, 600),
    ("Gestione campagne Google Ads (mensile)", 400, 1500),
    ("Migrazione dati da fogli Excel", 700, 2500),
    ("Aggiornamento contenuti sito web", 300, 1200),
]


# ------------------------------------------------------------------
# PIANO (deterministico): quali fatture, con quali date e pagamenti
# ------------------------------------------------------------------
def build_plan(today):
    rnd = random.Random(SEED)
    start = today - timedelta(days=30 * MONTHS_BACK)
    span = (today - timedelta(days=3) - start).days
    invoices = []

    for ext_id, name, profile in COMPANIES:
        for _ in range(rnd.randint(6, 10)):
            inv_date = start + timedelta(days=rnd.randint(0, span))
            term = rnd.choice([30, 30, 60]) if profile != "cattivo" else rnd.choice([60, 90])
            due = inv_date + timedelta(days=term)

            lines = []
            for desc, lo, hi in rnd.sample(SERVICES, rnd.randint(1, 3)):
                lines.append((desc, round(rnd.uniform(lo, hi) / 10) * 10))

            # Totale lordo approssimato, per decidere gli importi dei parziali
            gross = sum(p for _, p in lines) * (1 + VAT_RATE / 100)

            pay_date, share = None, 0.0     # share = quota pagata (1 = tutto)
            overdue = due < today
            r = rnd.random()
            if overdue:
                if profile == "buono":
                    pay_date, share = due + timedelta(days=rnd.randint(-7, 4)), 1.0
                elif profile == "lento":
                    if r < 0.60:
                        pay_date, share = due + timedelta(days=rnd.randint(8, 35)), 1.0
                    elif r < 0.75:
                        pay_date, share = due + timedelta(days=rnd.randint(5, 20)), rnd.choice([0.3, 0.5])
                else:  # cattivo
                    if r < 0.20:
                        pay_date, share = due + timedelta(days=rnd.randint(15, 45)), 1.0
                    elif r < 0.40:
                        pay_date, share = due + timedelta(days=rnd.randint(5, 30)), rnd.choice([0.3, 0.5])
            else:
                if profile == "buono" and r < 0.30:
                    pay_date, share = inv_date + timedelta(days=rnd.randint(3, 20)), 1.0

            # Un pagamento non puo' essere nel futuro ne' prima della fattura
            if pay_date is not None:
                if pay_date >= today:
                    pay_date, share = None, 0.0
                elif pay_date < inv_date:
                    pay_date = inv_date + timedelta(days=1)

            invoices.append({
                "ext_id": ext_id, "partner_name": name, "profile": profile,
                "invoice_date": inv_date, "due": due, "lines": lines,
                "pay_date": pay_date, "share": share, "gross": gross,
            })

    invoices.sort(key=lambda i: i["invoice_date"])
    for n, inv in enumerate(invoices, 1):
        inv["ref"] = f"{REF_PREFIX}-{n:03d}"
    return invoices


def print_summary(invoices, today):
    print(f"\nFatture pianificate: {len(invoices)}")
    paid = sum(1 for i in invoices if i["share"] == 1.0)
    partial = sum(1 for i in invoices if 0 < i["share"] < 1)
    open_overdue = [i for i in invoices if i["share"] < 1 and i["due"] < today]
    print(f"  pagate: {paid} | parziali: {partial} | aperte: {len(invoices) - paid - partial}")
    print(f"  scadute e non (del tutto) pagate: {len(open_overdue)}\n")
    per = {}
    for i in open_overdue:
        per.setdefault(i["partner_name"], 0.0)
        per[i["partner_name"]] += i["gross"] * (1 - i["share"])
    print("Chi non ha pagato (stima, IVA inclusa):")
    for name, amt in sorted(per.items(), key=lambda x: -x[1]):
        print(f"  {name:<42} {amt:>10,.0f} EUR")


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
            # Alcuni metodi Odoo restituiscono None: l'azione e' riuscita comunque
            if "cannot marshal None" in str(e):
                return True
            raise


def find_partner(odoo, ext_id, name):
    xml = odoo.call("ir.model.data", "search_read",
                    [[("model", "=", "res.partner"), ("name", "=", ext_id)]],
                    {"fields": ["res_id"], "limit": 1})
    if xml:
        return xml[0]["res_id"]
    ids = odoo.call("res.partner", "search", [[("name", "=", name), ("is_company", "=", True)]], {"limit": 1})
    return ids[0] if ids else None


def main():
    dry = "--dry-run" in sys.argv
    today = date.today()
    plan = build_plan(today)
    print_summary(plan, today)
    if dry:
        print("\n--dry-run: nessuna modifica fatta in Odoo.")
        return

    odoo = Odoo()

    existing = odoo.call("account.move", "search_count", [[("ref", "=like", f"{REF_PREFIX}-%")]])
    if existing:
        sys.exit(f"\nIn Odoo ci sono gia' {existing} fatture {REF_PREFIX}: script fermato per non duplicarle.")

    partners = {}
    for ext_id, name, _ in COMPANIES:
        pid = find_partner(odoo, ext_id, name)
        if not pid:
            sys.exit(f"Azienda non trovata in Odoo: {name} ({ext_id})")
        partners[ext_id] = pid

    journal = odoo.call("account.journal", "search", [[("type", "=", "sale")]], {"limit": 1})
    if not journal:
        sys.exit("Nessun sezionale vendite trovato: l'app Fatturazione e' installata?")
    # IVA: prima l'imposta vendite predefinita dell'azienda (Impostazioni > Imposte),
    # poi, in mancanza, una qualsiasi imposta vendite al VAT_RATE%
    tax = []
    company_id = odoo.call("res.users", "read", [[odoo.uid]], {"fields": ["company_id"]})[0]["company_id"][0]
    default_tax = odoo.call("res.company", "read", [[company_id]], {"fields": ["account_sale_tax_id"]})[0]["account_sale_tax_id"]
    if default_tax:
        tax = [default_tax[0]]
        print(f"IVA usata: {default_tax[1]} (imposta vendite predefinita)")
    else:
        tax = odoo.call("account.tax", "search",
                        [[("type_tax_use", "=", "sale"), ("amount_type", "=", "percent"), ("amount", "=", VAT_RATE)]],
                        {"limit": 1})
    if not tax:
        print(f"ATTENZIONE: nessuna IVA vendite al {VAT_RATE}% trovata, fatture senza imposta.")

    print(f"\nCreo {len(plan)} fatture...")
    errors = 0
    for inv in plan:
        try:
            line_vals = []
            for desc, price in inv["lines"]:
                vals = {"name": desc, "quantity": 1, "price_unit": price}
                if tax:
                    vals["tax_ids"] = [(6, 0, tax)]
                line_vals.append((0, 0, vals))

            move_id = odoo.call("account.move", "create", [{
                "move_type": "out_invoice",
                "partner_id": partners[inv["ext_id"]],
                "journal_id": journal[0],
                "invoice_date": inv["invoice_date"].isoformat(),
                "invoice_date_due": inv["due"].isoformat(),
                "invoice_payment_term_id": False,
                "ref": inv["ref"],
                "invoice_line_ids": line_vals,
            }])
            odoo.call("account.move", "action_post", [[move_id]])

            if inv["pay_date"] and inv["share"] > 0:
                total = odoo.call("account.move", "read", [[move_id]], {"fields": ["amount_total"]})[0]["amount_total"]
                amount = round(total * inv["share"], 2)
                ctx = {"context": {"active_model": "account.move", "active_ids": [move_id]}}
                wiz = odoo.call("account.payment.register", "create",
                                [{"amount": amount, "payment_date": inv["pay_date"].isoformat()}], ctx)
                odoo.call("account.payment.register", "action_create_payments", [[wiz]], ctx)

            print(f"  {inv['ref']}  {inv['invoice_date']}  {inv['partner_name'][:32]:<32} ok")
        except Exception as e:  # noqa: BLE001 - continuiamo con le altre fatture
            errors += 1
            print(f"  {inv['ref']}  ERRORE: {e}")

    print(f"\nFatto. Errori: {errors}. In Odoo: Fatturazione > Clienti > Fatture, filtro Riferimento contiene {REF_PREFIX}.")


if __name__ == "__main__":
    main()
