// biomed-billing-daisy.js - Billing management for daisyUI
var billingModal = document.getElementById("billingModal");
var currentBilling = null;
var billingName = document.getElementById("billingName");
var billingEmail = document.getElementById("billingEmail");
var billingAddress = document.getElementById("billingAddress");
var billingPhone = document.getElementById("billingPhone");
var billingTaxID = document.getElementById("billingTaxID");
var masterBillings = [];
var mainContactSelect = document.getElementById("mainContactsSelecter");
var ContactsDummy = [];

// Clear modal fields
function clearBillingModal() {
    billingName.value = '';
    billingEmail.value = '';
    billingAddress.value = '';
    billingPhone.value = "";
    billingTaxID.value = "";
    currentBilling = null;
    if (mainContactSelect) {
        mainContactSelect.value = '';
    }
    console.log('Billing Modal cleared');
}

// Open billing modal for adding
function openBillingModal(billingId = null) {
    clearBillingModal();
    if (billingId) {
        var foundBilling = masterBillings.find(b => b.Id === billingId);
        if (foundBilling) {
            billingName.value = foundBilling.Name || '';
            billingEmail.value = foundBilling.Email || '';
            billingAddress.value = foundBilling.Address || '';
            billingPhone.value = foundBilling.Phone || '';
            billingTaxID.value = foundBilling.TaxID || '';
            if (mainContactSelect && foundBilling.ContactId) {
                mainContactSelect.value = foundBilling.ContactId;
            }
            currentBilling = foundBilling;
        }
    }
    billingModal.showModal();
}

// Open billing modal with pre-selected contact (called from Contact table)
function openBillingModalForContact(contactId, contactName) {
    clearBillingModal();
    // Wait for dropdown to be populated
    setTimeout(() => {
        if (mainContactSelect) {
            mainContactSelect.value = contactId;
        }
        billingModal.showModal();
    }, 100);
}

// Delete billing
function deleteBilling() {
    if (!currentBilling) return;
    
    if (!confirm('ต้องการลบ Billing นี้หรือไม่?')) return;
    
    var billingId = currentBilling.Id;
    var xhr = new XMLHttpRequest();
    var urlx = url + '/biomedapi/billinginformations/delete';
    var method = 'POST';

    xhr.open(method, urlx, true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.setRequestHeader('Authorization', 'Bearer ' + readToken());

    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4) {
            if (xhr.status === 200) {
                console.log('Billing deleted successfully');
                xalert('Billing deleted successfully', 0, 5000);
                masterBillings = masterBillings.filter(b => b.Id !== billingId);
                renderBillingTable();
            } else {
                console.error('Error deleting billing:', xhr.responseText);
                xalert('Error deleting billing', 1, -1);
            }
        }
    };

    xhr.send(JSON.stringify({id: billingId}));
    clearBillingModal();
    billingModal.close();
}

// Add or update billing
function addBilling() {
    var billing = {
        contactID: parseInt(mainContactSelect.value) || null,
        ContactId: parseInt(mainContactSelect.value) || null,
        Name: billingName.value || null,
        Email: billingEmail.value || null,
        Address: billingAddress.value || null,
        Phone: billingPhone.value || null,
        TaxID: billingTaxID.value || null
    };

    if (currentBilling !== null) {
        billing.Id = currentBilling.Id;
    }

    addBillingRequest(billing);
    billingModal.close();
}

// API request to add/update billing
function addBillingRequest(billing) {
    var xhr = new XMLHttpRequest();
    var urlx = billing.Id ? '/biomedapi/billinginformations/update' : '/biomedapi/billinginformations/create';
    var method = 'POST';

    xhr.open(method, url + urlx, true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.setRequestHeader('Authorization', 'Bearer ' + readToken());

    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4) {
            if (xhr.status === 200) {
                console.log('Billing added/updated successfully');
                xalert('Billing added/updated successfully', 0, 5000);
                
                if (billing.Id) {
                    // Update existing
                    var idx = masterBillings.findIndex(b => b.Id === billing.Id);
                    if (idx >= 0) {
                        masterBillings[idx] = { ...masterBillings[idx], ...billing };
                    }
                } else {
                    // New billing
                    billing.Id = parseInt(xhr.responseText);
                    masterBillings.push(billing);
                }
                
                renderBillingTable();
                
                // Force refresh billings
                getBillings((err, billings) => {
                    if (err) {
                        console.error(err);
                        return;
                    }
                    console.log("Force Update Billing", billings);
                    masterBillings = billings;
                    renderBillingTable();
                }, true);
                
            } else {
                console.error('Error adding/updating billing:', xhr.responseText);
                xalert('Error adding/updating billing', 1, -1);
            }
        }
    };

    xhr.send(JSON.stringify(billing));
}

