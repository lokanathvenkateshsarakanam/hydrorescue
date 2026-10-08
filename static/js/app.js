// HydroRescue Main Client Application

let mapInstance = null;
let currentSelectedCategoryId = 1;
let activeCategories = [];
let activeDispatchData = null;

// ==========================================
// 1. HOMEOWNER PORTAL LOGIC
// ==========================================

async function initHomeownerApp() {
    await loadCategories();
    await loadPlumbersList();
    initRadarMap();
    checkActiveDispatch();
}

async function loadCategories() {
    try {
        const res = await fetch('/api/categories');
        const categories = await res.json();
        activeCategories = categories;
        renderCategoryCards(categories);
        if (categories.length > 0) {
            selectCategory(categories[0].id);
        }
    } catch (err) {
        console.error('Error loading categories:', err);
    }
}

function renderCategoryCards(categories) {
    const container = document.getElementById('category-cards-container');
    if (!container) return;

    container.innerHTML = categories.map(cat => {
        const isSelected = cat.id === currentSelectedCategoryId;
        const severityBadgeColor = cat.severity_level === 'CRITICAL' ? 'bg-rose-500/20 text-rose-300 border-rose-500/30' : 'bg-amber-500/20 text-amber-300 border-amber-500/30';
        
        return `
            <div onclick="selectCategory(${cat.id})" class="p-3.5 rounded-xl border transition-all cursor-pointer flex items-center justify-between gap-3 ${isSelected ? 'bg-slate-700/80 border-cyan-400 shadow-md ring-1 ring-cyan-400/50' : 'bg-slate-900/60 border-slate-700 hover:border-slate-600'}">
                <div class="flex items-start gap-3">
                    <div class="p-2 rounded-lg bg-slate-800 text-cyan-400 border border-slate-700 shrink-0 mt-0.5">
                        <i data-lucide="${cat.icon || 'wrench'}" class="w-4 h-4"></i>
                    </div>
                    <div>
                        <div class="flex items-center gap-2">
                            <h4 class="text-xs font-bold text-white">${cat.title}</h4>
                            <span class="text-[9px] font-extrabold px-1.5 py-0.2 rounded border ${severityBadgeColor}">${cat.severity_level}</span>
                        </div>
                        <p class="text-[11px] text-slate-400 mt-0.5 line-clamp-1">${cat.description}</p>
                    </div>
                </div>
                <div class="text-right shrink-0">
                    <div class="text-xs font-black text-cyan-400">Cap: $${cat.max_price_cap}</div>
                    <div class="text-[10px] text-rose-400 line-through">$${cat.market_gouged_price} broker</div>
                </div>
            </div>
        `;
    }).join('');

    if (window.lucide) lucide.createIcons();
}

function selectCategory(catId) {
    currentSelectedCategoryId = catId;
    const cat = activeCategories.find(c => c.id === catId);
    if (!cat) return;

    // Update Price Summary UI
    const feeElem = document.getElementById('price-dispatch-fee');
    const laborElem = document.getElementById('price-labor-est');
    const partsElem = document.getElementById('price-parts-est');
    const capElem = document.getElementById('price-total-cap');
    const gougeElem = document.getElementById('price-market-gouge');

    if (feeElem) feeElem.innerText = `$${cat.base_dispatch_fee.toFixed(2)}`;
    if (laborElem) laborElem.innerText = `$${(cat.est_labor_hours * cat.est_labor_rate).toFixed(2)} (${cat.est_labor_hours}h @ $${cat.est_labor_rate}/hr)`;
    if (partsElem) partsElem.innerText = `$${cat.est_parts_min.toFixed(0)} - $${cat.est_parts_max.toFixed(0)}`;
    if (capElem) capElem.innerText = `$${cat.max_price_cap.toFixed(2)} MAX`;
    if (gougeElem) gougeElem.innerText = `$${cat.market_gouged_price.toFixed(2)}+`;

    // Re-render highlight
    renderCategoryCards(activeCategories);
}

