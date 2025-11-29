"""
Sistema di Gestione Calendario Prenotazioni
Database SQLite per la gestione di appuntamenti e clienti
"""

import sqlite3
from datetime import datetime, timedelta
import random

def crea_database():
    """Crea il database e le tabelle necessarie"""
    
    # Connessione al database
    conn = sqlite3.connect('calendario_prenotazioni.db')
    cursor = conn.cursor()
    
    # Tabella CATEGORIE (opzionale, per classificare gli appuntamenti)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categorie (
            id_categoria INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_categoria TEXT NOT NULL UNIQUE,
            descrizione TEXT,
            colore TEXT
        )
    ''')
    
    # Tabella APPUNTAMENTI
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS appuntamenti (
            id_appuntamento INTEGER PRIMARY KEY AUTOINCREMENT,
            titolo TEXT NOT NULL,
            descrizione TEXT,
            data_appuntamento DATE NOT NULL,
            ora_inizio TIME,
            ora_fine TIME,
            id_categoria INTEGER,
            priorita TEXT DEFAULT 'media',
            difficolta INTEGER DEFAULT 3,
            tempo_stimato_ore REAL,
            stato TEXT DEFAULT 'da_fare',
            urgente BOOLEAN DEFAULT 0,
            note TEXT,
            data_creazione TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_modifica TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_completamento TIMESTAMP,
            FOREIGN KEY (id_categoria) REFERENCES categorie(id_categoria),
            CHECK (priorita IN ('bassa', 'media', 'alta', 'critica')),
            CHECK (stato IN ('da_fare', 'in_corso', 'completato', 'cancellato', 'posticipato')),
            CHECK (difficolta BETWEEN 1 AND 10)
        )
    ''')
    
    # Tabella STORICO_MODIFICHE (per tracciare le modifiche agli appuntamenti)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS storico_modifiche (
            id_modifica INTEGER PRIMARY KEY AUTOINCREMENT,
            id_appuntamento INTEGER NOT NULL,
            tipo_modifica TEXT NOT NULL,
            descrizione_modifica TEXT,
            data_modifica TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (id_appuntamento) REFERENCES appuntamenti(id_appuntamento)
        )
    ''')
    
    # Indici per migliorare le performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_appuntamenti_data ON appuntamenti(data_appuntamento)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_appuntamenti_priorita ON appuntamenti(priorita)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_appuntamenti_stato ON appuntamenti(stato)')
    
    conn.commit()
    print("✓ Database e tabelle creati con successo")
    
    return conn, cursor

def inserisci_dati_esempio(conn, cursor):
    """Inserisce dati di esempio nel database"""
    
    # Categorie
    categorie = [
        ('Lavoro', 'Task lavorativi', '#3498db'),
        ('Studio', 'Attività di studio e apprendimento', '#9b59b6'),
        ('Personale', 'Impegni personali', '#2ecc71'),
        ('Salute', 'Visite mediche e fitness', '#e74c3c'),
        ('Casa', 'Lavori domestici e manutenzione', '#f39c12'),
        ('Famiglia', 'Tempo con famiglia e amici', '#1abc9c'),
    ]
    
    cursor.executemany('''
        INSERT OR IGNORE INTO categorie (nome_categoria, descrizione, colore)
        VALUES (?, ?, ?)
    ''', categorie)
    
    # Appuntamenti di esempio
    base_date = datetime.now()
    appuntamenti = []
    
    # Task di esempio realistici
    task_examples = [
        ("Riunione team", "Riunione settimanale con il team di progetto", "Lavoro", "alta", 5, 2.0, False),
        ("Palestra", "Allenamento cardio e pesi", "Salute", "media", 3, 1.5, False),
        ("Spesa settimanale", "Comprare generi alimentari per la settimana", "Personale", "bassa", 2, 1.0, False),
        ("Studiare Python", "Completare corso online su machine learning", "Studio", "alta", 7, 3.0, False),
        ("Dentista", "Controllo semestrale", "Salute", "media", 2, 1.0, False),
        ("Presentazione cliente", "Preparare e presentare proposta", "Lavoro", "critica", 8, 4.0, True),
        ("Riparare rubinetto", "Chiamare idraulico per perdita", "Casa", "alta", 4, 0.5, True),
        ("Compleanno mamma", "Organizzare cena di compleanno", "Famiglia", "alta", 6, 3.0, False),
        ("Report mensile", "Completare report per il management", "Lavoro", "alta", 6, 2.5, False),
        ("Yoga", "Lezione di yoga online", "Salute", "bassa", 2, 1.0, False),
        ("Corso inglese", "Lezione settimanale di inglese", "Studio", "media", 4, 1.5, False),
        ("Pagare bollette", "Pagamento utenze mensili", "Personale", "alta", 1, 0.5, True),
    ]
    
    # Mappa categorie
    categoria_map = {cat[0]: i+1 for i, cat in enumerate(categorie)}
    
    # Genera appuntamenti per i prossimi 30 giorni
    for i in range(30):
        num_task_giorno = random.randint(0, 3)
        data = base_date + timedelta(days=i)
        
        for j in range(num_task_giorno):
            task = random.choice(task_examples)
            titolo, descrizione, categoria, priorita, difficolta, tempo_ore, urgente = task
            
            # Genera orario casuale
            ora_inizio_h = random.randint(8, 18)
            ora_inizio_m = random.choice([0, 15, 30, 45])
            ora_inizio = f"{ora_inizio_h:02d}:{ora_inizio_m:02d}"
            
            # Calcola ora fine basata sul tempo stimato
            if tempo_ore:
                fine_dt = datetime.strptime(ora_inizio, '%H:%M') + timedelta(hours=tempo_ore)
                ora_fine = fine_dt.strftime('%H:%M')
            else:
                ora_fine = None
            
            stato = random.choice(['da_fare', 'da_fare', 'da_fare', 'in_corso', 'completato'])
            
            # Se completato, aggiungi data completamento
            data_completamento = None
            if stato == 'completato':
                data_completamento = (data - timedelta(hours=random.randint(1, 48))).isoformat()
            
            appuntamenti.append((
                titolo,
                descrizione,
                data.strftime('%Y-%m-%d'),
                ora_inizio,
                ora_fine,
                categoria_map.get(categoria, 1),
                priorita,
                difficolta,
                tempo_ore,
                stato,
                1 if urgente else 0,
                "",  # note
                data_completamento
            ))
    
    cursor.executemany('''
        INSERT INTO appuntamenti (titolo, descrizione, data_appuntamento, ora_inizio, ora_fine,
                                 id_categoria, priorita, difficolta, tempo_stimato_ore, 
                                 stato, urgente, note, data_completamento)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', appuntamenti)
    
    conn.commit()
    print(f"✓ Inserite {len(categorie)} categorie")
    print(f"✓ Inseriti {len(appuntamenti)} appuntamenti/task")

