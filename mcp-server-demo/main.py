"""
MCP Server per Gestione Calendario Prenotazioni
Sistema completo di gestione appuntamenti con database SQLite
"""

from mcp.server.fastmcp import FastMCP
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

# Crea il server MCP
mcp = FastMCP("CalendarioPrenotazioni", json_response=True)

# Path del database
DB_PATH = "calendario_prenotazioni.db"


def get_db_connection():
    """Crea una connessione al database"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Per accedere ai campi per nome
    return conn


# ============= TOOLS: GESTIONE CLIENTI =============

@mcp.tool()
def create_client(
    nome: str,
    cognome: str,
    telefono: str,
    email: str = None,
    telefono_secondario: str = None,
    via: str = None,
    numero_civico: str = None,
    citta: str = None,
    cap: str = None,
    provincia: str = None,
    note: str = None
) -> dict:
    """Crea un nuovo cliente nel sistema
    
    Args:
        nome: Nome del cliente (richiesto)
        cognome: Cognome del cliente (richiesto)
        telefono: Numero di telefono principale (richiesto)
        email: Indirizzo email (opzionale)
        telefono_secondario: Numero di telefono secondario (opzionale)
        via: Via di residenza (opzionale)
        numero_civico: Numero civico (opzionale)
        citta: Città di residenza (opzionale)
        cap: Codice Avviamento Postale (opzionale)
        provincia: Sigla provincia, es. MI, RM (opzionale)
        note: Note aggiuntive sul cliente (opzionale)
    
    Returns:
        Dizionario con i dati del cliente creato
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO clienti (nome, cognome, email, telefono, telefono_secondario, 
                               via, numero_civico, citta, cap, provincia, note)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (nome, cognome, email, telefono, telefono_secondario, via, 
              numero_civico, citta, cap, provincia, note))
        
        cliente_id = cursor.lastrowid
        conn.commit()
        
        # Recupera il cliente appena creato
        cursor.execute('SELECT * FROM clienti WHERE id_cliente = ?', (cliente_id,))
        cliente = dict(cursor.fetchone())
        conn.close()
        
        return {
            "success": True,
            "message": f"Cliente {nome} {cognome} creato con successo",
            "cliente": cliente
        }
    except sqlite3.IntegrityError as e:
        return {"success": False, "error": f"Email già esistente: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def search_clients(query: str = None, citta: str = None, attivo: bool = True) -> list:
    """Cerca clienti nel database
    
    Args:
        query: Cerca per nome, cognome o email (opzionale)
        citta: Filtra per città (opzionale)
        attivo: Mostra solo clienti attivi (default: True)
    
    Returns:
        Lista di clienti che corrispondono ai criteri
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        sql = 'SELECT * FROM clienti WHERE 1=1'
        params = []
        
        if attivo is not None:
            sql += ' AND attivo = ?'
            params.append(1 if attivo else 0)
        
        if query:
            sql += ' AND (nome LIKE ? OR cognome LIKE ? OR email LIKE ?)'
            pattern = f'%{query}%'
            params.extend([pattern, pattern, pattern])
        
        if citta:
            sql += ' AND citta LIKE ?'
            params.append(f'%{citta}%')
        
        sql += ' ORDER BY cognome, nome'
        
        cursor.execute(sql, params)
        clienti = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return {
            "success": True,
            "count": len(clienti),
            "clienti": clienti
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_client_details(id_cliente: int) -> dict:
    """Ottieni i dettagli completi di un cliente
    
    Args:
        id_cliente: ID del cliente
    
    Returns:
        Dettagli completi del cliente incluso storico appuntamenti
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Dati cliente
        cursor.execute('SELECT * FROM clienti WHERE id_cliente = ?', (id_cliente,))
        cliente = cursor.fetchone()
        
        if not cliente:
            conn.close()
            return {"success": False, "error": "Cliente non trovato"}
        
        # Storico appuntamenti
        cursor.execute('''
            SELECT a.*, t.nome_tipo
            FROM appuntamenti a
            LEFT JOIN tipi_appuntamento t ON a.id_tipo = t.id_tipo
            WHERE a.id_cliente = ?
            ORDER BY a.data_appuntamento DESC, a.ora_inizio DESC
            LIMIT 20
        ''', (id_cliente,))
        
        appuntamenti = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return {
            "success": True,
            "cliente": dict(cliente),
            "storico_appuntamenti": appuntamenti,
            "totale_appuntamenti": len(appuntamenti)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============= TOOLS: GESTIONE APPUNTAMENTI =============

@mcp.tool()
def create_appointment(
    id_cliente: int,
    data_appuntamento: str,
    ora_inizio: str,
    titolo: str,
    id_tipo: int = None,
    durata_minuti: int = 30,
    descrizione: str = None,
    urgente: bool = False,
    luogo: str = "Studio Principale",
    note: str = None
) -> dict:
    """Crea un nuovo appuntamento nel calendario
    
    Args:
        id_cliente: ID del cliente (richiesto)
        data_appuntamento: Data in formato YYYY-MM-DD (richiesto)
        ora_inizio: Ora di inizio in formato HH:MM (richiesto)
        titolo: Titolo dell'appuntamento (richiesto)
        id_tipo: ID del tipo di appuntamento (opzionale)
        durata_minuti: Durata in minuti (default: 30)
        descrizione: Descrizione dettagliata (opzionale)
        urgente: Flag appuntamento urgente (default: False)
        luogo: Luogo dell'appuntamento (default: Studio Principale)
        note: Note aggiuntive (opzionale)
    
    Returns:
        Dettagli dell'appuntamento creato
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verifica che il cliente esista
        cursor.execute('SELECT id_cliente FROM clienti WHERE id_cliente = ?', (id_cliente,))
        if not cursor.fetchone():
            conn.close()
            return {"success": False, "error": "Cliente non trovato"}
        
        # Calcola ora fine
        ora_dt = datetime.strptime(ora_inizio, '%H:%M')
        ora_fine_dt = ora_dt + timedelta(minutes=durata_minuti)
        ora_fine = ora_fine_dt.strftime('%H:%M')
        
        # Verifica sovrapposizioni
        cursor.execute('''
            SELECT id_appuntamento, titolo 
            FROM appuntamenti
            WHERE data_appuntamento = ?
            AND stato NOT IN ('cancellato', 'non_presentato')
            AND (
                (ora_inizio < ? AND ora_fine > ?) OR
                (ora_inizio < ? AND ora_fine > ?) OR
                (ora_inizio >= ? AND ora_fine <= ?)
            )
        ''', (data_appuntamento, ora_fine, ora_inizio, ora_fine, ora_inizio, ora_inizio, ora_fine))
        
        conflitto = cursor.fetchone()
        if conflitto:
            conn.close()
            return {
                "success": False,
                "error": f"Conflitto con appuntamento esistente: {conflitto['titolo']}"
            }
        
        # Inserisci appuntamento
        cursor.execute('''
            INSERT INTO appuntamenti 
            (id_cliente, id_tipo, data_appuntamento, ora_inizio, ora_fine, 
             titolo, descrizione, urgente, stato, luogo, note)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'confermato', ?, ?)
        ''', (id_cliente, id_tipo, data_appuntamento, ora_inizio, ora_fine,
              titolo, descrizione, 1 if urgente else 0, luogo, note))
        
        appuntamento_id = cursor.lastrowid
        
        # Registra nello storico
        cursor.execute('''
            INSERT INTO storico_modifiche (id_appuntamento, tipo_modifica, descrizione_modifica)
            VALUES (?, 'creazione', 'Appuntamento creato')
        ''', (appuntamento_id,))
        
        conn.commit()
        
        # Recupera appuntamento creato con dettagli cliente
        cursor.execute('''
            SELECT a.*, c.nome, c.cognome, c.telefono, t.nome_tipo
            FROM appuntamenti a
            JOIN clienti c ON a.id_cliente = c.id_cliente
            LEFT JOIN tipi_appuntamento t ON a.id_tipo = t.id_tipo
            WHERE a.id_appuntamento = ?
        ''', (appuntamento_id,))
        
        appuntamento = dict(cursor.fetchone())
        conn.close()
        
        return {
            "success": True,
            "message": f"Appuntamento creato per {appuntamento['nome']} {appuntamento['cognome']}",
            "appuntamento": appuntamento
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def list_appointments(
    data_da: str = None,
    data_a: str = None,
    stato: str = None,
    urgente: bool = None,
    id_cliente: int = None
) -> dict:
    """Elenca appuntamenti con filtri opzionali
    
    Args:
        data_da: Data iniziale formato YYYY-MM-DD (default: oggi)
        data_a: Data finale formato YYYY-MM-DD (opzionale)
        stato: Filtra per stato: confermato, completato, cancellato, in_attesa, non_presentato
        urgente: Filtra solo appuntamenti urgenti (opzionale)
        id_cliente: Filtra per cliente specifico (opzionale)
    
    Returns:
        Lista di appuntamenti con dettagli cliente
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        sql = '''
            SELECT a.*, c.nome, c.cognome, c.telefono, t.nome_tipo, t.colore
            FROM appuntamenti a
            JOIN clienti c ON a.id_cliente = c.id_cliente
            LEFT JOIN tipi_appuntamento t ON a.id_tipo = t.id_tipo
            WHERE 1=1
        '''
        params = []
        
        if data_da:
            sql += ' AND a.data_appuntamento >= ?'
            params.append(data_da)
        else:
            # Default: da oggi
            sql += ' AND a.data_appuntamento >= DATE("now")'
        
        if data_a:
            sql += ' AND a.data_appuntamento <= ?'
            params.append(data_a)
        
        if stato:
            sql += ' AND a.stato = ?'
            params.append(stato)
        
        if urgente is not None:
            sql += ' AND a.urgente = ?'
            params.append(1 if urgente else 0)
        
        if id_cliente:
            sql += ' AND a.id_cliente = ?'
            params.append(id_cliente)
        
        sql += ' ORDER BY a.data_appuntamento, a.ora_inizio'
        
        cursor.execute(sql, params)
        appuntamenti = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return {
            "success": True,
            "count": len(appuntamenti),
            "appuntamenti": appuntamenti
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def update_appointment(
    id_appuntamento: int,
    data_appuntamento: str = None,
    ora_inizio: str = None,
    durata_minuti: int = None,
    titolo: str = None,
    descrizione: str = None,
    stato: str = None,
    urgente: bool = None,
    note: str = None
) -> dict:
    """Aggiorna un appuntamento esistente
    
    Args:
        id_appuntamento: ID dell'appuntamento da modificare (richiesto)
        data_appuntamento: Nuova data formato YYYY-MM-DD (opzionale)
        ora_inizio: Nuovo orario inizio formato HH:MM (opzionale)
        durata_minuti: Nuova durata in minuti (opzionale)
        titolo: Nuovo titolo (opzionale)
        descrizione: Nuova descrizione (opzionale)
        stato: Nuovo stato (confermato, completato, cancellato, in_attesa, non_presentato)
        urgente: Flag urgenza (opzionale)
        note: Nuove note (opzionale)
    
    Returns:
        Appuntamento aggiornato
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verifica esistenza
        cursor.execute('SELECT * FROM appuntamenti WHERE id_appuntamento = ?', (id_appuntamento,))
        app_esistente = cursor.fetchone()
        
        if not app_esistente:
            conn.close()
            return {"success": False, "error": "Appuntamento non trovato"}
        
        modifiche = []
        updates = []
        params = []
        
        if data_appuntamento:
            updates.append('data_appuntamento = ?')
            params.append(data_appuntamento)
            modifiche.append(f"Data modificata in {data_appuntamento}")
        
        if ora_inizio:
            updates.append('ora_inizio = ?')
            params.append(ora_inizio)
            
            # Ricalcola ora fine se cambia l'inizio
            if durata_minuti:
                ora_dt = datetime.strptime(ora_inizio, '%H:%M')
                ora_fine = (ora_dt + timedelta(minutes=durata_minuti)).strftime('%H:%M')
            else:
                # Mantieni la stessa durata
                vecchia_fine = datetime.strptime(app_esistente['ora_fine'], '%H:%M')
                vecchio_inizio = datetime.strptime(app_esistente['ora_inizio'], '%H:%M')
                durata = (vecchia_fine - vecchio_inizio).total_seconds() / 60
                ora_dt = datetime.strptime(ora_inizio, '%H:%M')
                ora_fine = (ora_dt + timedelta(minutes=durata)).strftime('%H:%M')
            
            updates.append('ora_fine = ?')
            params.append(ora_fine)
            modifiche.append(f"Orario modificato: {ora_inizio} - {ora_fine}")
        
        if titolo:
            updates.append('titolo = ?')
            params.append(titolo)
            modifiche.append("Titolo modificato")
        
        if descrizione is not None:
            updates.append('descrizione = ?')
            params.append(descrizione)
            modifiche.append("Descrizione aggiornata")
        
        if stato:
            updates.append('stato = ?')
            params.append(stato)
            modifiche.append(f"Stato cambiato in {stato}")
        
        if urgente is not None:
            updates.append('urgente = ?')
            params.append(1 if urgente else 0)
            modifiche.append(f"Urgenza: {'SI' if urgente else 'NO'}")
        
        if note is not None:
            updates.append('note = ?')
            params.append(note)
        
        if not updates:
            conn.close()
            return {"success": False, "error": "Nessuna modifica specificata"}
        
        # Aggiorna timestamp modifica
        updates.append('data_modifica = CURRENT_TIMESTAMP')
        
        # Esegui update
        params.append(id_appuntamento)
        sql = f"UPDATE appuntamenti SET {', '.join(updates)} WHERE id_appuntamento = ?"
        cursor.execute(sql, params)
        
        # Registra nello storico
        descrizione_modifica = '; '.join(modifiche)
        cursor.execute('''
            INSERT INTO storico_modifiche (id_appuntamento, tipo_modifica, descrizione_modifica)
            VALUES (?, 'modifica', ?)
        ''', (id_appuntamento, descrizione_modifica))
        
        conn.commit()
        
        # Recupera appuntamento aggiornato
        cursor.execute('''
            SELECT a.*, c.nome, c.cognome, c.telefono
            FROM appuntamenti a
            JOIN clienti c ON a.id_cliente = c.id_cliente
            WHERE a.id_appuntamento = ?
        ''', (id_appuntamento,))
        
        appuntamento = dict(cursor.fetchone())
        conn.close()
        
        return {
            "success": True,
            "message": "Appuntamento aggiornato con successo",
            "modifiche": modifiche,
            "appuntamento": appuntamento
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def delete_appointment(id_appuntamento: int, motivo: str = None) -> dict:
    """Cancella (segna come cancellato) un appuntamento
    
    Args:
        id_appuntamento: ID dell'appuntamento da cancellare (richiesto)
        motivo: Motivo della cancellazione (opzionale)
    
    Returns:
        Conferma cancellazione
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verifica esistenza
        cursor.execute('''
            SELECT a.*, c.nome, c.cognome
            FROM appuntamenti a
            JOIN clienti c ON a.id_cliente = c.id_cliente
            WHERE a.id_appuntamento = ?
        ''', (id_appuntamento,))
        
        app = cursor.fetchone()
        if not app:
            conn.close()
            return {"success": False, "error": "Appuntamento non trovato"}
        
        # Segna come cancellato invece di eliminare
        cursor.execute('''
            UPDATE appuntamenti 
            SET stato = 'cancellato', data_modifica = CURRENT_TIMESTAMP
            WHERE id_appuntamento = ?
        ''', (id_appuntamento,))
        
        # Registra nello storico
        descrizione = f"Appuntamento cancellato. Motivo: {motivo}" if motivo else "Appuntamento cancellato"
        cursor.execute('''
            INSERT INTO storico_modifiche (id_appuntamento, tipo_modifica, descrizione_modifica)
            VALUES (?, 'cancellazione', ?)
        ''', (id_appuntamento, descrizione))
        
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "message": f"Appuntamento di {app['nome']} {app['cognome']} del {app['data_appuntamento']} cancellato",
            "appuntamento_cancellato": dict(app)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def search_appointments(query: str) -> dict:
    """Cerca appuntamenti per parola chiave
    
    Args:
        query: Termine di ricerca (cerca in titolo, descrizione, note, nome cliente)
    
    Returns:
        Lista di appuntamenti che corrispondono alla ricerca
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        pattern = f'%{query}%'
        cursor.execute('''
            SELECT a.*, c.nome, c.cognome, c.telefono, t.nome_tipo
            FROM appuntamenti a
            JOIN clienti c ON a.id_cliente = c.id_cliente
            LEFT JOIN tipi_appuntamento t ON a.id_tipo = t.id_tipo
            WHERE a.titolo LIKE ? 
               OR a.descrizione LIKE ?
               OR a.note LIKE ?
               OR c.nome LIKE ?
               OR c.cognome LIKE ?
            ORDER BY a.data_appuntamento DESC, a.ora_inizio DESC
        ''', (pattern, pattern, pattern, pattern, pattern))
        
        risultati = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return {
            "success": True,
            "query": query,
            "count": len(risultati),
            "risultati": risultati
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_daily_schedule(data: str = None) -> dict:
    """Ottieni il programma completo di una giornata
    
    Args:
        data: Data in formato YYYY-MM-DD (default: oggi)
    
    Returns:
        Programma completo della giornata con tutti gli appuntamenti
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if not data:
            data = datetime.now().strftime('%Y-%m-%d')
        
        cursor.execute('''
            SELECT a.*, c.nome, c.cognome, c.telefono, t.nome_tipo, t.colore
            FROM appuntamenti a
            JOIN clienti c ON a.id_cliente = c.id_cliente
            LEFT JOIN tipi_appuntamento t ON a.id_tipo = t.id_tipo
            WHERE a.data_appuntamento = ?
            AND a.stato NOT IN ('cancellato')
            ORDER BY a.ora_inizio
        ''', (data,))
        
        appuntamenti = [dict(row) for row in cursor.fetchall()]
        
        # Statistiche giornata
        urgenti = sum(1 for a in appuntamenti if a['urgente'])
        confermati = sum(1 for a in appuntamenti if a['stato'] == 'confermato')
        completati = sum(1 for a in appuntamenti if a['stato'] == 'completato')
        
        conn.close()
        
        return {
            "success": True,
            "data": data,
            "totale_appuntamenti": len(appuntamenti),
            "statistiche": {
                "urgenti": urgenti,
                "confermati": confermati,
                "completati": completati
            },
            "appuntamenti": appuntamenti
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============= RESOURCES =============

@mcp.resource("appointment://{id_appuntamento}")
def get_appointment_resource(id_appuntamento: str) -> str:
    """Risorsa per visualizzare i dettagli formattati di un appuntamento
    
    Args:
        id_appuntamento: ID dell'appuntamento
    
    Returns:
        Dettagli formattati dell'appuntamento
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT a.*, c.nome, c.cognome, c.telefono, c.email, t.nome_tipo
            FROM appuntamenti a
            JOIN clienti c ON a.id_cliente = c.id_cliente
            LEFT JOIN tipi_appuntamento t ON a.id_tipo = t.id_tipo
            WHERE a.id_appuntamento = ?
        ''', (id_appuntamento,))
        
        app = cursor.fetchone()
        
        if not app:
            conn.close()
            return f"❌ Appuntamento {id_appuntamento} non trovato"
        
        app = dict(app)
        
        # Emoji per stato
        stato_emoji = {
            'confermato': '✅',
            'completato': '✔️',
            'cancellato': '❌',
            'in_attesa': '⏳',
            'non_presentato': '⚠️'
        }
        
        urgente_flag = " 🚨 URGENTE" if app['urgente'] else ""
        
        result = f"""
{stato_emoji.get(app['stato'], '📅')} APPUNTAMENTO #{app['id_appuntamento']}{urgente_flag}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 DETTAGLI
   Titolo: {app['titolo']}
   Tipo: {app['nome_tipo'] or 'Non specificato'}
   Stato: {app['stato'].upper()}

📅 DATA E ORA
   Data: {app['data_appuntamento']}
   Orario: {app['ora_inizio']} - {app['ora_fine']}
   Luogo: {app['luogo'] or 'Non specificato'}

👤 CLIENTE
   Nome: {app['nome']} {app['cognome']}
   Telefono: {app['telefono']}
   Email: {app['email'] or 'Non disponibile'}

📝 NOTE
   {app['descrizione'] or 'Nessuna descrizione'}
   {app['note'] or ''}

⏰ INFO SISTEMA
   Creato: {app['data_creazione']}
   Modificato: {app['data_modifica']}
        """.strip()
        
        conn.close()
        return result
        
    except Exception as e:
        return f"❌ Errore: {str(e)}"


@mcp.resource("schedule://{data}")
def get_schedule_resource(data: str) -> str:
    """Risorsa per visualizzare il programma formattato di una giornata
    
    Args:
        data: Data in formato YYYY-MM-DD
    
    Returns:
        Programma formattato della giornata
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT a.*, c.nome, c.cognome, c.telefono, t.nome_tipo
            FROM appuntamenti a
            JOIN clienti c ON a.id_cliente = c.id_cliente
            LEFT JOIN tipi_appuntamento t ON a.id_tipo = t.id_tipo
            WHERE a.data_appuntamento = ?
            AND a.stato NOT IN ('cancellato')
            ORDER BY a.ora_inizio
        ''', (data,))
        
        appuntamenti = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        if not appuntamenti:
            return f"📅 Nessun appuntamento per il {data}"
        
        result = f"""
📅 PROGRAMMA DEL {data}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Totale appuntamenti: {len(appuntamenti)}

"""
        
        for app in appuntamenti:
            urgente_flag = " 🚨" if app['urgente'] else ""
            result += f"""
⏰ {app['ora_inizio']} - {app['ora_fine']}{urgente_flag}
   👤 {app['nome']} {app['cognome']} ({app['telefono']})
   📋 {app['titolo']}
   📊 Stato: {app['stato'].upper()}
"""
        
        return result.strip()
        
    except Exception as e:
        return f"❌ Errore: {str(e)}"


@mcp.resource("client://{id_cliente}")
def get_client_resource(id_cliente: str) -> str:
    """Risorsa per visualizzare i dettagli formattati di un cliente
    
    Args:
        id_cliente: ID del cliente
    
    Returns:
        Dettagli formattati del cliente con storico
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM clienti WHERE id_cliente = ?', (id_cliente,))
        cliente = cursor.fetchone()
        
        if not cliente:
            conn.close()
            return f"❌ Cliente {id_cliente} non trovato"
        
        cliente = dict(cliente)
        
        # Statistiche appuntamenti
        cursor.execute('''
            SELECT 
                COUNT(*) as totale,
                SUM(CASE WHEN stato = 'completato' THEN 1 ELSE 0 END) as completati,
                SUM(CASE WHEN stato = 'confermato' THEN 1 ELSE 0 END) as confermati,
                SUM(CASE WHEN stato = 'cancellato' THEN 1 ELSE 0 END) as cancellati
            FROM appuntamenti
            WHERE id_cliente = ?
        ''', (id_cliente,))
        
        stats = dict(cursor.fetchone())
        
        # Prossimi appuntamenti
        cursor.execute('''
            SELECT data_appuntamento, ora_inizio, titolo, stato
            FROM appuntamenti
            WHERE id_cliente = ? AND data_appuntamento >= DATE('now')
            ORDER BY data_appuntamento, ora_inizio
            LIMIT 5
        ''', (id_cliente,))
        
        prossimi = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        indirizzo = ""
        if cliente['via']:
            indirizzo = f"\n   {cliente['via']} {cliente['numero_civico'] or ''}"
            if cliente['citta']:
                indirizzo += f"\n   {cliente['cap'] or ''} {cliente['citta']} ({cliente['provincia'] or ''})"
        
        result = f"""
👤 CLIENTE #{cliente['id_cliente']} - {cliente['nome']} {cliente['cognome']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📞 CONTATTI
   Telefono: {cliente['telefono']}
   {"Tel. secondario: " + cliente['telefono_secondario'] if cliente['telefono_secondario'] else ''}
   Email: {cliente['email'] or 'Non disponibile'}{indirizzo}

📊 STATISTICHE APPUNTAMENTI
   Totale: {stats['totale']}
   Completati: {stats['completati']}
   Confermati: {stats['confermati']}
   Cancellati: {stats['cancellati']}
"""
        
        if prossimi:
            result += "\n📅 PROSSIMI APPUNTAMENTI\n"
            for app in prossimi:
                result += f"   • {app['data_appuntamento']} {app['ora_inizio']} - {app['titolo']} ({app['stato']})\n"
        
        if cliente['note']:
            result += f"\n📝 NOTE\n   {cliente['note']}\n"
        
        result += f"\n⏰ Registrato il: {cliente['data_registrazione']}"
        
        return result.strip()
        
    except Exception as e:
        return f"❌ Errore: {str(e)}"


# ============= PROMPTS =============

@mcp.prompt()
def daily_briefing_prompt(data: str = None) -> str:
    """Genera un prompt per creare il briefing giornaliero
    
    Args:
        data: Data in formato YYYY-MM-DD (default: oggi)
    
    Returns:
        Prompt per generare briefing completo
    """
    try:
        if not data:
            data = datetime.now().strftime('%Y-%m-%d')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT a.*, c.nome, c.cognome, c.telefono, t.nome_tipo
            FROM appuntamenti a
            JOIN clienti c ON a.id_cliente = c.id_cliente
            LEFT JOIN tipi_appuntamento t ON a.id_tipo = t.id_tipo
            WHERE a.data_appuntamento = ?
            AND a.stato NOT IN ('cancellato')
            ORDER BY a.ora_inizio
        ''', (data,))
        
        appuntamenti = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        urgenti = [a for a in appuntamenti if a['urgente']]
        confermati = [a for a in appuntamenti if a['stato'] == 'confermato']
        
        prompt = f"""
Crea un briefing giornaliero professionale e organizzato per il {data}.

📊 DATI:
- Totale appuntamenti: {len(appuntamenti)}
- Appuntamenti urgenti: {len(urgenti)}
- Appuntamenti confermati: {len(confermati)}

📋 ELENCO APPUNTAMENTI:
"""
        
        for app in appuntamenti:
            urgente_flag = "🚨 URGENTE - " if app['urgente'] else ""
            prompt += f"\n- {app['ora_inizio']}-{app['ora_fine']}: {urgente_flag}{app['nome']} {app['cognome']} - {app['titolo']}"
            if app['descrizione']:
                prompt += f"\n  Dettagli: {app['descrizione']}"
        
        prompt += """

Il briefing deve includere:
1. Saluto e panoramica della giornata
2. Lista cronologica degli appuntamenti con:
   - Orario
   - Nome cliente
   - Tipo di appuntamento
   - Note importanti o urgenze
3. Consigli per ottimizzare la giornata
4. Eventuali alert per appuntamenti urgenti o ravvicinati
5. Chiusura motivante

Usa un tono professionale, organizzato e chiaro. Usa emoji per migliorare la leggibilità.
        """
        
        return prompt.strip()
        
    except Exception as e:
        return f"Errore nel generare il prompt: {str(e)}"


@mcp.prompt()
def appointment_reminder_prompt(id_appuntamento: int) -> str:
    """Genera un prompt per creare un messaggio di promemoria
    
    Args:
        id_appuntamento: ID dell'appuntamento
    
    Returns:
        Prompt per generare messaggio di reminder
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT a.*, c.nome, c.cognome, c.telefono, t.nome_tipo
            FROM appuntamenti a
            JOIN clienti c ON a.id_cliente = c.id_cliente
            LEFT JOIN tipi_appuntamento t ON a.id_tipo = t.id_tipo
            WHERE a.id_appuntamento = ?
        ''', (id_appuntamento,))
        
        app = cursor.fetchone()
        conn.close()
        
        if not app:
            return f"Appuntamento {id_appuntamento} non trovato"
        
        app = dict(app)
        
        return f"""
Crea un messaggio di promemoria professionale per questo appuntamento:

👤 Cliente: {app['nome']} {app['cognome']}
📅 Data: {app['data_appuntamento']}
⏰ Orario: {app['ora_inizio']} - {app['ora_fine']}
📋 Tipo: {app['nome_tipo'] or 'Appuntamento'}
📍 Luogo: {app['luogo']}
{"🚨 APPUNTAMENTO URGENTE" if app['urgente'] else ""}

{f"Descrizione: {app['descrizione']}" if app['descrizione'] else ""}

Il messaggio deve:
1. Essere cortese e professionale
2. Includere data, ora e luogo precisi
3. {"Enfatizzare l'urgenza" if app['urgente'] else "Avere un tono standard"}
4. Includere istruzioni su come confermare o spostare
5. Essere lungo circa 3-4 frasi

Formato ottimale per SMS o email.
        """.strip()
        
    except Exception as e:
        return f"Errore: {str(e)}"


# Run with streamable HTTP transport
if __name__ == "__main__":
    mcp.run(transport="streamable-http")