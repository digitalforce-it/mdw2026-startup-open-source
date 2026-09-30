# Filtri salvati usati nella sessione

Per ciascuno: applicare il filtro, poi Preferiti > Salva ricerca corrente (condividendolo con tutti gli utenti se serve). I filtri con codice si inseriscono in Personalizza filtro, in modalità sviluppatore.

## Chi non ha pagato (Fatturazione > Clienti > Fatture)

- Filtro predefinito **In ritardo**
- Raggruppa per **Partner**
- Consiglio: aggiungere la colonna **Importo dovuto** e ordinare per quella, così in cima c'è chi deve di più.

## Preventivi a rischio (CRM > Flusso)

```
[("activity_state", "=", "overdue")]
```

Solo le opportunità con un'attività scaduta, cioè una richiamata che doveva già essere fatta. Nel kanban corrispondono alla parte rossa della barra sopra ogni colonna.

## Contatti senza risposta (CRM > Lead)

```
[("activity_ids", "=", False), ("user_id", "=", False)]
```

Lead senza attività e senza addetto: nessuno li ha presi in carico.
