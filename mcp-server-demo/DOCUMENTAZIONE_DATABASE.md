# 📅 Documentazione Database Calendario Prenotazioni

## 📋 Panoramica

Questo database è progettato per gestire un sistema completo di calendario prenotazioni, con gestione clienti, tipologie di appuntamenti e tracciamento delle modifiche.

---

## 🗄️ Struttura del Database

Il database è composto da **4 tabelle principali** più **3 indici** per ottimizzare le performance.

---

## 📊 Tabelle

### 1. **CLIENTI**

Contiene tutte le informazioni anagrafiche e di contatto dei clienti.

| Campo | Tipo | Descrizione | Vincoli |
|-------|------|-------------|---------|
| `id_cliente` | INTEGER | Identificativo univoco del cliente | PRIMARY KEY, AUTOINCREMENT |
| `nome` | TEXT | Nome del cliente | NOT NULL |
| `cognome` | TEXT | Cognome del cliente | NOT NULL |
| `email` | TEXT | Indirizzo email | UNIQUE |
| `telefono` | TEXT | Numero di telefono principale | NOT NULL |
| `telefono_secondario` | TEXT | Numero di telefono secondario | NULL |
| `via` | TEXT | Via di residenza | NULL |
| `numero_civico` | TEXT | Numero civico | NULL |
| `citta` | TEXT | Città di residenza | NULL |
| `cap` | TEXT | Codice Avviamento Postale | NULL |
| `provincia` | TEXT | Sigla provincia (es. MI, RM) | NULL |
| `note` | TEXT | Note aggiuntive sul cliente | NULL |
| `data_registrazione` | TIMESTAMP | Data di registrazione nel sistema | DEFAULT CURRENT_TIMESTAMP |
| `attivo` | BOOLEAN | Indica se il cliente è attivo | DEFAULT 1 |

**Indici:**
- `idx_clienti_email` su campo `email` per ricerche rapide

---

### 2. **TIPI_APPUNTAMENTO**

Definisce le diverse tipologie di appuntamenti disponibili.

| Campo | Tipo | Descrizione | Vincoli |
|-------|------|-------------|---------|
| `id_tipo` | INTEGER | Identificativo univoco del tipo | PRIMARY KEY, AUTOINCREMENT |
| `nome_tipo` | TEXT | Nome del tipo di appuntamento | NOT NULL, UNIQUE |
| `descrizione` | TEXT | Descrizione dettagliata | NULL |
| `durata_minuti` | INTEGER | Durata standard in minuti | DEFAULT 30 |
| `colore` | TEXT | Colore per visualizzazione calendario (hex) | NULL |

**Esempi di tipi:**
- Consulenza (60 min)
- Visita medica (45 min)
- Controllo (30 min)
- Urgenza (30 min)
- Follow-up (30 min)

---

### 3. **APPUNTAMENTI**

Tabella principale che gestisce tutti gli appuntamenti del calendario.

| Campo | Tipo | Descrizione | Vincoli |
|-------|------|-------------|---------|
| `id_appuntamento` | INTEGER | Identificativo univoco appuntamento | PRIMARY KEY, AUTOINCREMENT |
| `id_cliente` | INTEGER | Riferimento al cliente | NOT NULL, FOREIGN KEY → clienti(id_cliente) |
| `id_tipo` | INTEGER | Riferimento al tipo di appuntamento | FOREIGN KEY → tipi_appuntamento(id_tipo) |
| `data_appuntamento` | DATE | Data dell'appuntamento | NOT NULL |
| `ora_inizio` | TIME | Ora di inizio (formato HH:MM) | NOT NULL |
| `ora_fine` | TIME | Ora di fine (formato HH:MM) | NOT NULL |
| `titolo` | TEXT | Titolo/oggetto dell'appuntamento | NOT NULL |
| `descrizione` | TEXT | Descrizione dettagliata | NULL |
| `urgente` | BOOLEAN | Flag per appuntamenti urgenti 🚨 | DEFAULT 0 |
| `stato` | TEXT | Stato dell'appuntamento | DEFAULT 'confermato' |
| `luogo` | TEXT | Luogo dell'appuntamento | NULL |
| `note` | TEXT | Note aggiuntive | NULL |
| `data_creazione` | TIMESTAMP | Data di creazione dell'appuntamento | DEFAULT CURRENT_TIMESTAMP |
| `data_modifica` | TIMESTAMP | Data ultima modifica | DEFAULT CURRENT_TIMESTAMP |
| `promemoria_inviato` | BOOLEAN | Flag invio promemoria | DEFAULT 0 |

**Stati possibili:**
- `confermato`: Appuntamento confermato
- `completato`: Appuntamento concluso
- `cancellato`: Appuntamento cancellato
- `in_attesa`: In attesa di conferma
- `non_presentato`: Cliente non si è presentato

**Indici:**
- `idx_appuntamenti_data` su campo `data_appuntamento` per ricerche per data
- `idx_appuntamenti_cliente` su campo `id_cliente` per ricerche per cliente

---

### 4. **STORICO_MODIFICHE**

Traccia tutte le modifiche effettuate agli appuntamenti per audit trail.

| Campo | Tipo | Descrizione | Vincoli |
|-------|------|-------------|---------|
| `id_modifica` | INTEGER | Identificativo univoco modifica | PRIMARY KEY, AUTOINCREMENT |
| `id_appuntamento` | INTEGER | Riferimento all'appuntamento | NOT NULL, FOREIGN KEY → appuntamenti(id_appuntamento) |
| `tipo_modifica` | TEXT | Tipo di modifica effettuata | NOT NULL |
| `descrizione_modifica` | TEXT | Descrizione della modifica | NULL |
| `data_modifica` | TIMESTAMP | Data e ora della modifica | DEFAULT CURRENT_TIMESTAMP |