async function submitEmergencyDispatch(e) {
    e.preventDefault();

    const name = document.getElementById('cust-name').value;
    const phone = document.getElementById('cust-phone').value;
    const address = document.getElementById('cust-address').value;
    const desc = document.getElementById('cust-desc').value;
    const shutoffCheck = document.getElementById('cust-shutoff-check').checked;

    const btn = document.getElementById('btn-submit-sos');
    btn.disabled = true;
    btn.innerHTML = `<i data-lucide="loader" class="w-5 h-5 animate-spin"></i> Matching Nearest Verified Plumber...`;
    if (window.lucide) lucide.createIcons();

    try {
        const res = await fetch('/api/dispatches/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                customer_name: name,
                customer_phone: phone,
                address: address,
                description: desc,
                category_id: currentSelectedCategoryId,
                shutoff_confirmed: shutoffCheck
            })
        });
        const result = await res.json();
        if (result.success) {
            window.soundFX.playEmergencyPing();
            alert(`EMERGENCY DISPATCH CONFIRMED!\n\nReference: ${result.dispatch_code}\nETA: ${result.eta_minutes} minutes\nEscrow Deposit Secured: $${result.escrow_deposit}\n\n${result.message}`);
            await checkActiveDispatch();
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    } catch (err) {
        alert('Failed to submit emergency dispatch. Please call (555) 019-9110.');
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<i data-lucide="zap" class="w-5 h-5"></i> Dispatch Verified Emergency Plumber Now`;
        if (window.lucide) lucide.createIcons();
    }
}

async function checkActiveDispatch() {
    try {
        const res = await fetch('/api/dispatches/active');
        const d = await res.json();
        if (!d || d.status === 'completed' || d.status === 'cancelled') {
            document.getElementById('active-dispatch-banner')?.classList.add('hidden');
            return;
        }

        activeDispatchData = d;
        const banner = document.getElementById('active-dispatch-banner');
        if (!banner) return;
        banner.classList.remove('hidden');

        document.getElementById('dispatch-code-badge').innerText = d.dispatch_code;
        document.getElementById('dispatch-plumber-name').innerText = `${d.plumber_name || 'Assigned Technician'} (${d.business_name || 'Emergency Squad'})`;
        document.getElementById('dispatch-category-text').innerText = `${d.category_title} • ${d.address}`;
        document.getElementById('dispatch-eta-text').innerText = `${d.eta_minutes} mins`;
        document.getElementById('dispatch-call-btn').href = `tel:${d.plumber_phone || '5550000000'}`;
        
        if (d.plumber_avatar) {
            document.getElementById('dispatch-plumber-avatar').src = d.plumber_avatar;
        }

        // Status badge
        const badge = document.getElementById('dispatch-status-badge');
        const stepAcc = document.getElementById('step-accepted');
        const stepEn = document.getElementById('step-enroute');
        const stepArr = document.getElementById('step-arrived');
        const stepComp = document.getElementById('step-completed');

        // Reset step colors
        [stepAcc, stepEn, stepArr, stepComp].forEach(el => {
            if (el) {
                const circle = el.querySelector('div');
                circle.className = 'w-7 h-7 rounded-full bg-slate-800 border-2 border-slate-600 flex items-center justify-center text-slate-400 text-[10px] font-bold';
            }
        });

        const setStepActive = (el) => {
            if (!el) return;
            const circle = el.querySelector('div');
            circle.className = 'w-7 h-7 rounded-full bg-cyan-500 border-2 border-white flex items-center justify-center text-white text-[10px] font-black shadow-lg shadow-cyan-500/50';
        };

        if (d.status === 'accepted') {
            badge.className = 'text-xs font-bold px-2.5 py-0.5 rounded-md bg-amber-500/20 text-amber-300 border border-amber-500/30';
            badge.innerText = 'DISPATCH ACCEPTED';
            setStepActive(stepAcc);
        } else if (d.status === 'en_route') {
            badge.className = 'text-xs font-bold px-2.5 py-0.5 rounded-md bg-cyan-500/20 text-cyan-300 border border-cyan-500/30';
            badge.innerText = 'TRUCK EN ROUTE';
            setStepActive(stepAcc);
            setStepActive(stepEn);
        } else if (d.status === 'arrived' || d.status === 'in_progress') {
            badge.className = 'text-xs font-bold px-2.5 py-0.5 rounded-md bg-blue-500/20 text-blue-300 border border-blue-500/30';
            badge.innerText = 'ON-SITE / DIAGNOSING';
            setStepActive(stepAcc);
            setStepActive(stepEn);
            setStepActive(stepArr);
            // Show Escrow release button
            document.getElementById('btn-release-escrow')?.classList.remove('hidden');
        }

        // Shutoff confirm button label
        const shutLabel = document.getElementById('shutoff-btn-label');
        if (d.shutoff_confirmed) {
            shutLabel.innerText = 'Water Shutoff: CONFIRMED';
            document.getElementById('btn-water-shut-confirm').classList.add('bg-emerald-700/60', 'text-white');
        } else {
            shutLabel.innerText = 'Confirm Water Is Shut Off';
        }

        if (window.lucide) lucide.createIcons();
    } catch (err) {
        console.error('Active dispatch error:', err);
    }
}

async function confirmWaterShutoff() {
    if (!activeDispatchData) {
        alert('Water shut off confirmed. Your dispatcher has been alerted.');
        return;
    }
    try {
        await fetch(`/api/dispatches/${activeDispatchData.id}/shutoff-confirm`, { method: 'POST' });
        window.soundFX.playSuccessPing();
        alert('Thank you! Confirmed water is shut off. This has been updated on the plumber\'s live dashboard.');
        checkActiveDispatch();
    } catch(e) {
        console.error(e);
    }
}

async function releaseEscrowPayment() {
    if (!activeDispatchData) return;
    const confirmRelease = confirm(`Confirm completion of emergency repair and release escrow deposit ($${activeDispatchData.escrow_deposit})?\n\nThis automatically issues your official 90-Day Emergency Workmanship Warranty.`);
    if (!confirmRelease) return;

    try {
        const res = await fetch(`/api/dispatches/${activeDispatchData.id}/release-escrow`, { method: 'POST' });
        const data = await res.json();
        window.soundFX.playSuccessPing();
        alert(`SUCCESS!\n\n${data.message}\nWarranty Certificate: ${data.warranty_certificate_id}`);
        location.reload();
    } catch (err) {
        alert('Error releasing escrow.');
    }
}

// Map Initialization
function initRadarMap() {
    const mapContainer = document.getElementById('radar-map');
    if (!mapContainer) return;

    const sfCoords = [37.7749, -122.4194];
    mapInstance = L.map('radar-map').setView(sfCoords, 13);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors'
    }).addTo(mapInstance);

    // Homeowner Location Marker
    const homeIcon = L.divIcon({
        className: 'custom-home-pin',
        html: `
            <div class="relative flex items-center justify-center">
                <span class="absolute w-8 h-8 rounded-full bg-cyan-500/30 animate-ping"></span>
                <div class="w-6 h-6 rounded-full bg-cyan-500 border-2 border-white flex items-center justify-center text-white text-[10px] font-bold shadow-lg">
                    H
                </div>
            </div>
        `,
        iconSize: [24, 24]
    });
    L.marker(sfCoords, { icon: homeIcon }).addTo(mapInstance).bindPopup("<b>Your Emergency Location</b><br>452 Castro St").openPopup();
}

async function loadPlumbersList() {
    try {
        const res = await fetch('/api/plumbers');
        const plumbers = await res.json();
        
        // Update stats
        const activeCount = plumbers.filter(p => p.is_on_call).length;
        const statsCount = document.getElementById('stats-active-count');
        if (statsCount) statsCount.innerText = `${activeCount} On-Duty`;

        renderPlumbers(plumbers);
        renderPlumbersOnMap(plumbers);
    } catch (err) {
        console.error('Error loading plumbers:', err);
    }
}

function renderPlumbers(plumbers) {
    const container = document.getElementById('plumbers-list-container');
    if (!container) return;

    container.innerHTML = plumbers.map(p => {
        return `
            <div class="p-4 bg-slate-900/70 border border-slate-700/80 rounded-xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 hover:border-slate-600 transition-colors">
                <div class="flex items-start gap-3.5">
                    <div class="relative shrink-0">
                        <img src="${p.avatar_url || 'https://images.unsplash.com/photo-1621905251189-08b45d6a269e?w=100'}" alt="${p.name}" class="w-12 h-12 rounded-xl object-cover border border-slate-600">
                        <span class="absolute -bottom-1 -right-1 w-3.5 h-3.5 rounded-full border-2 border-slate-900 ${p.is_on_call ? 'bg-emerald-500' : 'bg-slate-500'}"></span>
                    </div>
                    <div>
                        <div class="flex flex-wrap items-center gap-2">
                            <h5 class="text-sm font-bold text-white">${p.name}</h5>
                            <span class="text-[10px] bg-emerald-500/20 text-emerald-400 font-bold px-2 py-0.2 rounded border border-emerald-500/30 flex items-center gap-1">
                                <i data-lucide="shield-check" class="w-3 h-3"></i> ${p.license_type}
                            </span>
                            <span class="text-xs text-amber-400 font-bold flex items-center gap-0.5">
                                <i data-lucide="star" class="w-3 h-3 fill-amber-400"></i> ${p.rating} (${p.reviews_count})
                            </span>
                        </div>
                        <p class="text-xs text-slate-400 mt-0.5">${p.business_name}</p>
                        <div class="flex flex-wrap gap-2 text-[11px] text-slate-400 mt-1.5">
                            <span class="text-slate-300 font-medium"><strong class="text-white">Fee:</strong> $${p.emergency_dispatch_fee}</span>
                            <span>•</span>
                            <span class="text-slate-300 font-medium"><strong class="text-white">Labor:</strong> $${p.hourly_rate}/hr</span>
                            <span>•</span>
                            <span class="text-cyan-300 font-mono">${p.license_no}</span>
                        </div>
                    </div>
                </div>

                <div class="flex sm:flex-col items-center sm:items-end justify-between w-full sm:w-auto gap-2">
                    <span class="text-[11px] font-bold px-2 py-0.5 rounded ${p.is_on_call ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-slate-800 text-slate-400'}">
                        ${p.is_on_call ? 'ON-CALL (READY)' : 'STANDBY'}
                    </span>
                    <button onclick="openCredentialsModal(${p.id})" class="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-cyan-300 rounded-lg text-xs font-semibold flex items-center gap-1 transition-colors border border-slate-700">
                        <i data-lucide="file-check" class="w-3.5 h-3.5"></i>
                        <span>Audit License & Insurance</span>
                    </button>
                </div>
            </div>
        `;
    }).join('');

    if (window.lucide) lucide.createIcons();
}

function renderPlumbersOnMap(plumbers) {
    if (!mapInstance) return;

    plumbers.forEach(p => {
        const truckIcon = L.divIcon({
            className: 'custom-truck-pin',
            html: `
                <div class="relative flex items-center justify-center">
                    <span class="absolute w-8 h-8 rounded-full ${p.is_on_call ? 'bg-emerald-500/20 animate-ping' : ''}"></span>
                    <div class="w-7 h-7 rounded-xl ${p.is_on_call ? 'bg-emerald-600' : 'bg-slate-700'} border-2 border-white flex items-center justify-center text-white shadow-lg">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17a2 2 0 11-4 0 2 2 0 014 0zM19 17a2 2 0 11-4 0 2 2 0 014 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16V6a1 1 0 00-1-1H4a1 1 0 00-1 1v10a1 1 0 001 1h1m8-1a1 1 0 01-1 1H9m4-1V8a1 1 0 011-1h2.586a1 1 0 01.707.293l3.414 3.414a1 1 0 01.293.707V16a1 1 0 01-1 1h-1m-6-1a1 1 0 001 1h1M5 17a2 2 0 104 0m-4 0a2 2 0 114 0m6 0a2 2 0 104 0m-4 0a2 2 0 114 0"/></svg>
                    </div>
                </div>
            `,
            iconSize: [28, 28]
        });

        const marker = L.marker([p.latitude, p.longitude], { icon: truckIcon }).addTo(mapInstance);
        marker.bindPopup(`
            <div class="p-1 space-y-1">
                <div class="font-bold text-white text-xs">${p.name}</div>
                <div class="text-[11px] text-cyan-400 font-semibold">${p.license_type} (${p.license_no})</div>
                <div class="text-[10px] text-slate-300">Rate: $${p.hourly_rate}/hr • Fee: $${p.emergency_dispatch_fee}</div>
                <div class="text-[10px] text-emerald-400 font-bold">${p.is_on_call ? '● Active On-Duty' : '○ Standby'}</div>
            </div>
        `);
    });
}

async function openCredentialsModal(plumberId) {
    try {
        const res = await fetch(`/api/plumbers/${plumberId}`);
        const p = await res.json();
        
        document.getElementById('modal-plumber-name').innerText = p.name;
        document.getElementById('modal-business-name').innerText = p.business_name;
        document.getElementById('modal-license-info').innerText = `${p.license_type} • State #${p.license_no} (Active)`;
        document.getElementById('modal-insurance-info').innerText = `${p.insurance_carrier} (#${p.insurance_policy_no}) - ${p.insurance_coverage}`;
        document.getElementById('modal-bg-info').innerText = `Clear (Audited: ${p.background_check_date})`;

        const toolsContainer = document.getElementById('modal-tools-list');
        toolsContainer.innerHTML = p.equipped_tools.map(tool => `
            <span class="px-2.5 py-1 bg-slate-800 text-slate-300 border border-slate-700 rounded-lg text-[11px] font-medium flex items-center gap-1">
                <i data-lucide="check" class="w-3 h-3 text-emerald-400"></i> ${tool}
            </span>
        `).join('');

        document.getElementById('credentials-modal').classList.remove('hidden');
        if (window.lucide) lucide.createIcons();
    } catch(err) {
        console.error(err);
    }
}

