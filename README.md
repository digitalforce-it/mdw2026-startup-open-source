# La startup open source

**45 minuti per costruire il software che ti serve**
Milano Digital Week 2026 · Le Village by CA Milano · 1 ottobre 2026 · DigitalForce

Questo repository contiene tutto quello che abbiamo usato nella sessione: il codice, i dati dimostrativi, le istruzioni e i prompt. È pubblico perché l'idea della sessione è proprio questa: con un gestionale open source, un'intelligenza artificiale e un problema descritto bene, il software che serve si può costruire da soli.

## Tre ingredienti, niente magia

1. **Un ERP open source.** Abbiamo usato Odoo 19 Community Edition, ma il concetto vale anche per altri gestionali open source.
2. **L'AI che preferite**, collegata al gestionale tramite le sue API.
3. **Un prompt fatto bene:** cosa serve, per chi, con quali dati. Li trovate in [`prompts/`](prompts/).

## Cosa c'è qui

| Cartella | Contenuto |
|---|---|
| [`modules/mdw_lead_form`](modules/mdw_lead_form) | Modulo Odoo: landing page e profilo social di "Pausa", una startup di fantasia. Il modulo di contatto crea un lead nel CRM, con la fonte (Instagram, sito, volantino QR). |
| [`scripts/`](scripts) | Script che popolano un database Odoo con dati realistici: fatture con pagamenti e ritardi, una pipeline commerciale, lead in arrivo. |
| [`data/`](data) | Le 20 aziende e i contatti dimostrativi usati negli script (tutti di fantasia). |
| [`docs/`](docs) | Istruzioni passo passo: installazione, solleciti automatici, filtri salvati, pagina Pausa. |
| [`prompts/`](prompts) | I prompt usati per costruire le app con l'AI. |
| [`slides/`](slides) | Le slide della sessione in PDF. |

## Per ripartire da zero

1. Installate **Odoo 19 Community** ([documentazione ufficiale](https://www.odoo.com/documentation/19.0/administration/on_premise.html)) e create un database.
2. **Prima di installare Fatturazione**, impostate il paese dell'azienda su **Italia**, così Odoo carica il piano dei conti italiano con le aliquote IVA. Controllate in Fatturazione > Configurazione > Impostazioni > Localizzazione fiscale.
3. Installate **Fatturazione**, **CRM** e **Vendite**.
4. Importate i contatti da `data/mdw_contatti_demo_milano.xlsx` (Contatti > Importa).
5. Lanciate gli script in `scripts/`, sempre prima con `--dry-run`. Istruzioni in [`docs/installazione.md`](docs/installazione.md).
6. Configurate i solleciti automatici e i filtri: [`docs/solleciti.md`](docs/solleciti.md) e [`docs/filtri.md`](docs/filtri.md).

**Fate sempre un backup del database prima di lanciare gli script.** Le fatture confermate non si cancellano con un clic.

## I quattro esempi della sessione

- **Chi non ha ancora pagato:** fatture scadute raggruppate per cliente, e solleciti automatici 7 giorni dopo la scadenza.
- **I preventivi che stiamo per perdere:** pipeline con le richiamate in ritardo.
- **I contatti che arrivano e spariscono:** lead da Instagram, sito e volantino, e quelli senza risposta.
- **La cassa che non torna:** saldo in banca, saldo contabile e previsione di cassa.

## Licenza

- Codice (moduli e script): **LGPL-3.0**, come Odoo Community. Testo in [`LICENSE`](LICENSE) e [`COPYING`](COPYING).
- Documentazione, prompt e slide: **CC BY 4.0**. Potete riusarli citando la fonte.

Tutte le aziende, le persone e i dati di questo repository sono di fantasia.

## Contatti

DigitalForce, Milano · cesare@digitalforce.it · naveed@digitalforce.it · 02 7310 3509

Open source? Open soccorso.