**Esempi di modifiche:**
- Creazione appuntamento
- Modifica orario
- Cambio stato
- Cancellazione

---

## 🔗 Relazioni tra Tabelle

```
CLIENTI (1) ─────< (N) APPUNTAMENTI
                         │
                         │ (N)
                         │
                         ▼
                    TIPI_APPUNTAMENTO (1)
                         
APPUNTAMENTI (1) ─────< (N) STORICO_MODIFICHE
```

### Relazioni dettagliate:

1. **CLIENTI → APPUNTAMENTI** (1:N)
   - Un cliente può avere molti appuntamenti
   - Ogni appuntamento appartiene a un solo cliente
   - Chiave estera: `appuntamenti.id_cliente` → `clienti.id_cliente`

2. **TIPI_APPUNTAMENTO → APPUNTAMENTI** (1:N)
   - Un tipo può essere associato a molti appuntamenti
   - Ogni appuntamento ha un tipo specifico
   - Chiave estera: `appuntamenti.id_tipo` → `tipi_appuntamento.id_tipo`

3. **APPUNTAMENTI → STORICO_MODIFICHE** (1:N)
   - Un appuntamento può avere molte modifiche
   - Ogni modifica si riferisce a un solo appuntamento
   - Chiave estera: `storico_modifiche.id_appuntamento` → `appuntamenti.id_appuntamento`

---

## 🎯 Funzionalità Principali

### ✅ Gestione Completa Clienti
- Dati anagrafici completi
- Doppio numero di telefono
- Indirizzo completo (via, civico, città, CAP, provincia)
- Note personalizzate
- Tracking data registrazione

### ✅ Calendario Flessibile
- Data e orario preciso (inizio/fine)
- Classificazione per tipo di appuntamento
- Flag urgenza per prioritizzazione
- Stati multipli per workflow
- Note e descrizioni dettagliate

### ✅ Categorizzazione Appuntamenti
- Tipologie predefinite personalizzabili
- Durata standard configurabile
- Codifica colori per visualizzazione

### ✅ Audit Trail
- Tracciamento modifiche
- Storico completo operazioni
- Timestamp automatici

---

## 📈 Query Utili

### Appuntamenti del giorno
```sql
SELECT a.*, c.nome, c.cognome, c.telefono
FROM appuntamenti a
JOIN clienti c ON a.id_cliente = c.id_cliente
WHERE a.data_appuntamento = DATE('now')
ORDER BY a.ora_inizio;
```

### Appuntamenti urgenti in arrivo
```sql
SELECT a.*, c.nome, c.cognome, c.telefono
FROM appuntamenti a
JOIN clienti c ON a.id_cliente = c.id_cliente
WHERE a.urgente = 1 
  AND a.data_appuntamento >= DATE('now')
  AND a.stato = 'confermato'
ORDER BY a.data_appuntamento, a.ora_inizio;
```

### Storico cliente
```sql
SELECT a.*
FROM appuntamenti a
WHERE a.id_cliente = ?
ORDER BY a.data_appuntamento DESC, a.ora_inizio DESC;
```

### Slot liberi del giorno
```sql
SELECT time('08:00') as ora_inizio, time('09:00') as ora_fine
WHERE NOT EXISTS (
    SELECT 1 FROM appuntamenti 
    WHERE data_appuntamento = DATE('now')
    AND ora_inizio < time('09:00')
    AND ora_fine > time('08:00')
);
```

---

## 🚀 Utilizzo

### Creazione Database
```bash
python calendario_prenotazioni.py
```

Questo comando:
1. Crea il file `calendario_prenotazioni.db`
2. Genera tutte le tabelle e gli indici
3. Inserisce dati di esempio
4. Mostra statistiche iniziali

### Output Atteso
- ✓ Database e tabelle creati
- ✓ 8 clienti inseriti
- ✓ 5 tipi di appuntamento
- ✓ ~60-100 appuntamenti di esempio
- ✓ Statistiche complete

---

## 🔒 Vincoli di Integrità

- **Email univoca** per ogni cliente
- **Stati appuntamento** vincolati a valori predefiniti
- **Foreign keys** per garantire integrità referenziale
- **NOT NULL** su campi obbligatori
- **Default values** per campi timestamp e flag booleani

---

## 💡 Estensioni Future Possibili

- Tabella `operatori` per gestire chi effettua gli appuntamenti
- Tabella `servizi` per dettagliare i servizi offerti
- Tabella `pagamenti` per tracciare i pagamenti
- Tabella `promemoria` per gestire invio notifiche
- Sistema di ricorrenza per appuntamenti ripetuti
- Gestione sale/risorse disponibili
- Integration con calendari esterni (Google Calendar, Outlook)

---

## 📝 Note Tecniche

- **Database Engine**: SQLite 3
- **Encoding**: UTF-8
- **Formato Date**: ISO 8601 (YYYY-MM-DD)
- **Formato Orari**: HH:MM (24h)
- **Formato Timestamp**: CURRENT_TIMESTAMP (UTC)

---

**Versione**: 1.0  
**Data Creazione**: 29 Novembre 2025  
**Autore**: Sistema Gestione Prenotazioni