function closeCredentialsModal() {
    document.getElementById('credentials-modal').classList.add('hidden');
}


// ==========================================
// 2. PLUMBER PORTAL LOGIC
// ==========================================

let plumberIsOnDuty = true;
let currentPlumberDispatchId = 1;

async function initPlumberPortal() {
    try {
        const res = await fetch('/api/dispatches/active');
        const d = await res.json();
        if (d) {
            currentPlumberDispatchId = d.id;
            document.getElementById('job-dispatch-code').innerText = d.dispatch_code;
            document.getElementById('job-status-pill').innerText = `${d.status.toUpperCase()} (ETA: ${d.eta_minutes}m)`;
            document.getElementById('job-category').innerText = d.category_title;
            document.getElementById('job-address').innerText = d.address;
            document.getElementById('job-customer').innerText = `${d.customer_name} • ${d.customer_phone}`;
            
            const shutoffElem = document.getElementById('job-shutoff-status');
            if (d.shutoff_confirmed) {
                shutoffElem.innerHTML = `<i data-lucide="check-circle" class="w-4 h-4 text-emerald-400"></i> Main Valve CLOSED by Homeowner`;
                shutoffElem.className = 'text-emerald-400 font-bold flex items-center gap-1.5';
            } else {
                shutoffElem.innerHTML = `<i data-lucide="alert-circle" class="w-4 h-4 text-rose-400"></i> Main Valve UNCONFIRMED (Bring Curb Key)`;
                shutoffElem.className = 'text-rose-400 font-bold flex items-center gap-1.5';
            }
        }
        
        // Listen to invoice inputs to calculate payout live
        const laborInput = document.getElementById('inv-labor-hours');
        const partsInput = document.getElementById('inv-parts-cost');
        if (laborInput && partsInput) {
            const updateCalc = () => {
                const labor = parseFloat(laborInput.value) || 0;
                const parts = parseFloat(partsInput.value) || 0;
                const total = 89.0 + (labor * 160.0) + parts;
                document.getElementById('calc-total-invoice').innerText = `$${total.toFixed(2)}`;
            };
            laborInput.addEventListener('input', updateCalc);
            partsInput.addEventListener('input', updateCalc);
        }

        if (window.lucide) lucide.createIcons();
    } catch(err) {
        console.error(err);
    }
}

