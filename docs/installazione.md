# Installazione e dati dimostrativi

## Prerequisiti

- Odoo 19 Community con **Fatturazione**, **CRM** e **Vendite** installati.
- Localizzazione fiscale **Italia** (Fatturazione > Configurazione > Impostazioni). Se il pacchetto risulta "Piano dei conti generico" e non si può cambiare, è perché ci sono già registrazioni contabili: partite da un database vuoto o da un backup precedente.
- Le aziende di `data/mdw_contatti_demo_milano.xlsx` importate in Contatti.
- Una **chiave API**: avatar in alto a destra > Preferenze > Sicurezza account > Nuova chiave API.

## Backup prima di tutto

Sul server, con PostgreSQL:

```
sudo -u postgres pg_dump -Fc -f /tmp/backup.dump NOME_DATABASE
tar czf /tmp/filestore.tar.gz -C /percorso/data_dir/filestore NOME_DATABASE
```

## 1. Fatture (`scripts/mdw_crea_fatture_demo.py`)

Crea circa 150 fatture degli ultimi sei mesi con IVA 22%, le conferma e registra i pagamenti secondo il profilo di ogni cliente: puntuale, lento o cattivo pagatore.

1. Compilate `URL`, `DB`, `USER`, `API_KEY` in cima al file.
2. `python3 mdw_crea_fatture_demo.py --dry-run` mostra il piano senza scrivere nulla.
3. `python3 mdw_crea_fatture_demo.py` crea le fatture.

Lo script usa l'imposta vendite predefinita dell'azienda e si ferma se trova già fatture con riferimento `MDW-DEMO`, per non duplicarle.

## 2. Pipeline commerciale (`scripts/mdw_crea_opportunita_demo.py`)

Crea circa 45 opportunità distribuite sulle fasi (Nuovo, Qualificato, Proposta, Vinto, più alcune perse), con preventivi inviati, ordini confermati e attività di richiamata, alcune in ritardo.

Stessa configurazione e stesso uso dello script fatture.

## 3. Lead in arrivo (`scripts/mdw_crea_lead_demo.py`)

Da eseguire **nella shell di Odoo**, perché retrodata i lead:

```
sudo -u odoo /percorso/odoo-bin shell -c /etc/odoo/odoo.conf -d NOME_DATABASE --no-http
>>> exec(open('/tmp/mdw_crea_lead_demo.py').read())
```

Crea il team "Pausa" e 15 lead: 5 dimenticati, 5 in lavorazione, 5 gestiti. Richiede l'opzione **Lead** attiva nelle impostazioni del CRM.

## Nota sulle email

Se il server Odoo ha un server di posta configurato, i solleciti automatici **partono davvero**. I domini delle aziende di fantasia potrebbero esistere: per le prove usate un server senza posta in uscita, o una casella di test.