// Get contact name by ID
function getContactName(contactId) {
    if (!contactId) return '-';
    var contact = ContactsDummy.find(c => c.Id === contactId);
    return contact ? escapeHtml(contact.Name) : `Contact #${contactId}`;
}

// Render billing table
function renderBillingTable() {
    var tbody = document.getElementById('billingTableBody');
    
    // Update statistics
    if (typeof updateContactStats === 'function') {
        updateContactStats();
    }
    
    if (!masterBillings || masterBillings.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="text-center py-8 text-base-content/60">
                    <i class="fas fa-inbox text-4xl mb-2"></i><br>
                    ไม่พบข้อมูล Billing
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = masterBillings.map(billing => `
        <tr class="hover:bg-base-200 cursor-pointer" onclick="editBillingRow(${billing.Id})">
            <td class="font-mono text-xs">${billing.Id || '-'}</td>
            <td><span class="badge badge-ghost badge-sm">${getContactName(billing.ContactId)}</span></td>
            <td class="font-semibold">${escapeHtml(billing.Name) || '-'}</td>
            <td><a href="mailto:${billing.Email || ''}" class="link link-secondary">${escapeHtml(billing.Email) || '-'}</a></td>
            <td class="max-w-[200px] truncate">${escapeHtml(billing.Address) || '-'}</td>
            <td><a href="tel:${billing.Phone || ''}" class="link">${escapeHtml(billing.Phone) || '-'}</a></td>
            <td class="font-mono text-xs">${escapeHtml(billing.TaxID) || '-'}</td>
            <td>
                <button class="btn btn-ghost btn-xs" onclick="event.stopPropagation(); editBillingRow(${billing.Id})">
                    <i class="fas fa-edit text-secondary"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

// Edit billing row
function editBillingRow(billingId) {
    var foundBilling = masterBillings.find(b => b.Id === billingId);
    if (foundBilling) {
        currentBilling = foundBilling;
        billingName.value = foundBilling.Name || '';
        billingEmail.value = foundBilling.Email || '';
        billingAddress.value = foundBilling.Address || '';
        billingPhone.value = foundBilling.Phone || '';
        billingTaxID.value = foundBilling.TaxID || '';
        if (mainContactSelect && foundBilling.ContactId) {
            mainContactSelect.value = foundBilling.ContactId;
        }
        billingModal.showModal();
    }
}

// HTML escape helper (if not already defined)
if (typeof escapeHtml === 'undefined') {
    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize billing (called from contact page)
function callBilling() {
    // Load billings
    getBillings((err, billings) => {
        if (err) {
            console.error(err);
            xalert("Error loading billings", 1, -1);
            return;
        }
        console.log('Billings loaded:', billings);
        masterBillings = billings;
        renderBillingTable();
    }, true);

    // Load contacts for dropdown
    loadContactsDropdown();
}

// Load contacts for dropdown
function loadContactsDropdown() {
    getContacts((err, contacts) => {
        if (err) {
            console.error("Failed to fetch contacts:", err);
            return;
        }
        
        ContactsDummy = contacts;
        
        if (mainContactSelect) {
            mainContactSelect.innerHTML = '<option value="" disabled selected>Select Contact</option>';
            contacts.forEach(contact => {
                const option = document.createElement("option");
                option.value = contact.Id;
                option.textContent = contact.Name;
                if (contact.Position) {
                    option.textContent += ` (${contact.Position})`;
                }
                mainContactSelect.appendChild(option);
            });
        }
        
        // Re-render billing table with contact names
        renderBillingTable();
    });
}
