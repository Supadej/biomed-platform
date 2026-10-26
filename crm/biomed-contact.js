// biomed-contact.js - Contact management for daisyUI
var contactModal = document.getElementById("contactModal");
var currentContact = null;
var contactName = document.getElementById("contactName");
var contactEmail = document.getElementById("contactEmail");
var contactAddress = document.getElementById("contactAddress");
var contactPhone = document.getElementById("contactPhone");
var contactPosition = document.getElementById("contactPosition");
var contactDepartment = document.getElementById("contactDepartment");
var masterContacts = [];

// Clear modal fields
function clearContactModal() {
    contactName.value = '';
    contactEmail.value = '';
    contactAddress.value = '';
    contactPhone.value = "";
    contactPosition.value = "";
    contactDepartment.value = '';
    currentContact = null;
    console.log('Contact Modal cleared');
}

// Open contact modal for adding
function openContactModal(contactId = null) {
    clearContactModal();
    if (contactId) {
        var foundContact = masterContacts.find(c => c.Id === contactId);
        if (foundContact) {
            contactName.value = foundContact.Name || '';
            contactEmail.value = foundContact.Email || '';
            contactAddress.value = foundContact.Address || '';
            contactPhone.value = foundContact.Phone || '';
            contactPosition.value = foundContact.Position || '';
            contactDepartment.value = foundContact.Department || '';
            currentContact = foundContact;
        }
    }
    contactModal.showModal();
}

// Delete contact
function deleteContact() {
    if (!currentContact) return;
    
    if (!confirm('ต้องการลบ Contact นี้หรือไม่?')) return;
    
    var contactId = currentContact.Id;
    var xhr = new XMLHttpRequest();
    var urlx = url + '/biomedapi/contacts/delete';
    var method = 'POST';

    xhr.open(method, urlx, true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.setRequestHeader('Authorization', 'Bearer ' + readToken());

    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4) {
            if (xhr.status === 200) {
                console.log('Contact deleted successfully');
                xalert('Contact deleted successfully', 0, 5000);
                masterContacts = masterContacts.filter(c => c.Id !== contactId);
                renderContactTable();
            } else {
                console.error('Error deleting contact:', xhr.responseText);
                xalert('Error deleting contact', 1, -1);
            }
        }
    };

    xhr.send(JSON.stringify({id: contactId}));
    clearContactModal();
    contactModal.close();
}

// Add or update contact
function addContact() {
    var contact = {
        Name: contactName.value || null,
        Email: contactEmail.value || null,
        Address: contactAddress.value || null,
        Phone: contactPhone.value || null,
        Position: contactPosition.value || null,
        Department: null
    };

    if (currentContact !== null) {
        contact.Id = currentContact.Id;
    }

    addContactRequest(contact);
    contactModal.close();
}

// API request to add/update contact
function addContactRequest(contact) {
    var xhr = new XMLHttpRequest();
    var urlx = contact.Id ? '/biomedapi/contacts/update' : '/biomedapi/contacts/create';
    var method = 'POST';

    xhr.open(method, url + urlx, true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.setRequestHeader('Authorization', 'Bearer ' + readToken());

    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4) {
            if (xhr.status === 200) {
                console.log('Contact added/updated successfully');
                xalert('Contact added/updated successfully', 0, 5000);
                
                if (contact.Id) {
                    // Update existing
                    var idx = masterContacts.findIndex(c => c.Id === contact.Id);
                    if (idx >= 0) {
                        masterContacts[idx] = { ...masterContacts[idx], ...contact };
                    }
                } else {
                    // New contact
                    contact.Id = parseInt(xhr.responseText);
                    masterContacts.push(contact);
                }
                
                renderContactTable();
                
                // Force refresh contacts
                getContacts((err, contacts) => {
                    if (err) {
                        console.error(err);
                        return;
                    }
                    console.log("Force Update Contact", contacts);
                    masterContacts = contacts;
                    renderContactTable();
                }, true);
                
            } else {
                console.error('Error adding/updating contact:', xhr.responseText);
                xalert('Error adding/updating contact', 1, -1);
            }
        }
    };

    xhr.send(JSON.stringify(contact));
}

