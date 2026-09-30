# Solleciti automatici per le fatture scadute

Odoo Community non ha i solleciti di pagamento (sono una funzione Enterprise). Si ottengono con una **regola di automazione**, senza codice.

## 1. Installare le regole di automazione

App > togliere il filtro "App" > cercare "automazione" > installare **Regole di automazione** (`base_automation`). Poi attivare la modalità sviluppatore (Impostazioni > Attiva modalità sviluppatore).

## 2. Il modello di email

Impostazioni > Funzioni tecniche > E-mail > Modelli > Nuovo:

- **Nome:** Sollecito di pagamento
- **Si applica a:** Registrazione contabile
- **Oggetto:** `Sollecito: fattura {{ object.name }} scaduta`
- **Impostazioni > A (partner):** `{{ object.partner_id.id }}`
- **Lingua:** `{{ object.partner_id.lang }}` (così date e importi escono in formato italiano)
- **Corpo** (in modalità codice):

```html
<div>
  <p>Gentile cliente,</p>
  <p>dai nostri registri la fattura <strong><t t-out="object.name"/></strong>
  del <strong><t t-out="format_date(object.invoice_date)"/></strong>,
  scaduta il <strong><t t-out="format_date(object.invoice_date_due)"/></strong>,
  risulta ancora da saldare per un importo di
  <strong><t t-out="format_amount(object.amount_residual, object.currency_id)"/></strong>.</p>
  <p>Se il pagamento è già stato effettuato, la preghiamo di ignorare questo messaggio.</p>
  <p>Cordiali saluti</p>
</div>
```

## 3. La regola

Impostazioni > Funzioni tecniche > Automazione > Regole di automazione > Nuovo:

- **Nome:** Sollecito fatture scadute
- **Modello:** Registrazione contabile
- **Attivazione:** In base al campo data, **Scadenza**, **7 Giorni Dopo**
- **Applicare a:**

```
[("move_type", "=", "out_invoice"), ("state", "=", "posted"), ("payment_state", "in", ["not_paid", "partial"])]
```

- **Azioni:** Invia e-mail con il modello "Sollecito di pagamento"; Crea attività "Sollecitare il pagamento" assegnata al commerciale.

## 4. Attenzione alle fatture già scadute

Le regole basate sul tempo controllano solo i record la cui data (più il ritardo) cade **dopo l'ultima esecuzione** della regola. Se create la regola quando le fatture sono già scadute da tempo, non le sollecita. Per applicarla anche a quelle, dalla shell di Odoo:

```
r = env['base.automation'].search([('name', 'ilike', 'Sollecito')]); r.last_run = False
env['base.automation']._cron_process_time_based_automations()
env.cr.commit()
```
