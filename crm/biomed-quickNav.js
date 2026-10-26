/**
 * biomed-quickNav.js
 * Quick Navigation System - Bookmark/Shortcut for pages with URL parameters
 * 
 * Features:
 * - Save current page with URL parameters as shortcut
 * - Manage shortcuts (view, navigate, delete)
 * - Keyboard shortcut: Ctrl+K to open
 * - Auto-inject navbar button and modal
 */

// ===== GLOBAL VARIABLES =====
let quickNavShortcuts = [];
let quickNavUserId = null;
let quickNavModalInjected = false;

// ===== PAGE TYPE DETECTION =====
const PAGE_CONFIG = {
    'crm.html': { type: 'crm-search', icon: 'fa-search', label: 'CRM Search', color: 'primary' },
    'crm-detail.html': { type: 'crm', icon: 'fa-building', label: 'CRM Lead', color: 'primary' },
    'helpdesk.html': { type: 'helpdesk-search', icon: 'fa-search', label: 'Helpdesk Search', color: 'secondary' },
    'helpdesk-detail.html': { type: 'helpdesk', icon: 'fa-ticket', label: 'Helpdesk Ticket', color: 'secondary' },
    'event.html': { type: 'event', icon: 'fa-calendar', label: 'Event', color: 'accent' },
    'project.html': { type: 'project-search', icon: 'fa-search', label: 'Project Search', color: 'info' },
    'project-overview.html': { type: 'project', icon: 'fa-project-diagram', label: 'Project', color: 'info' },
    'project-activity.html': { type: 'activity', icon: 'fa-tasks', label: 'Activity', color: 'info' },
    'contact.html': { type: 'contact-search', icon: 'fa-search', label: 'Contact Search', color: 'success' },
    'contact-detail.html': { type: 'contact', icon: 'fa-user', label: 'Contact', color: 'success' },
    'inventory.html': { type: 'inventory-search', icon: 'fa-search', label: 'Inventory Search', color: 'warning' },
    'inventory-detail.html': { type: 'inventory', icon: 'fa-box', label: 'Inventory Item', color: 'warning' },
    'visualization.html': { type: 'visualization', icon: 'fa-chart-bar', label: 'Visualization', color: 'error' },
    'd3.html': { type: 'network', icon: 'fa-project-diagram', label: 'Network', color: 'error' }
};

// ===== API FUNCTIONS =====
async function loadQuickNavShortcuts() {
    if (!quickNavUserId) {
        console.warn('QuickNav: User ID not set');
        return [];
    }
    
    try {
        const response = await fetch(`${url}/biomedapi/v2/user/GetShortcuts/${quickNavUserId}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + readToken()
            }
        });
        
        if (response.ok) {
            quickNavShortcuts = await response.json();
            return quickNavShortcuts;
        } else {
            console.error('QuickNav: Failed to load shortcuts', response.status);
            return [];
        }
    } catch (error) {
        console.error('QuickNav: Error loading shortcuts', error);
        return [];
    }
}

async function createQuickNavShortcut(name, urlParams, type) {
    if (!quickNavUserId) {
        showQuickNavAlert('ไม่สามารถบันทึกได้ กรุณา Login ใหม่', 'error');
        return false;
    }
    
    try {
        const response = await fetch(`${url}/biomedapi/v2/user/CreateShortcut`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + readToken()
            },
            body: JSON.stringify({
                Name: name,
                UrlParams: urlParams,
                Type: type,
                UserId: quickNavUserId
            })
        });
        
        if (response.ok) {
            showQuickNavAlert('บันทึก Shortcut เรียบร้อย', 'success');
            await loadQuickNavShortcuts();
            renderQuickNavList();
            return true;
        } else {
            showQuickNavAlert('เกิดข้อผิดพลาดในการบันทึก', 'error');
            return false;
        }
    } catch (error) {
        console.error('QuickNav: Error creating shortcut', error);
        showQuickNavAlert('เกิดข้อผิดพลาดในการบันทึก', 'error');
        return false;
    }
}

async function deleteQuickNavShortcut(id) {
    try {
        const response = await fetch(`${url}/biomedapi/v2/user/DeleteShortcut/${id}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + readToken()
            }
        });
        
        if (response.ok) {
            showQuickNavAlert('ลบ Shortcut เรียบร้อย', 'success');
            await loadQuickNavShortcuts();
            renderQuickNavList();
            return true;
        } else {
            showQuickNavAlert('เกิดข้อผิดพลาดในการลบ', 'error');
            return false;
        }
    } catch (error) {
        console.error('QuickNav: Error deleting shortcut', error);
        showQuickNavAlert('เกิดข้อผิดพลาดในการลบ', 'error');
        return false;
    }
}

