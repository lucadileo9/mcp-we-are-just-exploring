"""
MCP Server per Gestione Task e Appuntamenti Personali
Sistema di gestione task con priorità, scadenze e difficoltà
"""

from mcp.server.fastmcp import FastMCP
import sqlite3
from datetime import datetime, timedelta
from typing import Optional

# Crea il server MCP
mcp = FastMCP("TaskManager", json_response=True)

# Path del database
DB_PATH = "calendario_prenotazioni.db"


def get_db_connection():
    """Crea una connessione al database"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ============= TOOLS: GESTIONE TASK =============

@mcp.tool()
def create_task(
    titolo: str,
    data_appuntamento: str,
    descrizione: str = None,
    ora_inizio: str = None,
    ora_fine: str = None,
    priorita: str = "media",
    difficolta: int = 5,
    tempo_stimato_ore: float = None,
    id_categoria: int = None,
    urgente: bool = False,
    note: str = None
) -> dict:
    """Crea un nuovo task/appuntamento
    
    Args:
        titolo: Nome del task (richiesto)
        data_appuntamento: Data scadenza formato YYYY-MM-DD (richiesto)
        descrizione: Descrizione dettagliata (opzionale)
        ora_inizio: Ora inizio formato HH:MM (opzionale)
        ora_fine: Ora fine formato HH:MM (opzionale)
        priorita: Priorità - bassa, media, alta, critica (default: media)
        difficolta: Livello di difficoltà da 1 a 10 (default: 5)
        tempo_stimato_ore: Ore stimate per completare (opzionale)
        id_categoria: ID categoria (opzionale)
        urgente: Flag urgenza (default: False)
        note: Note aggiuntive (opzionale)
    
    Returns:
        Dettagli del task creato
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Inserisci task
        cursor.execute('''
            INSERT INTO appuntamenti 
            (titolo, descrizione, data_appuntamento, ora_inizio, ora_fine,
             id_categoria, priorita, difficolta, tempo_stimato_ore, urgente, note, stato)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'da_fare')
        ''', (titolo, descrizione, data_appuntamento, ora_inizio, ora_fine,
              id_categoria, priorita, difficolta, tempo_stimato_ore, 
              1 if urgente else 0, note))
        
        task_id = cursor.lastrowid
        
        # Registra nello storico
        cursor.execute('''
            INSERT INTO storico_modifiche (id_appuntamento, tipo_modifica, descrizione_modifica)
            VALUES (?, 'creazione', 'Task creato')
        ''', (task_id,))
        
        conn.commit()
        
        # Recupera task creato
        cursor.execute('''
            SELECT a.*, c.nome_categoria
            FROM appuntamenti a
            LEFT JOIN categorie c ON a.id_categoria = c.id_categoria
            WHERE a.id_appuntamento = ?
        ''', (task_id,))
        
        task = dict(cursor.fetchone())
        conn.close()
        
        return {
            "success": True,
            "message": f"Task '{titolo}' creato con successo",
            "task": task
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def list_tasks(
    data_da: str = None,
    data_a: str = None,
    stato: str = None,
    priorita: str = None,
    urgente: bool = None,
    categoria: int = None
) -> dict:
    """Elenca task con filtri opzionali
    
    Args:
        data_da: Data iniziale formato YYYY-MM-DD (default: oggi)
        data_a: Data finale formato YYYY-MM-DD (opzionale)
        stato: Filtra per stato - da_fare, in_corso, completato, cancellato, posticipato
        priorita: Filtra per priorità - bassa, media, alta, critica
        urgente: Filtra solo task urgenti (opzionale)
        categoria: ID categoria (opzionale)
    
    Returns:
        Lista di task
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        sql = '''
            SELECT a.*, c.nome_categoria, c.colore
            FROM appuntamenti a
            LEFT JOIN categorie c ON a.id_categoria = c.id_categoria
            WHERE 1=1
        '''
        params = []
        
        if data_da:
            sql += ' AND a.data_appuntamento >= ?'
            params.append(data_da)
        else:
            sql += ' AND a.data_appuntamento >= DATE("now")'
        
        if data_a:
            sql += ' AND a.data_appuntamento <= ?'
            params.append(data_a)
        
        if stato:
            sql += ' AND a.stato = ?'
            params.append(stato)
        
        if priorita:
            sql += ' AND a.priorita = ?'
            params.append(priorita)
        
        if urgente is not None:
            sql += ' AND a.urgente = ?'
            params.append(1 if urgente else 0)
        
        if categoria:
            sql += ' AND a.id_categoria = ?'
            params.append(categoria)
        
        # Ordina per urgenza, priorità, data
        sql += '''
            ORDER BY 
                a.urgente DESC,
                CASE a.priorita
                    WHEN 'critica' THEN 1
                    WHEN 'alta' THEN 2
                    WHEN 'media' THEN 3
                    WHEN 'bassa' THEN 4
                END,
                a.data_appuntamento,
                a.ora_inizio
        '''
        
        cursor.execute(sql, params)
        tasks = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return {
            "success": True,
            "count": len(tasks),
            "tasks": tasks
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def update_task(
    id_task: int,
    titolo: str = None,
    descrizione: str = None,
    data_appuntamento: str = None,
    ora_inizio: str = None,
    ora_fine: str = None,
    priorita: str = None,
    difficolta: int = None,
    tempo_stimato_ore: float = None,
    stato: str = None,
    urgente: bool = None,
    note: str = None
) -> dict:
    """Aggiorna un task esistente
    
    Args:
        id_task: ID del task da modificare (richiesto)
        titolo: Nuovo titolo (opzionale)
        descrizione: Nuova descrizione (opzionale)
        data_appuntamento: Nuova data formato YYYY-MM-DD (opzionale)
        ora_inizio: Nuovo orario inizio formato HH:MM (opzionale)
        ora_fine: Nuovo orario fine formato HH:MM (opzionale)
        priorita: Nuova priorità (opzionale)
        difficolta: Nuova difficoltà 1-10 (opzionale)
        tempo_stimato_ore: Nuovo tempo stimato (opzionale)
        stato: Nuovo stato (opzionale)
        urgente: Flag urgenza (opzionale)
        note: Nuove note (opzionale)
    
    Returns:
        Task aggiornato
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verifica esistenza
        cursor.execute('SELECT * FROM appuntamenti WHERE id_appuntamento = ?', (id_task,))
        if not cursor.fetchone():
            conn.close()
            return {"success": False, "error": "Task non trovato"}
        
        modifiche = []
        updates = []
        params = []
        
        if titolo is not None:
            updates.append('titolo = ?')
            params.append(titolo)
            modifiche.append(f"Titolo aggiornato")
        
        if descrizione is not None:
            updates.append('descrizione = ?')
            params.append(descrizione)
            modifiche.append("Descrizione aggiornata")
        
        if data_appuntamento is not None:
            updates.append('data_appuntamento = ?')
            params.append(data_appuntamento)
            modifiche.append(f"Data modificata: {data_appuntamento}")
        
        if ora_inizio is not None:
            updates.append('ora_inizio = ?')
            params.append(ora_inizio)
            modifiche.append(f"Orario inizio: {ora_inizio}")
        
        if ora_fine is not None:
            updates.append('ora_fine = ?')
            params.append(ora_fine)
            modifiche.append(f"Orario fine: {ora_fine}")
        
        if priorita is not None:
            updates.append('priorita = ?')
            params.append(priorita)
            modifiche.append(f"Priorità: {priorita}")
        
        if difficolta is not None:
            updates.append('difficolta = ?')
            params.append(difficolta)
            modifiche.append(f"Difficoltà: {difficolta}/10")
        
        if tempo_stimato_ore is not None:
            updates.append('tempo_stimato_ore = ?')
            params.append(tempo_stimato_ore)
            modifiche.append(f"Tempo stimato: {tempo_stimato_ore}h")
        
        if stato is not None:
            updates.append('stato = ?')
            params.append(stato)
            modifiche.append(f"Stato: {stato}")
            
            # Se completato, aggiungi timestamp
            if stato == 'completato':
                updates.append('data_completamento = CURRENT_TIMESTAMP')
        
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
        params.append(id_task)
        sql = f"UPDATE appuntamenti SET {', '.join(updates)} WHERE id_appuntamento = ?"
        cursor.execute(sql, params)
        
        # Registra nello storico
        cursor.execute('''
            INSERT INTO storico_modifiche (id_appuntamento, tipo_modifica, descrizione_modifica)
            VALUES (?, 'modifica', ?)
        ''', (id_task, '; '.join(modifiche)))
        
        conn.commit()
        
        # Recupera task aggiornato
        cursor.execute('''
            SELECT a.*, c.nome_categoria
            FROM appuntamenti a
            LEFT JOIN categorie c ON a.id_categoria = c.id_categoria
            WHERE a.id_appuntamento = ?
        ''', (id_task,))
        
        task = dict(cursor.fetchone())
        conn.close()
        
        return {
            "success": True,
            "message": "Task aggiornato con successo",
            "modifiche": modifiche,
            "task": task
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def complete_task(id_task: int) -> dict:
    """Segna un task come completato
    
    Args:
        id_task: ID del task da completare (richiesto)
    
    Returns:
        Task completato
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE appuntamenti 
            SET stato = 'completato', 
                data_completamento = CURRENT_TIMESTAMP,
                data_modifica = CURRENT_TIMESTAMP
            WHERE id_appuntamento = ?
        ''', (id_task,))
        
        if cursor.rowcount == 0:
            conn.close()
            return {"success": False, "error": "Task non trovato"}
        
        cursor.execute('''
            INSERT INTO storico_modifiche (id_appuntamento, tipo_modifica, descrizione_modifica)
            VALUES (?, 'completamento', 'Task completato')
        ''', (id_task,))
        
        conn.commit()
        
        cursor.execute('SELECT * FROM appuntamenti WHERE id_appuntamento = ?', (id_task,))
        task = dict(cursor.fetchone())
        conn.close()
        
        return {
            "success": True,
            "message": f"✅ Task '{task['titolo']}' completato!",
            "task": task
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def delete_task(id_task: int, motivo: str = None) -> dict:
    """Cancella (segna come cancellato) un task
    
    Args:
        id_task: ID del task da cancellare (richiesto)
        motivo: Motivo della cancellazione (opzionale)
    
    Returns:
        Conferma cancellazione
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM appuntamenti WHERE id_appuntamento = ?', (id_task,))
        task = cursor.fetchone()
        
        if not task:
            conn.close()
            return {"success": False, "error": "Task non trovato"}
        
        task = dict(task)
        
        cursor.execute('''
            UPDATE appuntamenti 
            SET stato = 'cancellato', data_modifica = CURRENT_TIMESTAMP
            WHERE id_appuntamento = ?
        ''', (id_task,))
        
        descrizione = f"Task cancellato. Motivo: {motivo}" if motivo else "Task cancellato"
        cursor.execute('''
            INSERT INTO storico_modifiche (id_appuntamento, tipo_modifica, descrizione_modifica)
            VALUES (?, 'cancellazione', ?)
        ''', (id_task, descrizione))
        
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "message": f"Task '{task['titolo']}' del {task['data_appuntamento']} cancellato",
            "task_cancellato": task
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def search_tasks(query: str) -> dict:
    """Cerca task per parola chiave
    
    Args:
        query: Termine di ricerca (cerca in titolo, descrizione, note)
    
    Returns:
        Lista di task che corrispondono alla ricerca
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        pattern = f'%{query}%'
        cursor.execute('''
            SELECT a.*, c.nome_categoria
            FROM appuntamenti a
            LEFT JOIN categorie c ON a.id_categoria = c.id_categoria
            WHERE a.titolo LIKE ? 
               OR a.descrizione LIKE ?
               OR a.note LIKE ?
            ORDER BY a.data_appuntamento DESC
        ''', (pattern, pattern, pattern))
        
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
def get_today_tasks() -> dict:
    """Ottieni tutti i task di oggi
    
    Returns:
        Task di oggi ordinati per priorità e orario
    """
    try:
        oggi = datetime.now().strftime('%Y-%m-%d')
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT a.*, c.nome_categoria, c.colore
            FROM appuntamenti a
            LEFT JOIN categorie c ON a.id_categoria = c.id_categoria
            WHERE a.data_appuntamento = ?
            AND a.stato NOT IN ('completato', 'cancellato')
            ORDER BY 
                a.urgente DESC,
                CASE a.priorita
                    WHEN 'critica' THEN 1
                    WHEN 'alta' THEN 2
                    WHEN 'media' THEN 3
                    WHEN 'bassa' THEN 4
                END,
                a.ora_inizio
        ''', (oggi,))
        
        tasks = [dict(row) for row in cursor.fetchall()]
        
        # Statistiche
        urgenti = sum(1 for t in tasks if t['urgente'])
        critica = sum(1 for t in tasks if t['priorita'] == 'critica')
        alta = sum(1 for t in tasks if t['priorita'] == 'alta')
        
        conn.close()
        
        return {
            "success": True,
            "data": oggi,
            "totale_tasks": len(tasks),
            "statistiche": {
                "urgenti": urgenti,
                "priorita_critica": critica,
                "priorita_alta": alta
            },
            "tasks": tasks
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_categories() -> dict:
    """Ottieni tutte le categorie disponibili
    
    Returns:
        Lista di categorie
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM categorie ORDER BY nome_categoria')
        categorie = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return {
            "success": True,
            "count": len(categorie),
            "categorie": categorie
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============= RESOURCES =============

@mcp.resource("task://{id_task}")
def get_task_resource(id_task: str) -> str:
    """Risorsa per visualizzare i dettagli formattati di un task
    
    Args:
        id_task: ID del task
    
    Returns:
        Dettagli formattati del task
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT a.*, c.nome_categoria
            FROM appuntamenti a
            LEFT JOIN categorie c ON a.id_categoria = c.id_categoria
            WHERE a.id_appuntamento = ?
        ''', (id_task,))
        
        task = cursor.fetchone()
        
        if not task:
            conn.close()
            return f"❌ Task {id_task} non trovato"
        
        task = dict(task)
        
        # Emoji per stato
        stato_emoji = {
            'da_fare': '⏳',
            'in_corso': '🔄',
            'completato': '✅',
            'cancellato': '❌',
            'posticipato': '📅'
        }
        
        # Emoji per priorità
        priorita_emoji = {
            'critica': '🔴',
            'alta': '🟠',
            'media': '🟡',
            'bassa': '🟢'
        }
        
        urgente_flag = " 🚨 URGENTE" if task['urgente'] else ""
        orario = f"   Orario: {task['ora_inizio']}"
        if task['ora_fine']:
            orario += f" - {task['ora_fine']}"
        orario = orario if task['ora_inizio'] else ""
        
        result = f"""
{stato_emoji.get(task['stato'], '📋')} TASK #{task['id_appuntamento']}{urgente_flag}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 {task['titolo']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📅 SCADENZA
   Data: {task['data_appuntamento']}
{orario}

{priorita_emoji.get(task['priorita'], '⚪')} PRIORITÀ E DIFFICOLTÀ
   Priorità: {task['priorita'].upper()}
   Difficoltà: {'⭐' * task['difficolta']} ({task['difficolta']}/10)
   {f"Tempo stimato: {task['tempo_stimato_ore']} ore" if task['tempo_stimato_ore'] else ""}

📂 CATEGORIA
   {task['nome_categoria'] or 'Nessuna categoria'}

📊 STATO
   {task['stato'].upper().replace('_', ' ')}
   {f"Completato: {task['data_completamento']}" if task['data_completamento'] else ""}

📝 DESCRIZIONE
   {task['descrizione'] or 'Nessuna descrizione'}

💭 NOTE
   {task['note'] or 'Nessuna nota'}

⏰ INFO SISTEMA
   Creato: {task['data_creazione']}
   Modificato: {task['data_modifica']}
        """.strip()
        
        conn.close()
        return result
        
    except Exception as e:
        return f"❌ Errore: {str(e)}"


@mcp.resource("today://tasks")
def get_today_resource() -> str:
    """Risorsa per visualizzare i task di oggi formattati
    
    Returns:
        Task di oggi formattati
    """
    try:
        oggi = datetime.now().strftime('%Y-%m-%d')
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT a.*, c.nome_categoria
            FROM appuntamenti a
            LEFT JOIN categorie c ON a.id_categoria = c.id_categoria
            WHERE a.data_appuntamento = ?
            AND a.stato NOT IN ('completato', 'cancellato')
            ORDER BY 
                a.urgente DESC,
                CASE a.priorita
                    WHEN 'critica' THEN 1
                    WHEN 'alta' THEN 2
                    WHEN 'media' THEN 3
                    WHEN 'bassa' THEN 4
                END,
                a.ora_inizio
        ''', (oggi,))
        
        tasks = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        if not tasks:
            return f"✅ Nessun task in programma per oggi ({oggi})"
        
        priorita_emoji = {'critica': '🔴', 'alta': '🟠', 'media': '🟡', 'bassa': '🟢'}
        
        result = f"""
📅 TASK DI OGGI - {oggi}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Totale task: {len(tasks)}

"""
        
        for task in tasks:
            urgente_flag = " 🚨" if task['urgente'] else ""
            orario = f"{task['ora_inizio']}" if task['ora_inizio'] else "📋"
            emoji_p = priorita_emoji.get(task['priorita'], '⚪')
            difficolta_stelle = '⭐' * task['difficolta']
            
            result += f"""
{orario} {emoji_p} {task['titolo']}{urgente_flag}
   Difficoltà: {difficolta_stelle} ({task['difficolta']}/10)
   Categoria: {task['nome_categoria'] or 'N/A'}
   {task['descrizione'][:60] + '...' if task['descrizione'] and len(task['descrizione']) > 60 else task['descrizione'] or ''}

"""
        
        return result.strip()
        
    except Exception as e:
        return f"❌ Errore: {str(e)}"


# ============= PROMPTS =============

@mcp.prompt()
def daily_planning_prompt(data: str = None) -> str:
    """Genera un prompt per pianificare la giornata
    
    Args:
        data: Data in formato YYYY-MM-DD (default: oggi)
    
    Returns:
        Prompt per pianificazione giornaliera
    """
    try:
        if not data:
            data = datetime.now().strftime('%Y-%m-%d')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT a.*, c.nome_categoria
            FROM appuntamenti a
            LEFT JOIN categorie c ON a.id_categoria = c.id_categoria
            WHERE a.data_appuntamento = ?
            AND a.stato NOT IN ('completato', 'cancellato')
            ORDER BY 
                a.urgente DESC,
                CASE a.priorita
                    WHEN 'critica' THEN 1
                    WHEN 'alta' THEN 2
                    WHEN 'media' THEN 3
                    WHEN 'bassa' THEN 4
                END,
                a.ora_inizio
        ''', (data,))
        
        tasks = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        urgenti = [t for t in tasks if t['urgente']]
        critici = [t for t in tasks if t['priorita'] == 'critica']
        
        tempo_totale = sum(t['tempo_stimato_ore'] or 0 for t in tasks)
        
        prompt = f"""
Crea un piano di lavoro ottimizzato per il {data}.

📊 PANORAMICA:
- Totale task: {len(tasks)}
- Task urgenti: {len(urgenti)}
- Task critici: {len(critici)}
- Tempo totale stimato: {tempo_totale} ore

📋 TASK DA COMPLETARE:
"""
        
        for task in tasks:
            urgente_flag = "🚨 URGENTE - " if task['urgente'] else ""
            orario = f"[{task['ora_inizio']}-{task['ora_fine']}] " if task['ora_inizio'] and task['ora_fine'] else ""
            tempo = f" ({task['tempo_stimato_ore']}h)" if task['tempo_stimato_ore'] else ""
            
            prompt += f"""
- {orario}{urgente_flag}[{task['priorita'].upper()}] {task['titolo']}{tempo}
  Difficoltà: {task['difficolta']}/10 | Categoria: {task['nome_categoria'] or 'N/A'}
  {task['descrizione'] if task['descrizione'] else ''}
"""
        
        prompt += """

Crea un piano che:
1. Inizi con un saluto motivante
2. Evidenzi i task urgenti e critici
3. Suggerisca un ordine ottimale di esecuzione considerando:
   - Priorità e urgenza
   - Orari fissi (se presenti)
   - Livello di difficoltà
   - Tempo stimato
4. Fornisca consigli pratici per:
   - Gestione del tempo
   - Pause strategiche
   - Affrontare i task più difficili
5. Conclude con una nota incoraggiante

Usa un tono professionale ma motivante. Usa emoji per rendere il piano più leggibile.
        """
        
        return prompt.strip()
        
    except Exception as e:
        return f"Errore nel generare il prompt: {str(e)}"


@mcp.prompt()
def task_breakdown_prompt(id_task: int) -> str:
    """Genera un prompt per scomporre un task complesso
    
    Args:
        id_task: ID del task da scomporre
    
    Returns:
        Prompt per scomposizione task
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT a.*, c.nome_categoria
            FROM appuntamenti a
            LEFT JOIN categorie c ON a.id_categoria = c.id_categoria
            WHERE a.id_appuntamento = ?
        ''', (id_task,))
        
        task = cursor.fetchone()
        conn.close()
        
        if not task:
            return f"Task {id_task} non trovato"
        
        task = dict(task)
        
        return f"""
Aiutami a scomporre questo task complesso in subtask più gestibili:

📋 TASK: {task['titolo']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 Descrizione: {task['descrizione'] or 'Nessuna descrizione'}

📊 Dettagli:
- Scadenza: {task['data_appuntamento']}
- Priorità: {task['priorita'].upper()}
- Difficoltà: {task['difficolta']}/10
- Tempo stimato: {task['tempo_stimato_ore']} ore
- Categoria: {task['nome_categoria'] or 'N/A'}

Fornisci:
1. Una lista di 3-7 subtask specifici e actionable
2. Per ogni subtask:
   - Descrizione chiara (max 1 riga)
   - Tempo stimato
   - Livello di difficoltà
   - Ordine suggerito di esecuzione
3. Suggerimenti pratici per affrontare il task nel modo più efficace

Sii concreto e pratico. Ogni subtask deve essere qualcosa che può essere completato in una sessione di lavoro.
        """.strip()
        
    except Exception as e:
        return f"Errore: {str(e)}"


# Run with STDIO transport for Claude Desktop
if __name__ == "__main__":
    mcp.run()
