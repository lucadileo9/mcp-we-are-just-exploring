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
    
    # Tabella CLIENTI
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clienti (
            id_cliente INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cognome TEXT NOT NULL,
            email TEXT UNIQUE,
            telefono TEXT NOT NULL,
            telefono_secondario TEXT,
            via TEXT,
            numero_civico TEXT,
            citta TEXT,
            cap TEXT,
            provincia TEXT,
            note TEXT,
            data_registrazione TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            attivo BOOLEAN DEFAULT 1
        )
    ''')
    
    # Tabella TIPI_APPUNTAMENTO
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tipi_appuntamento (
            id_tipo INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_tipo TEXT NOT NULL UNIQUE,
            descrizione TEXT,
            durata_minuti INTEGER DEFAULT 30,
            colore TEXT
        )
    ''')
    
    # Tabella APPUNTAMENTI
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS appuntamenti (
            id_appuntamento INTEGER PRIMARY KEY AUTOINCREMENT,
            id_cliente INTEGER NOT NULL,
            id_tipo INTEGER,
            data_appuntamento DATE NOT NULL,
            ora_inizio TIME NOT NULL,
            ora_fine TIME NOT NULL,
            titolo TEXT NOT NULL,
            descrizione TEXT,
            urgente BOOLEAN DEFAULT 0,
            stato TEXT DEFAULT 'confermato',
            luogo TEXT,
            note TEXT,
            data_creazione TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_modifica TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            promemoria_inviato BOOLEAN DEFAULT 0,
            FOREIGN KEY (id_cliente) REFERENCES clienti(id_cliente),
            FOREIGN KEY (id_tipo) REFERENCES tipi_appuntamento(id_tipo),
            CHECK (stato IN ('confermato', 'completato', 'cancellato', 'in_attesa', 'non_presentato'))
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
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_appuntamenti_cliente ON appuntamenti(id_cliente)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_clienti_email ON clienti(email)')
    
    conn.commit()
    print("✓ Database e tabelle creati con successo")
    
    return conn, cursor

def inserisci_dati_esempio(conn, cursor):
    """Inserisce dati di esempio nel database"""
    
    # Tipi di appuntamento
    tipi = [
        ('Consulenza', 'Consulenza generale', 60, '#3498db'),
        ('Visita medica', 'Visita medica di routine', 45, '#2ecc71'),
        ('Controllo', 'Controllo periodico', 30, '#f39c12'),
        ('Urgenza', 'Appuntamento urgente', 30, '#e74c3c'),
        ('Follow-up', 'Visita di controllo successiva', 30, '#9b59b6'),
    ]
    
    cursor.executemany('''
        INSERT OR IGNORE INTO tipi_appuntamento (nome_tipo, descrizione, durata_minuti, colore)
        VALUES (?, ?, ?, ?)
    ''', tipi)
    
    # Clienti di esempio
    clienti = [
        ('Mario', 'Rossi', 'mario.rossi@email.it', '333-1234567', '339-7654321', 'Via Roma', '10', 'Milano', '20100', 'MI', 'Cliente storico'),
        ('Laura', 'Bianchi', 'laura.bianchi@email.it', '334-2345678', None, 'Corso Vittorio Emanuele', '25', 'Torino', '10121', 'TO', ''),
        ('Giuseppe', 'Verdi', 'giuseppe.verdi@email.it', '335-3456789', '338-1111111', 'Via Garibaldi', '5', 'Roma', '00100', 'RM', 'Preferisce appuntamenti mattutini'),
        ('Anna', 'Russo', 'anna.russo@email.it', '336-4567890', None, 'Piazza Duomo', '1', 'Firenze', '50100', 'FI', ''),
        ('Luca', 'Ferrari', 'luca.ferrari@email.it', '337-5678901', '340-2222222', 'Via Dante', '15', 'Bologna', '40100', 'BO', 'Allergico a determinati farmaci'),
        ('Francesca', 'Romano', 'francesca.romano@email.it', '338-6789012', None, 'Via Manzoni', '30', 'Napoli', '80100', 'NA', ''),
        ('Paolo', 'Esposito', 'paolo.esposito@email.it', '339-7890123', '341-3333333', 'Viale Europa', '8', 'Palermo', '90100', 'PA', 'Richiede sempre fattura'),
        ('Chiara', 'Conti', 'chiara.conti@email.it', '340-8901234', None, 'Via Veneto', '22', 'Genova', '16100', 'GE', ''),
    ]
    
    cursor.executemany('''
        INSERT INTO clienti (nome, cognome, email, telefono, telefono_secondario, via, numero_civico, citta, cap, provincia, note)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', clienti)
    
    # Appuntamenti di esempio
    base_date = datetime.now()
    appuntamenti = []
    
    # Genera appuntamenti per i prossimi 30 giorni
    for i in range(30):
        num_appuntamenti_giorno = random.randint(1, 4)
        data = base_date + timedelta(days=i)
        
        for j in range(num_appuntamenti_giorno):
            ora_inizio = random.randint(8, 17)
            minuti = random.choice([0, 15, 30, 45])
            id_cliente = random.randint(1, len(clienti))
            id_tipo = random.randint(1, len(tipi))
            urgente = random.choice([0, 0, 0, 1])  # 25% di probabilità di essere urgente
            stato = random.choice(['confermato', 'confermato', 'confermato', 'in_attesa'])
            
            durata = 30 if urgente else random.choice([30, 45, 60])
            ora_fine_h = ora_inizio + (durata // 60)
            ora_fine_m = minuti + (durata % 60)
            if ora_fine_m >= 60:
                ora_fine_h += 1
                ora_fine_m -= 60
            
            appuntamenti.append((
                id_cliente,
                id_tipo,
                data.strftime('%Y-%m-%d'),
                f"{ora_inizio:02d}:{minuti:02d}",
                f"{ora_fine_h:02d}:{ora_fine_m:02d}",
                f"Appuntamento {i+1}-{j+1}",
                f"Descrizione appuntamento per il cliente",
                urgente,
                stato,
                "Studio Principale",
                ""
            ))
    
    cursor.executemany('''
        INSERT INTO appuntamenti (id_cliente, id_tipo, data_appuntamento, ora_inizio, ora_fine, 
                                 titolo, descrizione, urgente, stato, luogo, note)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', appuntamenti)
    
    conn.commit()
    print(f"✓ Inseriti {len(clienti)} clienti")
    print(f"✓ Inseriti {len(tipi)} tipi di appuntamento")
    print(f"✓ Inseriti {len(appuntamenti)} appuntamenti")

def mostra_statistiche(cursor):
    """Mostra statistiche del database"""
    print("\n" + "="*60)
    print("STATISTICHE DATABASE")
    print("="*60)
    
    # Totale clienti
    cursor.execute('SELECT COUNT(*) FROM clienti')
    print(f"Totale clienti: {cursor.fetchone()[0]}")
    
    # Totale appuntamenti
    cursor.execute('SELECT COUNT(*) FROM appuntamenti')
    print(f"Totale appuntamenti: {cursor.fetchone()[0]}")
    
    # Appuntamenti urgenti
    cursor.execute('SELECT COUNT(*) FROM appuntamenti WHERE urgente = 1')
    print(f"Appuntamenti urgenti: {cursor.fetchone()[0]}")
    
    # Appuntamenti per stato
    cursor.execute('''
        SELECT stato, COUNT(*) as num 
        FROM appuntamenti 
        GROUP BY stato
        ORDER BY num DESC
    ''')
    print("\nAppuntamenti per stato:")
    for row in cursor.fetchall():
        print(f"  - {row[0]}: {row[1]}")
    
    # Prossimi 5 appuntamenti
    cursor.execute('''
        SELECT 
            a.data_appuntamento,
            a.ora_inizio,
            c.nome || ' ' || c.cognome as cliente,
            a.titolo,
            a.urgente
        FROM appuntamenti a
        JOIN clienti c ON a.id_cliente = c.id_cliente
        WHERE a.data_appuntamento >= date('now')
        ORDER BY a.data_appuntamento, a.ora_inizio
        LIMIT 5
    ''')
    
    print("\nProssimi 5 appuntamenti:")
    for row in cursor.fetchall():
        urgente_marker = " 🚨 URGENTE" if row[4] else ""
        print(f"  - {row[0]} alle {row[1]} - {row[2]}: {row[3]}{urgente_marker}")
    
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