// Render contact table
function renderContactTable() {
    var tbody = document.getElementById('contactTableBody');
    
    // Update statistics
    updateContactStats();
    
    if (!masterContacts || masterContacts.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="text-center py-8 text-base-content/60">
                    <i class="fas fa-inbox text-4xl mb-2"></i><br>
                    ไม่พบข้อมูล Contact
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = masterContacts.map(contact => `
        <tr class="hover:bg-base-200 cursor-pointer" onclick="editContactRow(${contact.Id})">
            <td class="font-mono text-xs">${contact.Id || '-'}</td>
            <td class="font-semibold">${escapeHtml(contact.Name) || '-'}</td>
            <td><a href="mailto:${contact.Email || ''}" class="link link-primary">${escapeHtml(contact.Email) || '-'}</a></td>
            <td class="max-w-[200px] truncate">${escapeHtml(contact.Address) || '-'}</td>
            <td><a href="tel:${contact.Phone || ''}" class="link">${escapeHtml(contact.Phone) || '-'}</a></td>
            <td>${escapeHtml(contact.Position) || '-'}</td>
            <td>${escapeHtml(contact.DepartmentID) || '-'}</td>
            <td>
                <div class="flex gap-1">
                    <button class="btn btn-ghost btn-xs" onclick="event.stopPropagation(); editContactRow(${contact.Id})" title="Edit Contact">
                        <i class="fas fa-edit text-primary"></i>
                    </button>
                    <button class="btn btn-ghost btn-xs" onclick="event.stopPropagation(); addBillingForContact(${contact.Id}, '${escapeHtml(contact.Name)}')" title="Add Billing Address">
                        <i class="fas fa-file-invoice text-secondary"></i>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
}

// Update contact statistics
function updateContactStats() {
    var totalContacts = masterContacts ? masterContacts.length : 0;
    var totalBillings = (typeof masterBillings !== 'undefined' && masterBillings) ? masterBillings.length : 0;
    var withEmail = masterContacts ? masterContacts.filter(c => c.Email && c.Email.trim() !== '').length : 0;
    var withPhone = masterContacts ? masterContacts.filter(c => c.Phone && c.Phone.trim() !== '').length : 0;
    
    var statTotalContacts = document.getElementById('statTotalContacts');
    var statTotalBillings = document.getElementById('statTotalBillings');
    var statWithEmail = document.getElementById('statWithEmail');
    var statWithPhone = document.getElementById('statWithPhone');
    
    if (statTotalContacts) statTotalContacts.textContent = totalContacts;
    if (statTotalBillings) statTotalBillings.textContent = totalBillings;
    if (statWithEmail) statWithEmail.textContent = withEmail;
    if (statWithPhone) statWithPhone.textContent = withPhone;
}

// Edit contact row
function editContactRow(contactId) {
    var foundContact = masterContacts.find(c => c.Id === contactId);
    if (foundContact) {
        currentContact = foundContact;
        contactName.value = foundContact.Name || '';
        contactEmail.value = foundContact.Email || '';
        contactAddress.value = foundContact.Address || '';
        contactPhone.value = foundContact.Phone || '';
        contactPosition.value = foundContact.Position || '';
        contactDepartment.value = foundContact.DepartmentID || '';
        contactModal.showModal();
    }
}

// HTML escape helper
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Check permissions
    myPermission(function(err, callback) {
        if (err) {
            console.log(err);
        } else {
            console.log(callback);
            // Check export permission (contact_access === 3)
            if (callback.MainPermissions.some(obj => obj.Type === 'contact_access' && obj.Value === 3)) {
                var exportButtons = document.getElementsByClassName('export');
                for (var i = 0; i < exportButtons.length; i++) {
                    exportButtons[i].classList.remove('hidden');
                }
                console.log('export permission granted');
            } else {
                var exportButtons = document.getElementsByClassName('export');
                for (var i = 0; i < exportButtons.length; i++) {
                    exportButtons[i].classList.add('hidden');
                }
                console.log('export permission denied');
            }
        }
    });

    // Load contacts
    getContacts((err, contacts) => {
        if (err) {
            console.error(err);
            xalert("Error loading contacts", 1, -1);
            return;
        }
        console.log('Contacts loaded:', contacts);
        masterContacts = contacts;
        renderContactTable();
    }, true);

    // Call billing initialization
    if (typeof callBilling === 'function') {
        callBilling();
    }
});

// Function to add billing for specific contact
function addBillingForContact(contactId, contactName) {
    if (typeof openBillingModalForContact === 'function') {
        openBillingModalForContact(contactId, contactName);
    } else {
        // Fallback - open billing modal with pre-selected contact
        clearBillingModal();
        var mainContactSelect = document.getElementById("mainContactsSelecter");
        if (mainContactSelect) {
            mainContactSelect.value = contactId;
        }
        document.getElementById("billingModal").showModal();
    }
}
