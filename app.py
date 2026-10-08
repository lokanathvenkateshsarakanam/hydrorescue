import os
import json
import random
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for
from database import get_db_connection, init_db

app = Flask(__name__)
app.config['SECRET_KEY'] = 'hydrorescue-verified-emergency-secret-key-2026'

# Ensure database is initialized
init_db()

# --- Page Routes ---

@app.route('/')
def homeowner_index():
    return render_template('index.html')

@app.route('/plumber')
def plumber_portal():
    return render_template('plumber_portal.html')

@app.route('/admin')
def admin_portal():
    return render_template('admin_portal.html')

@app.route('/shutoff-guide')
def shutoff_guide():
    return render_template('shutoff_guide.html')

# --- API Endpoints ---

@app.route('/api/categories', methods=['GET'])
def get_categories():
    conn = get_db_connection()
    categories = conn.execute('SELECT * FROM emergency_categories ORDER BY severity_level DESC').fetchall()
    conn.close()
    return jsonify([dict(c) for c in categories])

@app.route('/api/plumbers', methods=['GET'])
def get_plumbers():
    only_on_call = request.args.get('on_call')
    conn = get_db_connection()
    query = 'SELECT * FROM plumbers'
    params = []
    if only_on_call == '1':
        query += ' WHERE is_on_call = 1'
    query += ' ORDER BY is_on_call DESC, rating DESC'
    plumbers = conn.execute(query, params).fetchall()
    
    result = []
    for p in plumbers:
        item = dict(p)
        item['equipped_tools'] = json.loads(item['equipped_tools']) if item['equipped_tools'] else []
        item['badges'] = json.loads(item['badges']) if item['badges'] else []
        result.append(item)
    conn.close()
    return jsonify(result)

@app.route('/api/plumbers/<int:plumber_id>', methods=['GET'])
def get_plumber_detail(plumber_id):
    conn = get_db_connection()
    p = conn.execute('SELECT * FROM plumbers WHERE id = ?', (plumber_id,)).fetchone()
    if not p:
        conn.close()
        return jsonify({'error': 'Plumber not found'}), 404
    
    item = dict(p)
    item['equipped_tools'] = json.loads(item['equipped_tools']) if item['equipped_tools'] else []
    item['badges'] = json.loads(item['badges']) if item['badges'] else []
    
    reviews = conn.execute('SELECT * FROM reviews WHERE plumber_id = ? ORDER BY id DESC', (plumber_id,)).fetchall()
    item['reviews'] = [dict(r) for r in reviews]
    conn.close()
    return jsonify(item)

@app.route('/api/dispatches/active', methods=['GET'])
def get_active_dispatch():
    conn = get_db_connection()
    # Get newest non-cancelled dispatch
    dispatch = conn.execute('''
        SELECT d.*, c.title as category_title, c.icon as category_icon,
               p.name as plumber_name, p.business_name, p.phone as plumber_phone,
               p.avatar_url as plumber_avatar, p.license_no as plumber_license,
               p.license_type, p.rating as plumber_rating, p.latitude as plumber_lat,
               p.longitude as plumber_lng
        FROM dispatches d
        LEFT JOIN emergency_categories c ON d.category_id = c.id
        LEFT JOIN plumbers p ON d.plumber_id = p.id
        ORDER BY d.id DESC LIMIT 1
    ''').fetchone()
    conn.close()
    if not dispatch:
        return jsonify(None)
    return jsonify(dict(dispatch))

@app.route('/api/dispatches/<int:dispatch_id>', methods=['GET'])
def get_dispatch_by_id(dispatch_id):
    conn = get_db_connection()
    dispatch = conn.execute('''
        SELECT d.*, c.title as category_title, c.icon as category_icon,
               p.name as plumber_name, p.business_name, p.phone as plumber_phone,
               p.avatar_url as plumber_avatar, p.license_no as plumber_license,
               p.license_type, p.rating as plumber_rating, p.latitude as plumber_lat,
               p.longitude as plumber_lng
        FROM dispatches d
        LEFT JOIN emergency_categories c ON d.category_id = c.id
        LEFT JOIN plumbers p ON d.plumber_id = p.id
        WHERE d.id = ?
    ''', (dispatch_id,)).fetchone()
    conn.close()
    if not dispatch:
        return jsonify({'error': 'Dispatch not found'}), 404
    return jsonify(dict(dispatch))

