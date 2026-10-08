import sqlite3
import os
import json
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(__file__), 'hydrorescue.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Plumbers table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS plumbers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        business_name TEXT NOT NULL,
        phone TEXT NOT NULL,
        license_no TEXT NOT NULL,
        license_type TEXT NOT NULL,
        license_state TEXT NOT NULL,
        license_verified INTEGER DEFAULT 1,
        insurance_policy_no TEXT NOT NULL,
        insurance_carrier TEXT NOT NULL,
        insurance_coverage TEXT NOT NULL,
        insurance_verified INTEGER DEFAULT 1,
        background_checked INTEGER DEFAULT 1,
        background_check_date TEXT NOT NULL,
        rating REAL DEFAULT 4.9,
        reviews_count INTEGER DEFAULT 0,
        hourly_rate REAL DEFAULT 140.0,
        emergency_dispatch_fee REAL DEFAULT 89.0,
        is_on_call INTEGER DEFAULT 1,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        equipped_tools TEXT NOT NULL,
        avatar_url TEXT,
        badges TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Emergency categories with transparent pricing caps
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS emergency_categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        slug TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        severity_level TEXT NOT NULL,
        base_dispatch_fee REAL NOT NULL,
        est_labor_hours REAL NOT NULL,
        est_labor_rate REAL NOT NULL,
        est_parts_min REAL NOT NULL,
        est_parts_max REAL NOT NULL,
        max_price_cap REAL NOT NULL,
        market_gouged_price REAL NOT NULL,
        shutoff_critical INTEGER DEFAULT 1,
        icon TEXT NOT NULL
    )
    ''')

    # Dispatches table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS dispatches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dispatch_code TEXT UNIQUE NOT NULL,
        customer_name TEXT NOT NULL,
        customer_phone TEXT NOT NULL,
        address TEXT NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        category_id INTEGER NOT NULL,
        description TEXT,
        severity TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending',
        plumber_id INTEGER,
        eta_minutes INTEGER DEFAULT 20,
        dispatch_fee REAL NOT NULL,
        quoted_estimate_min REAL NOT NULL,
        quoted_estimate_max REAL NOT NULL,
        escrow_deposit REAL NOT NULL,
        final_invoice_amount REAL DEFAULT 0.0,
        shutoff_confirmed INTEGER DEFAULT 0,
        before_notes TEXT,
        after_repair_notes TEXT,
        warranty_days INTEGER DEFAULT 90,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        completed_at TEXT,
        FOREIGN KEY (category_id) REFERENCES emergency_categories(id),
        FOREIGN KEY (plumber_id) REFERENCES plumbers(id)
    )
    ''')

    # Reviews table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        plumber_id INTEGER NOT NULL,
        customer_name TEXT NOT NULL,
        emergency_type TEXT NOT NULL,
        rating INTEGER NOT NULL,
        comment TEXT NOT NULL,
        time_ago TEXT NOT NULL,
        verified_emergency INTEGER DEFAULT 1,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (plumber_id) REFERENCES plumbers(id)
    )
    ''')

    # Seed data if tables are empty
    cursor.execute('SELECT COUNT(*) FROM emergency_categories')
    if cursor.fetchone()[0] == 0:
        categories = [
            (
                'burst-pipe', 'Active Burst Pipe / Flooding',
                'Water actively spraying from pressurized supply line, ceiling, or basement drywall.',
                'CRITICAL', 99.0, 1.5, 160.0, 45.0, 120.0, 480.0, 1250.0, 1, 'zap'
            ),
            (
                'main-drain-backup', 'Main Sewer Line Backup',
                'Multiple toilets/tubs gurgling or raw sewage backing up through lowest floor drains.',
                'HIGH', 119.0, 2.0, 165.0, 60.0, 150.0, 599.0, 1600.0, 0, 'alert-triangle'
            ),
            (
                'water-heater-rupture', 'Water Heater Tank Failure / Leak',
                '50-gal tank leaking or bottom heating element ruptured, risk of structural water damage.',
                'HIGH', 89.0, 2.0, 155.0, 75.0, 200.0, 550.0, 1400.0, 1, 'flame'
            ),
            (
                'shutoff-valve-failure', 'Broken Main Shutoff Valve',
                'Main incoming gate or ball valve broken in open position, cannot stop house water supply.',
                'CRITICAL', 99.0, 1.5, 160.0, 50.0, 110.0, 450.0, 1100.0, 1, 'shield-alert'
            ),
            (
                'frozen-burst-threat', 'Frozen / Partially Ruptured Pipes',
                'Sub-freezing exterior wall pipe freeze with imminent rupture risk or hairline crack.',
                'MEDIUM', 89.0, 1.5, 150.0, 30.0, 90.0, 420.0, 950.0, 1, 'snowflake'
            ),
            (
                'gas-line-plumbing', 'Emergency Gas Shutoff / Leak Triage',
                'Natural gas odor near water heater or furnace line, requires licensed master plumber pressure test.',
                'CRITICAL', 129.0, 2.0, 175.0, 80.0, 180.0, 650.0, 1800.0, 1, 'activity'
            )
        ]
        cursor.executemany('''
        INSERT INTO emergency_categories (
            slug, title, description, severity_level, base_dispatch_fee,
            est_labor_hours, est_labor_rate, est_parts_min, est_parts_max,
            max_price_cap, market_gouged_price, shutoff_critical, icon
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', categories)

    cursor.execute('SELECT COUNT(*) FROM plumbers')
    if cursor.fetchone()[0] == 0:
        plumbers = [
            (
                'Marcus Vance', 'Apex Master Plumbing & Emergency Services',
                '(555) 392-1084', 'MP-89421-TX', 'Master Plumber', 'TX', 1,
                'POL-GL-7729104', 'Travelers Commercial', '$2,000,000 Aggregate', 1,
                1, '2026-08-15', 4.95, 218, 160.0, 89.0, 1,
                37.7749, -122.4194,
                json.dumps(['Ridgid ProPress Tool', 'Milwaukee 100ft Drain Snake', 'PEX-A / Copper 1/2"-1" Stock', 'Thermal Leak Camera', 'Digital Manometer']),
                'https://images.unsplash.com/photo-1621905251189-08b45d6a269e?auto=format&fit=crop&w=256&q=80',
                json.dumps(['Master Plumber', '24/7 Verified On-Duty', 'Zero-Gouge Certified', '90-Day Guarantee'])
            ),
            (
                'Elena Rostova', 'BlueFlow Rapid Response Plumbing',
                '(555) 843-9921', 'JP-40912-TX', 'Journeyman Plumber', 'TX', 1,
                'POL-GL-8911023', 'Nationwide Mutual', '$1,500,000 Aggregate', 1,
                1, '2026-09-02', 4.91, 164, 150.0, 99.0, 1,
                37.7833, -122.4167,
                json.dumps(['Hydro-Jet Portable Unit', 'BrassCraft Pro-Cutter', 'SharkBite EvoPEX Emergency Kits', 'Acoustic Pipe Locator']),
                'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&w=256&q=80',
                json.dumps(['Rapid Dispatch (<20m)', 'State Background Vetted', 'Commercial Insured'])
            ),
            (
                'David "Dave" Chen', 'Redline Emergency Hydro & Drain',
                '(555) 712-4401', 'MP-33109-TX', 'Master Plumber & Gas Fitter', 'TX', 1,
                'POL-GL-9004412', 'The Hartford', '$2,000,000 Aggregate', 1,
                1, '2026-07-20', 4.88, 305, 165.0, 99.0, 1,
                37.7690, -122.4467,
                json.dumps(['Spartan Tool 738 Jetter', 'ProPress Copper Crimper', 'Main Shutoff Key & Extractor', 'Sewer Inspection Camera']),
                'https://images.unsplash.com/photo-1560250097-0b93528c311a?auto=format&fit=crop&w=256&q=80',
                json.dumps(['Master Gas Fitter', 'Emergency Night Specialist', 'Verified Escrow Approved'])
            ),
            (
                'Sarah Jenkins', 'Guardian 24/7 Plumbing Pros',
                '(555) 609-3388', 'JP-55821-TX', 'Journeyman Plumber', 'TX', 1,
                'POL-GL-4482910', 'Liberty Mutual', '$2,000,000 Aggregate', 1,
                1, '2026-08-30', 4.93, 142, 145.0, 89.0, 1,
                37.7550, -122.4200,
                json.dumps(['Electric Eel Sewer Auger', 'PEX Expansion Tool', 'Emergency Water Extraction Pump']),
                'https://images.unsplash.com/photo-1580489944761-15a19d654956?auto=format&fit=crop&w=256&q=80',
                json.dumps(['Emergency Dispatch', 'Zero Price Gouging', 'Female-Led Trade Crew'])
            )
        ]
        cursor.executemany('''
        INSERT INTO plumbers (
            name, business_name, phone, license_no, license_type, license_state,
            license_verified, insurance_policy_no, insurance_carrier, insurance_coverage,
            insurance_verified, background_checked, background_check_date, rating,
            reviews_count, hourly_rate, emergency_dispatch_fee, is_on_call, latitude,
            longitude, equipped_tools, avatar_url, badges
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', plumbers)

    # Seed mock reviews
    cursor.execute('SELECT COUNT(*) FROM reviews')
    if cursor.fetchone()[0] == 0:
        reviews = [
            (1, 'Rachel K.', 'Burst Pipe at 2:30 AM', 5, 'Woke up to water raining through our ceiling at 2:30 AM on Sunday. Other places quoted $1,800 just to roll a truck or had disconnected lines. Marcus accepted in 45 seconds, guided me over the phone to shut the meter, and arrived in 18 minutes with the exact copper fitting. Total bill was $329. Saved our home.', '2 days ago', 1),
            (1, 'Carlos M.', 'Water Heater Rupture', 5, '100% transparent pricing. Escrow hold gave me total confidence that there would not be hidden emergency fees. Marcus is a certified Master Plumber, showed his state badge immediately upon arrival.', '5 days ago', 1),
            (2, 'Amanda B.', 'Severe Sewer Line Backup', 5, 'Elena showed up at 11 PM on a Saturday. Cleared the line, ran the camera, and walked us through the footage. No predatory fees, just honest professional work with a 90-day guarantee.', '1 week ago', 1),
            (3, 'Greg T.', 'Broken Main Valve', 5, 'Our main gate valve sheared off when we tried to turn off the water. Dave was at our curb within 22 minutes with specialized curb keys and installed a brand new quarter-turn ball valve.', '2 weeks ago', 1)
        ]
        cursor.executemany('''
        INSERT INTO reviews (plumber_id, customer_name, emergency_type, rating, comment, time_ago, verified_emergency)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', reviews)

    # Seed an active demo dispatch
    cursor.execute('SELECT COUNT(*) FROM dispatches')
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
        INSERT INTO dispatches (
            dispatch_code, customer_name, customer_phone, address, latitude, longitude,
            category_id, description, severity, status, plumber_id, eta_minutes,
            dispatch_fee, quoted_estimate_min, quoted_estimate_max, escrow_deposit,
            shutoff_confirmed, before_notes, created_at
        ) VALUES (
            'EMERG-4819', 'Jonathan Reynolds', '(555) 912-7721', '452 Castro St, San Francisco, CA',
            37.7600, -122.4350, 1, 'Hot water line burst underneath kitchen sink, flooding floor.',
            'CRITICAL', 'en_route', 1, 14, 89.0, 240.0, 390.0, 150.0, 1,
            'Customer successfully located and turned main ball valve. Water leak contained to kitchen cabinet.',
            datetime('now')
        )
        ''')

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("HydroRescue Database initialized successfully.")
