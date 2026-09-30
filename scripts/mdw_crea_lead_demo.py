# MDW 2026 - Scenario 3: lead demo per Pausa (da eseguire nella shell di Odoo)
#
# Avvio:
#   sudo -u odoo /opt/odoo/venv/bin/python3 /opt/odoo/odoo/odoo-bin shell -c /etc/odoo/mdw.conf -d mdw --no-http
# poi al prompt >>>
#   exec(open('/root/mdw_crea_lead_demo.py').read())
#
# Cosa fa:
#   - crea (se manca) il team di vendita "Pausa" e ci sposta i lead di prova gia' arrivati dal form
#   - cancella i lead di test "Settimana di prova - ..." inviati finora dal form
#   - crea 15 lead realistici, retrodatati negli ultimi 12 giorni:
#       5 dimenticati (nessun addetto, nessuna attivita')
#       5 in lavorazione (attivita' pianificata, alcune gia' in ritardo)
#       5 gestiti (risposta data, prossimo passo pianificato)
#   - crea il filtro condiviso "Contatti senza risposta" nel menu Lead

from datetime import datetime, timedelta

MARKER = "MDW-DEMO-PAUSA"
Lead = env["crm.lead"].with_context(active_test=False, tracking_disable=True, mail_create_nolog=True)

if Lead.search_count([("referred", "=", MARKER)]):
    raise SystemExit(f"Ci sono gia' lead {MARKER}: script fermato per non duplicarli.")

# --- Team "Pausa" -------------------------------------------------------
team = env["crm.team"].search([("name", "=", "Pausa")], limit=1)
if not team:
    team = env["crm.team"].create({"name": "Pausa", "use_leads": True, "use_opportunities": True})

# --- Pulizia dei lead di test inviati dal form ----------------------------
tests = Lead.search([("type", "=", "lead"), ("name", "=ilike", "Settimana di prova - %"), ("referred", "!=", MARKER)])
print(f"Lead di test cancellati: {len(tests)}")
tests.unlink()

# --- Utenti, fonti, tipi di attivita' ------------------------------------
def user(name):
    return env["res.users"].search([("name", "ilike", name)], limit=1) or env.user

cesare, naveed = user("cesare"), user("naveed")

def utm(model, name):
    return env[model].search([("name", "=ilike", name)], limit=1) or env[model].create({"name": name})

sources = {k: utm("utm.source", k) for k in ["Instagram", "Sito web", "Google Ads", "Volantino QR"]}
medium = utm("utm.medium", "Website")
todo = env.ref("mail.mail_activity_data_todo")
call = env.ref("mail.mail_activity_data_call")
email_type = env.ref("mail.mail_activity_data_email", raise_if_not_found=False) or todo
lead_model = env["ir.model"]._get("crm.lead")

# --- Dati: (stato, giorni fa, contatto, azienda, persone, fonte, nota, addetto, scadenza attivita') ---
DATA = [
    # dimenticati: nessun addetto, nessuna attivita'
    ("dimenticato", 9, "Chiara Galli", "Studio Associato Galli Commercialisti", "Da 11 a 30", "Instagram", "Avremmo bisogno anche di opzioni senza glutine.", None, None),
    ("dimenticato", 7, "Marco Pellegrini", "Lampo Creativi", "Fino a 10", "Instagram", "Si può ordinare anche il venerdì?", None, None),
    ("dimenticato", 11, "Federica Rinaldi", "Rinaldi & Partners Avvocati", "Da 31 a 100", "Google Ads", "Siamo in via Pola, consegnate anche lì?", None, None),
    ("dimenticato", 5, "Stefano Colombo", "Nuvola Coworking Isola", "Più di 100", "Sito web", "Coworking con 120 postazioni: vorremmo proporre Pausa a tutti i membri.", None, None),
    ("dimenticato", 6, "Laura Mazza", "Studio Mazza Architetti", "Fino a 10", "Instagram", "", None, None),
    # in lavorazione: attivita' pianificata (negativo = in ritardo)
    ("in_corso", 4, "Davide Ferri", "Ferri Assicurazioni", "Da 11 a 30", "Sito web", "Preferiremmo la consegna alle 13.", cesare, -2),
    ("in_corso", 2, "Sara Longhi", "Longhi Design Studio", "Fino a 10", "Instagram", "Due persone vegane.", naveed, 0),
    ("in_corso", 3, "Paolo Riva", "Riva Consulting", "Da 11 a 30", "Volantino QR", "Ho trovato il volantino in ascensore.", cesare, -1),
    ("in_corso", 1, "Giorgia Villa", "Villa & Sala Notai", "Da 11 a 30", "Google Ads", "", cesare, 1),
    ("in_corso", 2, "Matteo Conti", "Contiweb Software", "Da 31 a 100", "Instagram", "Il venerdì facciamo pranzo tutti insieme.", naveed, 0),
    # gestiti: risposta data, prossimo passo pianificato
    ("gestito", 10, "Elisa Fumagalli", "Fumagalli Eventi", "Da 11 a 30", "Sito web", "", cesare, 3),
    ("gestito", 8, "Andrea Sironi", "Sironi Ingegneria", "Da 31 a 100", "Google Ads", "Abbiamo due sedi a Milano.", naveed, 2),
    ("gestito", 12, "Valentina Ghezzi", "Ghezzi Comunicazione", "Fino a 10", "Instagram", "", cesare, 4),
    ("gestito", 6, "Roberto Lissoni", "Studio Lissoni Dentisti", "Da 11 a 30", "Volantino QR", "Pausa pranzo breve, massimo 40 minuti.", naveed, 1),
    ("gestito", 9, "Francesca Porta", "Porta Nuova Legal", "Da 31 a 100", "Instagram", "Interessati anche a pranzi per riunioni con clienti.", cesare, 5),
]