@app.route('/api/dispatches/create', methods=['POST'])
def create_dispatch():
    data = request.json or {}
    customer_name = data.get('customer_name', 'Emergency Homeowner')
    customer_phone = data.get('customer_phone', '(555) 234-5678')
    address = data.get('address', '124 Market St, San Francisco, CA')
    category_id = int(data.get('category_id', 1))
    description = data.get('description', 'Catastrophic pipe burst / severe water leak')
    shutoff_confirmed = 1 if data.get('shutoff_confirmed') else 0
    
    conn = get_db_connection()
    category = conn.execute('SELECT * FROM emergency_categories WHERE id = ?', (category_id,)).fetchone()
    if not category:
        conn.close()
        return jsonify({'error': 'Invalid category'}), 400

    # Match the best available on-call plumber
    plumber = conn.execute('SELECT * FROM plumbers WHERE is_on_call = 1 AND license_verified = 1 ORDER BY rating DESC LIMIT 1').fetchone()
    if not plumber:
        # Fallback to any plumber
        plumber = conn.execute('SELECT * FROM plumbers WHERE license_verified = 1 LIMIT 1').fetchone()

    plumber_id = plumber['id'] if plumber else None
    dispatch_code = f"EMERG-{random.randint(1000, 9999)}"
    eta = random.randint(14, 25)
    
    dispatch_fee = category['base_dispatch_fee']
    est_labor = category['est_labor_hours'] * category['est_labor_rate']
    quoted_min = dispatch_fee + est_labor + category['est_parts_min']
    quoted_max = dispatch_fee + est_labor + category['est_parts_max']
    escrow_deposit = round(dispatch_fee + (est_labor * 0.5), 2)

    # Homeowner coordinates (around SF downtown for demo)
    lat = 37.7749 + (random.uniform(-0.015, 0.015))
    lng = -122.4194 + (random.uniform(-0.015, 0.015))

    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO dispatches (
            dispatch_code, customer_name, customer_phone, address, latitude, longitude,
            category_id, description, severity, status, plumber_id, eta_minutes,
            dispatch_fee, quoted_estimate_min, quoted_estimate_max, escrow_deposit,
            shutoff_confirmed, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
    ''', (
        dispatch_code, customer_name, customer_phone, address, lat, lng,
        category_id, description, category['severity_level'], 'accepted',
        plumber_id, eta, dispatch_fee, quoted_min, quoted_max, escrow_deposit,
        shutoff_confirmed
    ))
    dispatch_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return jsonify({
        'success': True,
        'dispatch_id': dispatch_id,
        'dispatch_code': dispatch_code,
        'eta_minutes': eta,
        'escrow_deposit': escrow_deposit,
        'status': 'accepted',
        'message': f"Verified Master Plumber {plumber['name'] if plumber else 'Staff'} has been dispatched immediately."
    })

@app.route('/api/dispatches/<int:dispatch_id>/status', methods=['POST'])
def update_dispatch_status(dispatch_id):
    data = request.json or {}
    new_status = data.get('status')
    valid_statuses = ['pending', 'accepted', 'en_route', 'arrived', 'in_progress', 'completed', 'cancelled']
    if new_status not in valid_statuses:
        return jsonify({'error': 'Invalid status'}), 400

    conn = get_db_connection()
    if new_status == 'completed':
        conn.execute('UPDATE dispatches SET status = ?, completed_at = datetime("now") WHERE id = ?', (new_status, dispatch_id))
    else:
        conn.execute('UPDATE dispatches SET status = ? WHERE id = ?', (new_status, dispatch_id))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'status': new_status})

@app.route('/api/dispatches/<int:dispatch_id>/shutoff-confirm', methods=['POST'])
def confirm_shutoff(dispatch_id):
    conn = get_db_connection()
    conn.execute('UPDATE dispatches SET shutoff_confirmed = 1 WHERE id = ?', (dispatch_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'shutoff_confirmed': 1})

@app.route('/api/dispatches/<int:dispatch_id>/complete-repair', methods=['POST'])
def complete_repair(dispatch_id):
    data = request.json or {}
    parts_cost = float(data.get('parts_cost', 65.0))
    labor_hours = float(data.get('labor_hours', 1.5))
    repair_notes = data.get('repair_notes', 'Replaced ruptured 3/4" copper elbow with Ridgid ProPress copper coupling. Tested system at 65 PSI static pressure with zero leaks.')
    
    conn = get_db_connection()
    dispatch = conn.execute('''
        SELECT d.*, p.hourly_rate FROM dispatches d
        JOIN plumbers p ON d.plumber_id = p.id
        WHERE d.id = ?
    ''', (dispatch_id,)).fetchone()
    
    if not dispatch:
        conn.close()
        return jsonify({'error': 'Dispatch not found'}), 404

    hourly_rate = dispatch['hourly_rate'] or 160.0
    dispatch_fee = dispatch['dispatch_fee']
    labor_cost = labor_hours * hourly_rate
    final_total = dispatch_fee + labor_cost + parts_cost

    conn.execute('''
        UPDATE dispatches
        SET status = 'completed',
            final_invoice_amount = ?,
            after_repair_notes = ?,
            completed_at = datetime('now')
        WHERE id = ?
    ''', (final_total, repair_notes, dispatch_id))
    conn.commit()
    conn.close()

    return jsonify({
        'success': True,
        'final_invoice_amount': final_total,
        'parts_cost': parts_cost,
        'labor_cost': labor_cost,
        'dispatch_fee': dispatch_fee,
        'warranty_days': 90
    })

@app.route('/api/dispatches/<int:dispatch_id>/release-escrow', methods=['POST'])
def release_escrow(dispatch_id):
    conn = get_db_connection()
    conn.execute('''
        UPDATE dispatches
        SET status = 'completed'
        WHERE id = ?
    ''', (dispatch_id,))
    conn.commit()
    conn.close()
    return jsonify({
        'success': True,
        'message': 'Escrow funds successfully released to verified plumber. 90-Day Guarantee Certificate activated.',
        'warranty_certificate_id': f"WARR-90D-{dispatch_id:04d}"
    })

@app.route('/api/plumber/toggle-duty', methods=['POST'])
def toggle_plumber_duty():
    data = request.json or {}
    plumber_id = int(data.get('plumber_id', 1))
    is_on_call = 1 if data.get('is_on_call') else 0

    conn = get_db_connection()
    conn.execute('UPDATE plumbers SET is_on_call = ? WHERE id = ?', (is_on_call, plumber_id))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'plumber_id': plumber_id, 'is_on_call': is_on_call})

@app.route('/api/plumber/verify', methods=['POST'])
def admin_verify_plumber():
    data = request.json or {}
    plumber_id = int(data.get('plumber_id'))
    license_verified = int(data.get('license_verified', 1))
    insurance_verified = int(data.get('insurance_verified', 1))
    background_checked = int(data.get('background_checked', 1))

    conn = get_db_connection()
    conn.execute('''
        UPDATE plumbers
        SET license_verified = ?, insurance_verified = ?, background_checked = ?
        WHERE id = ?
    ''', (license_verified, insurance_verified, background_checked, plumber_id))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'plumber_id': plumber_id})

@app.route('/api/stats', methods=['GET'])
def get_stats():
    conn = get_db_connection()
    active_on_call = conn.execute('SELECT COUNT(*) FROM plumbers WHERE is_on_call = 1 AND license_verified = 1').fetchone()[0]
    total_verified = conn.execute('SELECT COUNT(*) FROM plumbers WHERE license_verified = 1 AND insurance_verified = 1').fetchone()[0]
    total_dispatches = conn.execute('SELECT COUNT(*) FROM dispatches').fetchone()[0]
    avg_rating = conn.execute('SELECT AVG(rating) FROM plumbers').fetchone()[0] or 4.9
    conn.close()

    return jsonify({
        'active_on_call_plumbers': active_on_call,
        'total_verified_trades': total_verified,
        'total_emergency_rescues': 420 + total_dispatches,
        'avg_eta_minutes': 18,
        'avg_customer_rating': round(avg_rating, 2),
        'anti_gouge_savings_percent': '54% Lower Than Unregulated Brokers',
        'compliance_rate': '100% Vetted (Master & Journeyman)'
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print(f"HydroRescue Server running at http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)
