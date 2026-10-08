from app import app
import json

def test_routes():
    client = app.test_client()

    print("[1] Testing Page Routes...")
    routes = ['/', '/plumber', '/admin', '/shutoff-guide']
    for r in routes:
        res = client.get(r)
        assert res.status_code == 200, f"Route {r} failed with status {res.status_code}"
        print(f"  [PASS] {r} returned HTTP 200")

    print("\n[2] Testing API Endpoints...")
    # Test categories
    res = client.get('/api/categories')
    assert res.status_code == 200
    categories = res.get_json()
    assert len(categories) > 0, "No categories returned"
    print(f"  [PASS] /api/categories returned {len(categories)} categories")

    # Test plumbers
    res = client.get('/api/plumbers')
    assert res.status_code == 200
    plumbers = res.get_json()
    assert len(plumbers) > 0, "No plumbers returned"
    print(f"  [PASS] /api/plumbers returned {len(plumbers)} verified plumbers")

    # Test active dispatch
    res = client.get('/api/dispatches/active')
    assert res.status_code == 200
    active = res.get_json()
    assert active is not None, "Active dispatch should exist"
    print(f"  [PASS] /api/dispatches/active returned dispatch {active['dispatch_code']} (Status: {active['status']})")

    # Test stats
    res = client.get('/api/stats')
    assert res.status_code == 200
    stats = res.get_json()
    print(f"  [PASS] /api/stats: {stats['active_on_call_plumbers']} plumbers active, compliance: {stats['compliance_rate']}")

    # Test dispatch creation
    print("\n[3] Testing Emergency Dispatch Workflow...")
    res = client.post('/api/dispatches/create', json={
        'customer_name': 'Test User',
        'customer_phone': '(555) 999-0000',
        'address': '789 Pine St, San Francisco, CA',
        'category_id': 1,
        'description': 'Main valve ruptured at 3 AM',
        'shutoff_confirmed': True
    })
    assert res.status_code == 200
    created = res.get_json()
    dispatch_id = created['dispatch_id']
    print(f"  [PASS] Emergency dispatch created: {created['dispatch_code']}, Escrow hold: ${created['escrow_deposit']}")

    # Test advancing status
    res = client.post(f'/api/dispatches/{dispatch_id}/status', json={'status': 'en_route'})
    assert res.status_code == 200
    print("  [PASS] Status updated to 'en_route'")

    # Test shutoff confirm
    res = client.post(f'/api/dispatches/{dispatch_id}/shutoff-confirm')
    assert res.status_code == 200
    print("  [PASS] Water shutoff status confirmed")

    # Test completing repair
    res = client.post(f'/api/dispatches/{dispatch_id}/complete-repair', json={
        'labor_hours': 1.5,
        'parts_cost': 75.0,
        'repair_notes': 'Repaired leak with ProPress coupling.'
    })
    assert res.status_code == 200
    completed = res.get_json()
    print(f"  [PASS] Repair completed. Final invoice: ${completed['final_invoice_amount']} (Warranty: {completed['warranty_days']} days)")

    # Test releasing escrow
    res = client.post(f'/api/dispatches/{dispatch_id}/release-escrow')
    assert res.status_code == 200
    escrow = res.get_json()
    print(f"  [PASS] Escrow released: {escrow['warranty_certificate_id']}")

    print("\nALL VERIFICATION TESTS PASSED SUCCESSFULLY!")

if __name__ == '__main__':
    test_routes()
