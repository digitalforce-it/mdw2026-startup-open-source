# Cassa: saldo in banca e previsione di cassa

Il modulo `mdw_cash_flow` risponde a una domanda sola: **quanti soldi avrò in banca nei prossimi mesi?** Aggiunge il menu **Fatturazione > Cassa** con due voci.

| Voce | Cosa mostra |
|---|---|
| **Saldo in banca** | Il saldo vero (inserito a mano) accanto al saldo secondo la contabilità, con il pulsante "Apri la previsione" |
| **Previsione di cassa** | Grafico mensile del saldo previsto, tabella pivot per tipo di movimento ed elenco dei singoli movimenti |

## Perché i due saldi non tornano

Nella demo il saldo in banca è **35.000 €** e quello contabile **288.196,94 €**. La contabilità di Odoo vede soprattutto le entrate registrate (fatture incassate e pagamenti), non quello che il conto in banca contiene davvero. La previsione parte quindi dal saldo reale, non da quello contabile.

Il saldo in banca è un campo semplice dell'azienda (`mdw_cash_start`, valore predefinito 35.000). Per usare il modulo con i vostri dati, correggetelo in **Fatturazione > Cassa > Saldo in banca**. Il saldo contabile è calcolato (conti di liquidità più conti "in sospeso" dei pagamenti).

## Come si costruisce la previsione

Ogni riga è un movimento di denaro atteso:

- **Saldo iniziale**: il saldo in banca di oggi.
- **Da incassare / Da pagare**: righe aperte di fatture clienti e fornitori, alla data di scadenza. I fornitori hanno segno negativo.
- **Ordine confermato**: ordini da fatturare, ipotizzando l'incasso 30 giorni dopo.
- **Preventivo (ponderato)**: preventivi aperti, moltiplicati per la probabilità dell'opportunità nel CRM (50% se manca), incasso a 30 giorni.

**Chi paga in ritardo:** gli importi già scaduti vengono spostati a oggi e marcati "In ritardo". Il filtro predefinito **Senza ritardi** li esclude; **Solo in ritardo** mostra quanto pesano i clienti che non pagano.

## Filtri disponibili

Saldo e fatture, Ordini confermati, Preventivi (ponderati), Senza ritardi, Solo in ritardo. Raggruppamenti: per tipo, per mese, per contatto.

## Installazione

1. Copiare la cartella `mdw_cash_flow` nella cartella dei moduli personalizzati (`addons_path`).
2. Riavviare Odoo, poi App > Aggiorna elenco app > cercare "Previsione di cassa" > Attiva.
3. Richiede **Fatturazione** (`account`) e **Vendite con CRM** (`sale_crm`).
4. Per una demo realistica, lanciare prima gli script in `scripts/` (fatture, pipeline, lead).

## Limiti

È un primo passo, non un prodotto finito:

- Il saldo in banca va aggiornato a mano: non legge l'estratto conto.
- Una sola valuta (quella dell'azienda) e un solo saldo per azienda.
- Ordini e preventivi usano una regola fissa a 30 giorni, non i termini di pagamento reali.
- La vista è in sola lettura: si guarda, non si modifica.