// ===== PAGE INFO HELPERS =====
function getQuickNavPageInfo() {
    const pathname = window.location.pathname;
    const filename = pathname.split('/').pop() || 'index.html';
    
    // Trigger URL update for pages with filter functions
    // CRM page
    if (filename === 'crm.html' && typeof updateCRMQueryURL === 'function') {
        updateCRMQueryURL();
    }
    // Helpdesk page (updateQueryURL from helpdesk)
    if (filename === 'helpdesk.html' && typeof updateQueryURL === 'function') {
        // Helpdesk already updates URL in applyFilters, but ensure it's current
        // The URL should already be updated from the last filter application
    }
    
    const search = window.location.search;
    
    const config = PAGE_CONFIG[filename] || { 
        type: 'page', 
        icon: 'fa-file', 
        label: filename.replace('.html', ''),
        color: 'neutral'
    };
    
    return {
        filename,
        search,
        fullUrl: filename + search,
        ...config
    };
}

function generateShortcutName() {
    const pageInfo = getQuickNavPageInfo();
    const params = new URLSearchParams(window.location.search);
    
    // Try to get a meaningful name from the page
    let name = pageInfo.label;
    
    // For detail pages, try to get the title from the page
    if (pageInfo.type.endsWith('-detail') || ['crm', 'helpdesk', 'activity', 'contact', 'inventory', 'event', 'project'].includes(pageInfo.type)) {
        const id = params.get('id');
        if (id) {
            // Try to get title from page elements or input fields
            // First check input fields (for modals like Event)
            const inputEl = document.querySelector('#eventTitle, #leadName, #ticketTitle, #activityTitle');
            if (inputEl && inputEl.value && inputEl.value.trim()) {
                name = inputEl.value.trim().substring(0, 50);
            } else {
                // Then check text elements
                const titleEl = document.querySelector('h1, h2, .card-title, #leadName, #ticketTitle, #eventTitle, #activityTitle');
                if (titleEl && titleEl.textContent && titleEl.textContent.trim()) {
                    name = titleEl.textContent.trim().substring(0, 50);
                } else {
                    name = `${pageInfo.label} #${id}`;
                }
            }
        }
    }
    
    // For search pages, indicate it's a search
    if (pageInfo.type.endsWith('-search') && window.location.search) {
        name = `${pageInfo.label} (Filter)`;
    }
    
    return name;
}