def slug(text):
    keep = "".join(c.lower() if c.isalnum() else " " for c in text)
    words = [w for w in keep.split() if w not in ("studio", "associato", "partners", "e", "sala", "srl")]
    return "".join(words[:2]) or "azienda"

now = datetime.now().replace(microsecond=0)
today = now.date()
created = []

for n, (state, days_ago, contact, company, size, source, note, owner, due) in enumerate(DATA, 1):
    first, last = contact.split(" ", 1)
    email = f"{first.lower()}.{last.lower().replace(' ', '')}@{slug(company)}.it"
    notes = f"<p>Persone in ufficio: {size}</p>" + (f"<p>{note}</p>" if note else "")
    lead = Lead.create({
        "type": "lead",
        "name": f"Settimana di prova - {company}",
        "contact_name": contact,
        "partner_name": company,
        "email_from": email,
        "phone": f"+39 02 {3000000 + n * 73129 % 6999999:07d}",
        "description": notes,
        "source_id": sources[source].id,
        "medium_id": medium.id,
        "team_id": team.id,
        "user_id": owner.id if owner else False,
        "referred": MARKER,
    })

    if state == "in_corso":
        env["mail.activity"].create({
            "res_model_id": lead_model.id, "res_id": lead.id, "activity_type_id": call.id,
            "summary": "Rispondere alla richiesta", "user_id": owner.id,
            "date_deadline": today + timedelta(days=due),
        })
    elif state == "gestito":
        done = env["mail.activity"].create({
            "res_model_id": lead_model.id, "res_id": lead.id, "activity_type_id": email_type.id,
            "summary": "Rispondere alla richiesta", "user_id": owner.id,
            "date_deadline": today - timedelta(days=days_ago - 1),
        })
        done.action_feedback(feedback="Inviati menu della settimana e proposta di date per la prova.")
        env["mail.activity"].create({
            "res_model_id": lead_model.id, "res_id": lead.id, "activity_type_id": todo.id,
            "summary": "Confermare la data della settimana di prova", "user_id": owner.id,
            "date_deadline": today + timedelta(days=due),
        })

    # Retrodata l'arrivo del contatto
    arrived = now - timedelta(days=days_ago, hours=(n * 5) % 9)
    env.cr.execute(
        "UPDATE crm_lead SET create_date = %s, write_date = %s, date_open = %s WHERE id = %s",
        (arrived, arrived, arrived if owner else None, lead.id),
    )
    created.append((state, contact, company, source))

# --- Filtro condiviso "Contatti senza risposta" nel menu Lead -------------
action = env.ref("crm.crm_lead_all_leads", raise_if_not_found=False)
if action and not env["ir.filters"].search([("name", "=", "Contatti senza risposta"), ("model_id", "=", "crm.lead")]):
    try:
        env["ir.filters"].create({
            "name": "Contatti senza risposta",
            "model_id": "crm.lead",
            "domain": "[('type', '=', 'lead'), ('activity_ids', '=', False), ('user_id', '=', False)]",
            "action_id": action.id,
            "user_id": False,
        })
        print("Filtro 'Contatti senza risposta' creato.")
    except Exception as e:
        print(f"Filtro non creato ({e}): crealo a mano dalla vista Lead.")

env.cr.commit()

print(f"\nTeam: {team.name} | lead creati: {len(created)}")
for state, contact, company, source in created:
    print(f"  {state:<12} {contact:<20} {company:<40} {source}")