def mostra_statistiche(cursor):
    """Mostra statistiche del database"""
    print("\n" + "="*60)
    print("STATISTICHE DATABASE")
    print("="*60)
    
    # Totale appuntamenti
    cursor.execute('SELECT COUNT(*) FROM appuntamenti')
    print(f"Totale task: {cursor.fetchone()[0]}")
    
    # Per stato
    cursor.execute('''
        SELECT stato, COUNT(*) as num 
        FROM appuntamenti 
        GROUP BY stato
        ORDER BY num DESC
    ''')
    print("\nTask per stato:")
    for row in cursor.fetchall():
        print(f"  - {row[0]}: {row[1]}")
    
    # Per priorità
    cursor.execute('''
        SELECT priorita, COUNT(*) as num 
        FROM appuntamenti 
        GROUP BY priorita
        ORDER BY 
            CASE priorita
                WHEN 'critica' THEN 1
                WHEN 'alta' THEN 2
                WHEN 'media' THEN 3
                WHEN 'bassa' THEN 4
            END
    ''')
    print("\nTask per priorità:")
    for row in cursor.fetchall():
        print(f"  - {row[0]}: {row[1]}")
    
    # Urgenti
    cursor.execute('SELECT COUNT(*) FROM appuntamenti WHERE urgente = 1')
    print(f"\nTask urgenti: {cursor.fetchone()[0]}")
    
    # Prossimi 5 task da fare
    cursor.execute('''
        SELECT 
            data_appuntamento,
            ora_inizio,
            titolo,
            priorita,
            urgente
        FROM appuntamenti
        WHERE data_appuntamento >= date('now')
        AND stato != 'completato'
        ORDER BY 
            urgente DESC,
            CASE priorita
                WHEN 'critica' THEN 1
                WHEN 'alta' THEN 2
                WHEN 'media' THEN 3
                WHEN 'bassa' THEN 4
            END,
            data_appuntamento,
            ora_inizio
        LIMIT 5
    ''')
    
    print("\nProssimi 5 task (per priorità e urgenza):")
    for row in cursor.fetchall():
        urgente_marker = " 🚨" if row[4] else ""
        priorita_emoji = {'critica': '🔴', 'alta': '🟠', 'media': '🟡', 'bassa': '🟢'}.get(row[3], '')
        orario = f" alle {row[1]}" if row[1] else ""
        print(f"  - {row[0]}{orario} {priorita_emoji} {row[2]}{urgente_marker}")
    
    print("="*60 + "\n")

def main():
    """Funzione principale"""
    print("\n" + "="*60)
    print("CREAZIONE DATABASE CALENDARIO PRENOTAZIONI")
    print("="*60 + "\n")
    
    # Crea database e tabelle
    conn, cursor = crea_database()
    
    # Inserisci dati di esempio
    print("\nInserimento dati di esempio...")
    inserisci_dati_esempio(conn, cursor)
    
    # Mostra statistiche
    mostra_statistiche(cursor)
    
    # Chiudi connessione
    conn.close()
    print("✓ Database creato e popolato con successo!")
    print(f"✓ File database: calendario_prenotazioni.db\n")

if __name__ == "__main__":
    main()