// ===== MODAL FUNCTIONS =====
function injectQuickNavModal() {
    if (quickNavModalInjected) return;
    
    const modalHTML = `
    <dialog id="quickNavModal" class="modal">
        <div class="modal-box w-11/12 max-w-2xl">
            <!-- Header -->
            <div class="flex items-center justify-between mb-4">
                <h3 class="font-bold text-lg flex items-center gap-2">
                    <i class="fas fa-compass text-primary"></i> Quick Navigation
                </h3>
                <form method="dialog">
                    <button class="btn btn-sm btn-circle btn-ghost">✕</button>
                </form>
            </div>
            
            <!-- Alert Area -->
            <div id="quickNavAlert" class="hidden mb-3"></div>
            
            <!-- Add Current Page Button -->
            <div class="bg-base-200 rounded-lg p-3 mb-4">
                <div class="flex flex-col sm:flex-row gap-2">
                    <input type="text" id="quickNavShortcutName" class="input input-bordered input-sm flex-1" placeholder="ชื่อ Shortcut...">
                    <button class="btn btn-primary btn-sm gap-2" onclick="addCurrentPageToQuickNav()">
                        <i class="fas fa-plus"></i> บันทึกหน้านี้
                    </button>
                </div>
                <p class="text-xs text-base-content/60 mt-2 flex items-start gap-1">
                    <i class="fas fa-info-circle flex-shrink-0 mt-0.5"></i> 
                    <span id="quickNavCurrentPage" class="truncate block max-w-full">-</span>
                </p>
            </div>
            
            <!-- Shortcuts List -->
            <div class="divider text-sm">MY SHORTCUTS</div>
            <div id="quickNavList" class="space-y-2 max-h-[50vh] overflow-y-auto">
                <div class="text-center py-8 text-base-content/50">
                    <i class="fas fa-spinner fa-spin text-2xl mb-2"></i>
                    <p>กำลังโหลด...</p>
                </div>
            </div>
            
            <!-- Footer -->
            <div class="mt-4 pt-3 border-t border-base-200 text-xs text-base-content/50 flex items-center justify-between">
                <span><kbd class="kbd kbd-xs">Ctrl</kbd> + <kbd class="kbd kbd-xs">K</kbd> เพื่อเปิด QuickNav</span>
                <span id="quickNavCount">0 shortcuts</span>
            </div>
        </div>
        <form method="dialog" class="modal-backdrop">
            <button>close</button>
        </form>
    </dialog>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    quickNavModalInjected = true;
}

// Show alert inside the QuickNav modal
function showQuickNavAlert(message, type = 'info') {
    const alertEl = document.getElementById('quickNavAlert');
    if (!alertEl) return;
    
    const alertClass = {
        'success': 'alert-success',
        'error': 'alert-error',
        'warning': 'alert-warning',
        'info': 'alert-info'
    }[type] || 'alert-info';
    
    const iconClass = {
        'success': 'fa-check-circle',
        'error': 'fa-exclamation-circle',
        'warning': 'fa-exclamation-triangle',
        'info': 'fa-info-circle'
    }[type] || 'fa-info-circle';
    
    alertEl.innerHTML = `
        <div class="alert ${alertClass} py-2 text-sm">
            <i class="fas ${iconClass}"></i>
            <span>${message}</span>
        </div>
    `;
    alertEl.classList.remove('hidden');
    
    // Auto hide after 3 seconds
    setTimeout(() => {
        alertEl.classList.add('hidden');
    }, 3000);
}

function openQuickNavModal() {
    injectQuickNavModal();
    
    const modal = document.getElementById('quickNavModal');
    if (modal) {
        // Update current page info
        const pageInfo = getQuickNavPageInfo();
        const currentPageEl = document.getElementById('quickNavCurrentPage');
        if (currentPageEl) {
            currentPageEl.textContent = pageInfo.fullUrl || pageInfo.filename;
        }
        
        // Set default name
        const nameInput = document.getElementById('quickNavShortcutName');
        if (nameInput) {
            nameInput.value = generateShortcutName();
        }
        
        // Load and render shortcuts
        loadQuickNavShortcuts().then(() => {
            renderQuickNavList();
        });
        
        modal.showModal();
    }
}

function closeQuickNavModal() {
    const modal = document.getElementById('quickNavModal');
    if (modal) {
        modal.close();
    }
}

function renderQuickNavList() {
    const container = document.getElementById('quickNavList');
    const countEl = document.getElementById('quickNavCount');
    
    if (!container) return;
    
    if (quickNavShortcuts.length === 0) {
        container.innerHTML = `
            <div class="text-center py-8 text-base-content/50">
                <i class="fas fa-bookmark text-3xl mb-2"></i>
                <p>ยังไม่มี Shortcut</p>
                <p class="text-xs">กดปุ่ม "บันทึกหน้านี้" เพื่อเพิ่ม</p>
            </div>
        `;
    } else {
        container.innerHTML = quickNavShortcuts.map(shortcut => {
            const config = getConfigByType(shortcut.Type);
            return `
            <div class="flex items-center gap-3 p-3 bg-base-100 border border-base-200 rounded-lg hover:border-primary hover:shadow-sm transition-all group">
                <div class="w-10 h-10 rounded-lg bg-${config.color}/10 flex items-center justify-center flex-shrink-0">
                    <i class="fas ${config.icon} text-${config.color}"></i>
                </div>
                <div class="flex-1 min-w-0">
                    <p class="font-medium text-sm truncate">${escapeHtml(shortcut.Name || 'Untitled')}</p>
                    <p class="text-xs text-base-content/50 truncate">${escapeHtml(shortcut.UrlParams || '')}</p>
                </div>
                <div class="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button class="btn btn-ghost btn-xs btn-circle" onclick="goToQuickNavShortcut('${escapeHtml(shortcut.UrlParams)}')" title="ไปที่หน้านี้">
                        <i class="fas fa-external-link-alt"></i>
                    </button>
                    <button class="btn btn-ghost btn-xs btn-circle text-error" onclick="confirmDeleteQuickNav(${shortcut.id})" title="ลบ">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
            `;
        }).join('');
    }
    
    if (countEl) {
        countEl.textContent = `${quickNavShortcuts.length} shortcuts`;
    }
}

function getConfigByType(type) {
    for (const [filename, config] of Object.entries(PAGE_CONFIG)) {
        if (config.type === type) {
            return config;
        }
    }
    return { type: 'page', icon: 'fa-file', label: 'Page', color: 'neutral' };
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ===== ACTION FUNCTIONS =====
function addCurrentPageToQuickNav() {
    const nameInput = document.getElementById('quickNavShortcutName');
    const name = nameInput?.value?.trim() || generateShortcutName();
    const pageInfo = getQuickNavPageInfo();
    
    createQuickNavShortcut(name, pageInfo.fullUrl, pageInfo.type);
}

function goToQuickNavShortcut(urlParams) {
    if (urlParams) {
        window.location.href = urlParams;
    }
}

function confirmDeleteQuickNav(id) {
    if (confirm('ต้องการลบ Shortcut นี้หรือไม่?')) {
        deleteQuickNavShortcut(id);
    }
}

// ===== NAVBAR BUTTON INJECTION =====
function injectQuickNavButton() {
    // Find the navbar actions area (before theme dropdown or logout button)
    const navbarActions = document.querySelector('.bm-header-account');
    
    if (navbarActions && crmHas('crm.shortcuts.view')) {
        // Check if button already exists
        if (document.getElementById('quickNavBtn')) return;
        
        // Create QuickNav button
        const btn = document.createElement('button');
        btn.id = 'quickNavBtn';
        btn.className = 'sysbtn';
        btn.title = 'Quick Navigation (Ctrl+K)';
        btn.textContent = 'Quick access';
        btn.onclick = openQuickNavModal;
        
        // Insert at the beginning of actions
        navbarActions.insertBefore(btn, navbarActions.firstChild);
    }
}

// ===== KEYBOARD SHORTCUT =====
function initQuickNavKeyboard() {
    document.addEventListener('keydown', function(event) {
        // Ctrl+K or Cmd+K
        if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
            event.preventDefault();
            openQuickNavModal();
        }
        
        // Escape to close
        if (event.key === 'Escape') {
            closeQuickNavModal();
        }
    });
}

// ===== INITIALIZATION =====
async function initQuickNav() {
    // Get user ID
    try {
        if (typeof myUserRequest === 'function') {
            myUserRequest(function(err, user) {
                if (!err && user) {
                    quickNavUserId = user.Id;
                }
            });
        }
    } catch (e) {
        console.warn('QuickNav: Could not get user ID', e);
    }
    
    // Inject navbar button
    injectQuickNavButton();
    
    // Setup keyboard shortcuts
    initQuickNavKeyboard();
    
    console.log('QuickNav: Initialized');
}

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initQuickNav);
} else {
    // DOM already loaded, wait a bit for other scripts
    setTimeout(initQuickNav, 500);
}

// Expose functions globally
window.QuickNav = {
    open: openQuickNavModal,
    close: closeQuickNavModal,
    addCurrent: addCurrentPageToQuickNav,
    load: loadQuickNavShortcuts,
    init: initQuickNav
};
