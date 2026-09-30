# Pausa: landing page e profilo social

Pausa è una startup di fantasia (pranzi consegnati negli uffici di Milano). Il modulo `mdw_lead_form` serve due pagine e riceve il modulo di contatto, **senza bisogno dell'app Sito web**.

| Indirizzo | Cosa mostra |
|---|---|
| `/pausa` | Landing page con il modulo "Settimana di prova" |
| `/pausa/social` | Profilo social dimostrativo di Pausa; il link in bio porta alla landing con `utm_source=instagram` |
| `/pausa/richiesta` | Riceve il modulo (POST) e crea un lead nel CRM |

## Fonte del contatto

Il parametro `utm_source` nel link diventa la **fonte** del lead:

- `/pausa?utm_source=instagram` → Instagram
- `/pausa?utm_source=qr` → Volantino QR
- `/pausa?utm_source=google` → Google Ads
- senza parametro → Sito web

## Installazione

1. Copiare la cartella `mdw_lead_form` nella cartella dei moduli personalizzati (`addons_path`).
2. Riavviare Odoo, poi App > Aggiorna elenco app > cercare "Pausa" > Attiva.
3. Richiede il **CRM**; per avere i lead separati dalle opportunità, attivare l'opzione **Lead** nelle impostazioni del CRM.

## Sicurezza

Il modulo è pubblico: chiunque abbia il link può creare lead. Ha un campo anti-spam nascosto, ma in produzione conviene aggiungere un captcha o disinstallarlo dopo l'uso. Le pagine sono HTML statico in `static/`: si modificano senza toccare il codice Python.