async function toggleDutyState() {
    plumberIsOnDuty = !plumberIsOnDuty;
    try {
        await fetch('/api/plumber/toggle-duty', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ plumber_id: 1, is_on_call: plumberIsOnDuty })
        });
        
        const statusText = document.getElementById('duty-status-text');
        const toggleBtn = document.getElementById('duty-toggle-btn');
        const toggleLabel = document.getElementById('duty-toggle-label');
        const statusIndicator = document.getElementById('plumber-status-indicator');

        if (plumberIsOnDuty) {
            statusText.innerText = 'ON-CALL (RECEIVING ALERTS)';
            statusText.className = 'text-sm font-black text-emerald-400';
            toggleLabel.innerText = 'Go Off-Duty';
            toggleBtn.className = 'px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-xl text-xs sm:text-sm shadow-lg shadow-emerald-900/50 transition-all flex items-center gap-2';
            statusIndicator.className = 'absolute -bottom-1 -right-1 w-4 h-4 bg-emerald-500 rounded-full border-2 border-slate-900';
            window.soundFX.playSuccessPing();
        } else {
            statusText.innerText = 'OFF-DUTY (STANDBY)';
            statusText.className = 'text-sm font-black text-slate-400';
            toggleLabel.innerText = 'Go On-Duty (Receive Calls)';
            toggleBtn.className = 'px-5 py-2.5 bg-slate-700 hover:bg-slate-600 text-white font-bold rounded-xl text-xs sm:text-sm transition-all flex items-center gap-2';
            statusIndicator.className = 'absolute -bottom-1 -right-1 w-4 h-4 bg-slate-500 rounded-full border-2 border-slate-900';
        }
    } catch(e) {
        console.error(e);
    }
}

async function updatePlumberJobStatus(status) {
    try {
        await fetch(`/api/dispatches/${currentPlumberDispatchId}/status`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status })
        });
        window.soundFX.playEmergencyPing();
        const pill = document.getElementById('job-status-pill');
        pill.innerText = `STATUS: ${status.toUpperCase()}`;
        alert(`Dispatched status updated to: ${status.toUpperCase()}. Homeowner live tracker synced.`);
    } catch(err) {
        alert('Failed to update status.');
    }
}

async function submitRepairCompletion(e) {
    e.preventDefault();
    const labor = parseFloat(document.getElementById('inv-labor-hours').value);
    const parts = parseFloat(document.getElementById('inv-parts-cost').value);
    const notes = document.getElementById('inv-notes').value;

    try {
        const res = await fetch(`/api/dispatches/${currentPlumberDispatchId}/complete-repair`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                labor_hours: labor,
                parts_cost: parts,
                repair_notes: notes
            })
        });
        const result = await res.json();
        if (result.success) {
            window.soundFX.playSuccessPing();
            alert(`REPAIR WORK COMPLETED!\n\nFinal Invoice: $${result.final_invoice_amount.toFixed(2)}\n90-Day Warranty Certificate Issued.\nHomeowner notified to release escrow.`);
            location.reload();
        }
    } catch(err) {
        alert('Failed to complete repair invoice.');
    }
}


// ==========================================
// 3. ADMIN PORTAL LOGIC
// ==========================================

async function initAdminPortal() {
    await loadAdminRegistry();
}

async function loadAdminRegistry() {
    try {
        const res = await fetch('/api/plumbers');
        const plumbers = await res.json();
        
        const countElem = document.getElementById('admin-active-count');
        if (countElem) {
            const activeCount = plumbers.filter(p => p.is_on_call).length;
            countElem.innerText = `${activeCount} Active Units`;
        }

        const tableBody = document.getElementById('admin-plumbers-table');
        if (!tableBody) return;

        tableBody.innerHTML = plumbers.map(p => {
            return `
                <tr class="hover:bg-slate-800/50 transition-colors">
                    <td class="py-3 px-3">
                        <div class="font-bold text-white">${p.name}</div>
                        <div class="text-[11px] text-slate-400">${p.business_name}</div>
                    </td>
                    <td class="py-3 px-3">
                        <span class="font-mono text-cyan-300 font-bold">${p.license_no}</span>
                        <div class="text-[10px] text-emerald-400 font-medium">State Verified</div>
                    </td>
                    <td class="py-3 px-3">
                        <div class="text-white font-medium">${p.insurance_carrier}</div>
                        <div class="text-[10px] text-slate-400">${p.insurance_coverage}</div>
                    </td>
                    <td class="py-3 px-3">
                        <span class="inline-flex items-center gap-1 text-emerald-400 font-semibold text-[11px]">
                            <i data-lucide="check" class="w-3.5 h-3.5"></i> Clear (${p.background_check_date})
                        </span>
                    </td>
                    <td class="py-3 px-3">
                        <span class="text-white font-bold">$${p.hourly_rate}/hr</span>
                        <span class="text-[10px] text-slate-400 block">Fee: $${p.emergency_dispatch_fee}</span>
                    </td>
                    <td class="py-3 px-3">
                        <button onclick="togglePlumberVerification(${p.id}, ${p.license_verified})" class="px-2.5 py-1 text-[11px] font-bold rounded-lg ${p.license_verified ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'bg-rose-500/20 text-rose-400 border border-rose-500/30'}">
                            ${p.license_verified ? 'Verified & Authorized' : 'Suspended'}
                        </button>
                    </td>
                </tr>
            `;
        }).join('');

        if (window.lucide) lucide.createIcons();
    } catch(err) {
        console.error(err);
    }
}

async function togglePlumberVerification(plumberId, currentStatus) {
    const newStatus = currentStatus ? 0 : 1;
    try {
        await fetch('/api/plumber/verify', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                plumber_id: plumberId,
                license_verified: newStatus,
                insurance_verified: newStatus,
                background_checked: newStatus
            })
        });
        await loadAdminRegistry();
    } catch(e) {
        console.error(e);
    }
}
