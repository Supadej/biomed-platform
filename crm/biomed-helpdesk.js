/**
 * Biomed Helpdesk - daisyUI Version
 * Kanban-style helpdesk management with modern UI components
 */

// Global Variables
let pipelineCache = [];
let ticketsCache = [];
let usersCache = [];
let contactsCache = [];
let productsCache = [];
let saleAreasCache = [];
let myuser = null;
let currentViewMode = 'card';

// Filter instances
let userFilterSelect = null;
let assignFilterSelect = null;
let contactFilterSelect = null;
let productFilterSelect = null;
let saleAreaFilterSelect = null;
let ticketAssignSelect = null;

// noUiSlider instances
let creationSlider = null;
let updateSlider = null;
let expectedSlider = null;
let prioritySlider = null;

// ============================================
// Quarter Mode: 'fiscal' (FYQ) or 'standard' (YQ)
// Shared localStorage key with CRM for consistency
// ============================================
let helpdeskQuarterMode = localStorage.getItem('crmQuarterMode') || 'fiscal';

// Build standard (calendar year) Translator for helpdesk
const HelpdeskStandardTranslator = [];
for (let year = 2023; year <= new Date().getFullYear() + 2; year++) {
    for (let q = 1; q <= 4; q++) {
        HelpdeskStandardTranslator.push(`Q${q} ${year}`);
    }
}

/**
 * Switch quarter mode between 'fiscal' (FYQ), 'standard' (YQ), or 'manual'
 */
function setHelpdeskQuarterMode(mode) {
    helpdeskQuarterMode = mode;
    localStorage.setItem('crmQuarterMode', mode);

    // Update toggle button UI
    const btnFYQ = document.getElementById('hdBtnFYQ');
    const btnYQ = document.getElementById('hdBtnYQ');
    const btnManual = document.getElementById('hdBtnManual');
    const desc = document.getElementById('hdQuarterModeDesc');
    const slidersContainer = document.getElementById('hdQuarterSlidersContainer');
    const manualContainer = document.getElementById('hdManualDateContainer');

    btnFYQ?.classList.remove('btn-active');
    btnYQ?.classList.remove('btn-active');
    btnManual?.classList.remove('btn-active');

    if (mode === 'fiscal') {
        btnFYQ?.classList.add('btn-active');
        if (desc) desc.textContent = 'Fiscal Year Quarter (Q1=May-Jul)';
        if (slidersContainer) slidersContainer.classList.remove('hidden');
        if (manualContainer) manualContainer.classList.add('hidden');
        reinitializeHelpdeskSliders();
    } else if (mode === 'standard') {
        btnYQ?.classList.add('btn-active');
        if (desc) desc.textContent = 'Year Quarter (Q1=Jan-Mar)';
        if (slidersContainer) slidersContainer.classList.remove('hidden');
        if (manualContainer) manualContainer.classList.add('hidden');
        reinitializeHelpdeskSliders();
    } else if (mode === 'manual') {
        btnManual?.classList.add('btn-active');
        if (desc) desc.textContent = 'Manual Date Range';
        if (slidersContainer) slidersContainer.classList.add('hidden');
        if (manualContainer) manualContainer.classList.remove('hidden');
        _initHelpdeskManualDateDefaults();
    }
}

/**
 * Set default values for manual date inputs (current month range)
 * Only sets values if the inputs are currently empty
 */
function _initHelpdeskManualDateDefaults() {
    const now = new Date();
    const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1);
    const endOfMonth = new Date(now.getFullYear(), now.getMonth() + 1, 0);
    
    const fmt = (d) => d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
    
    const fields = ['hdManualCreationStart', 'hdManualCreationEnd'];
    fields.forEach(id => {
        const el = document.getElementById(id);
        if (el && !el.value) {
            if (id.endsWith('Start')) el.value = fmt(startOfMonth);
            if (id.endsWith('End')) el.value = fmt(endOfMonth);
        }
    });
}

// Priority mapping
const PriorityMap = {
    0: { name: 'No Priority', emoji: '💤', class: 'priority-none', badge: 'badge-ghost' },
    1: { name: 'Low', emoji: '🧊', class: 'priority-low', badge: 'badge-info' },
    2: { name: 'Normal', emoji: '⚒️', class: 'priority-normal', badge: 'badge-success' },
    3: { name: 'High', emoji: '⚡', class: 'priority-high', badge: 'badge-warning' },
    4: { name: 'Urgent', emoji: '🔥', class: 'priority-urgent', badge: 'badge-error' },
    5: { name: 'Critical', emoji: '❤️‍🔥', class: 'priority-critical', badge: 'badge-error' }
};

// User cache for individual lookups (when not in main usersCache)
let userByIdCache = {};

/**
 * Get user by ID - check cache first, then fetch from server
 * @param {number} userId - User ID to lookup
 * @returns {object|null} - User object with Name property or null
 */
function getUserById(userId) {
    if (!userId) return null;
    
    // Check main usersCache first
    const cachedUser = usersCache.find(u => u.Id === userId);
    if (cachedUser) {
        // Ensure Name property exists
        if (!cachedUser.Name) {
            cachedUser.Name = `${cachedUser.FirstName || ''} ${cachedUser.LastName || ''}`.trim() || cachedUser.username || `User#${userId}`;
        }
        return cachedUser;
    }
    
    // Check individual user cache
    if (userByIdCache[userId]) {
        return userByIdCache[userId];
    }
    
    // Not found - fetch from server asynchronously and return placeholder
    fetchUserById(userId);
    
    return { Id: userId, Name: `Loading...`, loading: true };
}

/**
 * Fetch user by ID from server and update cache
 */
function fetchUserById(userId) {
    if (userByIdCache[userId]?.fetching) return; // Already fetching
    
    // Mark as fetching to prevent duplicate requests
    userByIdCache[userId] = { Id: userId, Name: `User#${userId}`, fetching: true };
    
    // Use GetUserById if available, otherwise try alternative
    if (typeof GetUserById === 'function') {
        GetUserById(userId, (error, user) => {
            if (!error && user) {
                user.Name = `${user.FirstName || ''} ${user.LastName || ''}`.trim() || user.username || `User#${userId}`;
                userByIdCache[userId] = user;
                // Re-render to show updated name
                if (currentViewMode === 'card') {
                    renderKanbanView();
                } else {
                    renderTableView();
                }
            } else {
                userByIdCache[userId] = { Id: userId, Name: `User#${userId}`, notFound: true };
            }
        });
    } else {
        // Fallback: search in usersCache with different matching
        const found = usersCache.find(u => u.Id == userId);
        if (found) {
            found.Name = `${found.FirstName || ''} ${found.LastName || ''}`.trim() || found.username || `User#${userId}`;
            userByIdCache[userId] = found;
        } else {
            userByIdCache[userId] = { Id: userId, Name: `User#${userId}`, notFound: true };
        }
    }
}

// Quarter Translator for slider - returns active translator based on quarter mode
let HelpdeskTranslatorFiscal = null;

function getHelpdeskTranslator() {
    if (helpdeskQuarterMode === 'standard') {
        return HelpdeskStandardTranslator;
    }
    // Fiscal mode: use global Translator if exists (from biomed-global.js)
    if (typeof Translator !== 'undefined' && Array.isArray(Translator) && Translator.length > 0) {
        return Translator;
    }
    // Otherwise generate locally
    if (!HelpdeskTranslatorFiscal) {
        HelpdeskTranslatorFiscal = [];
        for (let year = 23; year <= 28; year++) {
            for (let q = 1; q <= 4; q++) {
                HelpdeskTranslatorFiscal.push(`Q${q} Y${year}`);
            }
        }
    }
    return HelpdeskTranslatorFiscal;
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    xalert('กำลังโหลดข้อมูล...', 2, 3000);
    
    myPermission((user) => {
        myuser = user;
        console.log('User loaded:', myuser);
        
        // Load all data
        loadAllData();
    });
});

/**
 * Load all required data
 */
function loadAllData() {
    // Load pipelines
    GetHelpdeskPipeline((error, pipelines) => {
        if (error) {
            xalert('Error loading pipelines: ' + error, 1, -1);
            return;
        }
        pipelineCache = pipelines || [];
        console.log('Pipelines loaded:', pipelineCache);
        
        // Load users
        getUsers((error, users) => {
            if (error) {
                xalert('Error loading users: ' + error, 1, -1);
                return;
            }
            usersCache = (users || []).map(u => ({
                ...u,
                Name: `${u.FirstName || ''} ${u.LastName || ''}`.trim() || u.username || `User#${u.Id}`
            }));
            console.log('Users loaded:', usersCache);
            
            // Load contacts
            getContacts((error, contacts) => {
                if (error) {
                    xalert('Error loading contacts: ' + error, 1, -1);
                    return;
                }
                contactsCache = contacts || [];
                console.log('Contacts loaded:', contactsCache);
                
                // Load products
                getProducts((error, products) => {
                    if (error) {
                        xalert('Error loading products: ' + error, 1, -1);
                        return;
                    }
                    productsCache = products || [];
                    console.log('Products loaded:', productsCache);
                    
                    // Load sale areas
                    getSaleAreas((error, saleAreas) => {
                        if (error) {
                            xalert('Error loading sale areas: ' + error, 1, -1);
                            return;
                        }
                        saleAreasCache = saleAreas || [];
                        console.log('Sale Areas loaded:', saleAreasCache);
                        
                        // Initialize UI components
                        initializeFilters();
                        initializeSliders();
                        
                        // Parse URL and search
                        parseQueryURL();
                        applyFilters();
                        
                        xalert('โหลดข้อมูล Helpdesk สำเร็จ', 0, 3000);
                    }, false);
                }, false);
            }, false);
        }, false);
    });
}

/**
 * Initialize MultiSelect filters
 */
function initializeFilters() {
    // User options (creator)
    const userOptions = usersCache.map(u => ({
        value: u.Id.toString(),
        label: u.Name + (u.Position ? ` (${u.Position})` : '')
    }));
    
    // Contact options
    const contactOptions = contactsCache.map(c => ({
        value: c.Id.toString(),
        label: c.Name + (c.Company ? ` - ${c.Company}` : '')
    }));
    
    // Product options (filtered by permission)
    const hasManagePermission = myuser?.Permissions?.some(p => 
        p.Type === 'lead_manage' && (p.Value === 'Allow' || p.Value === 3)
    );
    
    console.log('Filter Debug:', {
        hasManagePermission,
        productsCacheLength: productsCache?.length,
        saleAreasCacheLength: saleAreasCache?.length,
        myuserProductUsers: myuser?.ProductUsers,
        myuserSaleAreaUsers: myuser?.SaleAreaUsers
    });
    
    // Product options - show all if no permission filter or has manage permission
    const productOptions = productsCache
        .filter(p => {
            if (hasManagePermission) return true;
            if (!myuser?.ProductUsers || myuser.ProductUsers.length === 0) return true; // No restriction
            return myuser.ProductUsers.some(pu => pu.ProductId === p.Id);
        })
        .map(p => ({
            value: p.Id.toString(),
            label: p.Name
        }));
    
    // Sale Area options - show all if no permission filter or has manage permission
    const saleAreaOptions = saleAreasCache
        .filter(sa => {
            if (hasManagePermission) return true;
            if (!myuser?.SaleAreaUsers || myuser.SaleAreaUsers.length === 0) return true; // No restriction
            return myuser.SaleAreaUsers.some(sau => sau.SaleAreaId === sa.Id);
        })
        .map(sa => ({
            value: sa.Id.toString(),
            label: sa.Name
        }));
    
    console.log('Filter Options:', {
        productOptionsLength: productOptions.length,
        saleAreaOptionsLength: saleAreaOptions.length,
        productOptions,
        saleAreaOptions
    });
    
    // Initialize MultiSelect components
    userFilterSelect = new MultiSelect('userFilter', {
        options: userOptions,
        placeholder: 'เลือกผู้สร้าง...',
        badgeClass: 'badge-primary',
        searchable: true,
        showSelectAll: true
    });
    
    assignFilterSelect = new MultiSelect('assignFilter', {
        options: userOptions,
        placeholder: 'เลือกผู้รับผิดชอบ...',
        badgeClass: 'badge-secondary',
        searchable: true,
        showSelectAll: true
    });
    
    contactFilterSelect = new MultiSelect('contactFilter', {
        options: contactOptions,
        placeholder: 'เลือก Contact...',
        badgeClass: 'badge-accent',
        searchable: true,
        showSelectAll: true
    });
    
    productFilterSelect = new MultiSelect('productFilter', {
        options: productOptions,
        placeholder: 'เลือกสินค้า...',
        badgeClass: 'badge-info',
        searchable: true,
        showSelectAll: true
    });
    
    saleAreaFilterSelect = new MultiSelect('saleAreaFilter', {
        options: saleAreaOptions,
        placeholder: 'เลือกพื้นที่ขาย...',
        badgeClass: 'badge-success',
        searchable: true,
        showSelectAll: true
    });
}

/**
 * Initialize Range Sliders
 */
function initializeSliders() {
    _createHelpdeskSliders();
    // Restore quarter mode toggle UI
    setHelpdeskQuarterMode(helpdeskQuarterMode);
}

/**
 * Reinitialize sliders when quarter mode changes
 */
function reinitializeHelpdeskSliders() {
    _createHelpdeskSliders();
}

/**
 * Internal: create/recreate all date and priority sliders
 */
function _createHelpdeskSliders() {
    const trans = getHelpdeskTranslator();

    const formatQuarter = (val) => {
        const t = getHelpdeskTranslator();
        const idx = Math.round(val);
        return t[idx] || '';
    };

    // Clear existing slider DOM content before recreating
    ['creationRangeSlider', 'updateRangeSlider', 'expectedRangeSlider'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.innerHTML = '';
    });

    // Creation date range slider
    creationSlider = new RangeSlider('creationRangeSlider', {
        min: 0,
        max: trans.length - 1,
        value: [0, trans.length - 1],
        step: 1,
        range: true,
        showLabels: true,
        colorClass: 'range-primary',
        formatValue: formatQuarter,
        text: { from: 'จาก', to: 'ถึง' }
    });

    // Update date range slider
    if (document.getElementById('updateRangeSlider')) {
        updateSlider = new RangeSlider('updateRangeSlider', {
            min: 0,
            max: trans.length - 1,
            value: [0, trans.length - 1],
            step: 1,
            range: true,
            showLabels: true,
            colorClass: 'range-secondary',
            formatValue: formatQuarter,
            text: { from: 'จาก', to: 'ถึง' }
        });
    }

    // Expected date range slider
    if (document.getElementById('expectedRangeSlider')) {
        expectedSlider = new RangeSlider('expectedRangeSlider', {
            min: 0,
            max: trans.length - 1,
            value: [0, trans.length - 1],
            step: 1,
            range: true,
            showLabels: true,
            colorClass: 'range-accent',
            formatValue: formatQuarter,
            text: { from: 'จาก', to: 'ถึง' }
        });
    }

    // Priority slider (only create, don't recreate on quarter mode change)
    const priorityEl = document.getElementById('prioritySlider');
    if (priorityEl && !prioritySlider) {
        prioritySlider = new RangeSlider('prioritySlider', {
            min: -1,
            max: 5,
            value: -1,
            step: 1,
            range: false,
            showLabels: true,
            colorClass: 'range-warning',
            formatValue: (val) => {
                val = Math.round(val);
                if (val === -1) return 'ทั้งหมด';
                return PriorityMap[val]?.emoji + ' ' + PriorityMap[val]?.name || val;
            },
            text: { min: 'Priority' }
        });
    }
}

/**
 * Get quarter date range from quarter number and year
 * Dispatches to fiscal or standard based on helpdeskQuarterMode
 */
function getQuarterDateRange(quarter, year) {
    const fullYear = 2000 + year;

    if (helpdeskQuarterMode === 'fiscal') {
        // Fiscal: Q1=May-Jul, Q2=Aug-Oct, Q3=Nov-Jan, Q4=Feb-Apr
        // Use global getQuarterDateRange from biomed-global.js if available
        if (typeof window._globalGetQuarterDateRange === 'function') {
            return window._globalGetQuarterDateRange(quarter, year);
        }
        // Inline fiscal quarter calculation
        const quarterStartMonths = [4, 7, 10, 1]; // May, Aug, Nov, Feb (0-indexed)
        const quarterEndMonths = [6, 9, 0, 3];     // Jul, Oct, Jan, Apr (0-indexed)
        let startYear = fullYear;
        let endYear = fullYear;
        if (quarter === 3) { endYear = fullYear + 1; } // Nov-Jan crosses year
        if (quarter === 4) { startYear = fullYear + 1; endYear = fullYear + 1; } // Feb-Apr is next calendar year
        const startDate = new Date(startYear, quarterStartMonths[quarter - 1], 1);
        const endDate = new Date(endYear, quarterEndMonths[quarter - 1] + 1, 0);
        endDate.setHours(23, 59, 59);
        return { startDate, endDate };
    }

    // Standard: Q1=Jan-Mar, Q2=Apr-Jun, Q3=Jul-Sep, Q4=Oct-Dec
    const startMonth = (quarter - 1) * 3;
    const endMonth = startMonth + 2;
    return {
        startDate: new Date(fullYear, startMonth, 1),
        endDate: new Date(fullYear, endMonth + 1, 0)
    };
}

/**
 * Format quarter from slider value
 */
function QFormater(value) {
    const trans = getHelpdeskTranslator();
    return trans[value] || '';
}

/**
 * Format date for API (local timezone safe)
 */
function timeFormater(date) {
    if (!date) return null;
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, '0');
    const d = String(date.getDate()).padStart(2, '0');
    return `${y}-${m}-${d}`;
}

/**
 * Apply filters and search
 */
function applyFilters() {
    const queryText = document.getElementById('ticketQuery')?.value || null;
    const trans = getHelpdeskTranslator();
    
    // Get priority value
    const priorityValue = Math.round(prioritySlider?.getValues() || -1);
    
    // Get multiselect values
    const userIds = userFilterSelect?.getValues() || [];
    const assignIds = assignFilterSelect?.getValues() || [];
    const contactIds = contactFilterSelect?.getValues() || [];
    const productIds = productFilterSelect?.getValues() || [];
    const saleAreaIds = saleAreaFilterSelect?.getValues() || [];
    
    // Build query
    const query = {
        AnyInt: priorityValue === -1 ? null : priorityValue,
        SaleAreaIDs: saleAreaIds.length > 0 ? saleAreaIds.map(Number) : null,
        ProductIDs: productIds.length > 0 ? productIds.map(Number) : null,
        ContactIDs: contactIds.length > 0 ? contactIds.map(Number) : null,
        ExtendedIDs: assignIds.length > 0 ? assignIds.map(Number) : null,
        UserIDs: userIds.length > 0 ? userIds.map(Number) : null,
        Title: queryText,
        DeepSearch: true
    };
    
    // Get date range based on mode
    let creationValues = [0, trans.length - 1]; // default for URL
    if (helpdeskQuarterMode === 'manual') {
        // Manual mode: read date inputs directly
        const creationStart = document.getElementById('hdManualCreationStart')?.value;
        const creationEnd = document.getElementById('hdManualCreationEnd')?.value;
        
        if (creationStart) {
            const sd = new Date(creationStart + 'T00:00:00');
            query.StartDate = timeFormater(sd);
        }
        if (creationEnd) {
            const ed = new Date(creationEnd + 'T23:59:59');
            query.EndDate = timeFormater(ed);
        }
    } else {
        // Quarter slider mode
        creationValues = creationSlider?.getValues() || [0, trans.length - 1];
        
        const creationStartQ = QFormater(creationValues[0]);
        const creationEndQ = QFormater(creationValues[1]);
        const creationStartRange = getQuarterDateRange(
            parseInt(creationStartQ.split(' ')[0].slice(-1)),
            parseInt(creationStartQ.split(' ')[1].slice(-2))
        );
        const creationEndRange = getQuarterDateRange(
            parseInt(creationEndQ.split(' ')[0].slice(-1)),
            parseInt(creationEndQ.split(' ')[1].slice(-2))
        );
        
        query.StartDate = timeFormater(creationStartRange.startDate);
        query.EndDate = timeFormater(creationEndRange.endDate);
    }
    
    console.log('Query:', query);
    
    // Update URL
    updateQueryURL(query, creationValues, priorityValue);
    
    // Display tickets
    displayTickets(query);
}

/**
 * Clear all filters
 */
function clearFilters() {
    document.getElementById('ticketQuery').value = '';
    
    const trans = getHelpdeskTranslator();
    creationSlider?.setValues([0, trans.length - 1]);
    updateSlider?.setValues([0, trans.length - 1]);
    expectedSlider?.setValues([0, trans.length - 1]);
    prioritySlider?.setValues(-1);
    
    // Clear manual date inputs
    ['hdManualCreationStart', 'hdManualCreationEnd'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.value = '';
    });
    
    userFilterSelect?.clearSelection();
    assignFilterSelect?.clearSelection();
    contactFilterSelect?.clearSelection();
    productFilterSelect?.clearSelection();
    saleAreaFilterSelect?.clearSelection();
    
    applyFilters();
}

/**
 * Update URL with query parameters
 */
function updateQueryURL(query, creationValues, priorityValue) {
    const urlParams = new URLSearchParams();
    
    urlParams.set('QuarterMode', helpdeskQuarterMode);
    
    if (helpdeskQuarterMode === 'manual') {
        const manualCreationStart = document.getElementById('hdManualCreationStart')?.value;
        const manualCreationEnd = document.getElementById('hdManualCreationEnd')?.value;
        if (manualCreationStart) urlParams.set('ManualCreationStart', manualCreationStart);
        if (manualCreationEnd) urlParams.set('ManualCreationEnd', manualCreationEnd);
    } else {
        urlParams.set('CreationQuarter', creationValues.join(','));
    }
    
    if (query.UserIDs) urlParams.set('UserIDs', query.UserIDs.join(','));
    if (query.ExtendedIDs) urlParams.set('AssignedIDs', query.ExtendedIDs.join(','));
    if (query.ContactIDs) urlParams.set('ContactIDs', query.ContactIDs.join(','));
    if (query.ProductIDs) urlParams.set('ProductIDs', query.ProductIDs.join(','));
    if (query.SaleAreaIDs) urlParams.set('SaleAreaIDs', query.SaleAreaIDs.join(','));
    if (priorityValue !== -1) urlParams.set('Priority', priorityValue);
    if (query.Title) urlParams.set('QueryText', query.Title);
    
    const newUrl = `${window.location.pathname}?${urlParams.toString()}`;
    window.history.replaceState(null, '', newUrl);
}

/**
 * Parse URL query parameters
 */
function parseQueryURL() {
    const urlParams = new URLSearchParams(window.location.search);
    
    // Restore quarter mode from URL (overrides localStorage)
    const qMode = urlParams.get('QuarterMode');
    if (qMode === 'fiscal' || qMode === 'standard' || qMode === 'manual') {
        helpdeskQuarterMode = qMode;
        localStorage.setItem('crmQuarterMode', qMode);
        setHelpdeskQuarterMode(qMode);
    }
    
    if (qMode === 'manual') {
        const manualStart = urlParams.get('ManualCreationStart');
        const manualEnd = urlParams.get('ManualCreationEnd');
        if (manualStart) {
            const el = document.getElementById('hdManualCreationStart');
            if (el) el.value = manualStart;
        }
        if (manualEnd) {
            const el = document.getElementById('hdManualCreationEnd');
            if (el) el.value = manualEnd;
        }
    } else {
        const creationQuarter = urlParams.get('CreationQuarter')?.split(',').map(Number);
        if (creationQuarter) {
            creationSlider?.setValue(creationQuarter);
        }
    }
    
    const priority = urlParams.get('Priority');
    if (priority) {
        prioritySlider?.setValues(parseInt(priority));
    }
    
    const queryText = urlParams.get('QueryText');
    if (queryText) {
        document.getElementById('ticketQuery').value = queryText;
    }
    
    // Set multiselect values
    const userIds = urlParams.get('UserIDs')?.split(',').filter(Boolean);
    const assignIds = urlParams.get('AssignedIDs')?.split(',').filter(Boolean);
    const contactIds = urlParams.get('ContactIDs')?.split(',').filter(Boolean);
    const productIds = urlParams.get('ProductIDs')?.split(',').filter(Boolean);
    const saleAreaIds = urlParams.get('SaleAreaIDs')?.split(',').filter(Boolean);
    
    if (userIds) userFilterSelect?.setValues(userIds);
    if (assignIds) assignFilterSelect?.setValues(assignIds);
    if (contactIds) contactFilterSelect?.setValues(contactIds);
    if (productIds) productFilterSelect?.setValues(productIds);
    if (saleAreaIds) saleAreaFilterSelect?.setValues(saleAreaIds);
}

/**
 * Display tickets in Kanban or Table view
 */
function displayTickets(query) {
    const container = document.getElementById('pipelineContainer');
    container.innerHTML = `
        <div class="flex items-center justify-center py-16 text-base-content/50 w-full">
            <span class="loading loading-spinner loading-lg mr-3"></span>
            กำลังโหลด Tickets...
        </div>
    `;
    
    // Fetch tickets from API
    getTickets(query, (error, tickets) => {
        if (error) {
            xalert('Error loading tickets: ' + error, 1, -1);
            container.innerHTML = `
                <div class="flex items-center justify-center py-16 text-error w-full">
                    <i class="fa-solid fa-triangle-exclamation mr-2"></i>
                    ไม่สามารถโหลดข้อมูลได้
                </div>
            `;
            return;
        }
        
        ticketsCache = tickets || [];
        console.log('Tickets loaded:', ticketsCache);
        
        // Render based on view mode
        if (currentViewMode === 'card') {
            renderKanbanView();
        } else if (currentViewMode === 'table') {
            renderTableView();
        } else if (currentViewMode === 'viz') {
            renderVisualization();
        }
    });
}

/**
 * Render Kanban View
 */
function renderKanbanView() {
    const container = document.getElementById('pipelineContainer');
    
    // Sort pipelines by order
    const sortedPipelines = [...pipelineCache].sort((a, b) => (a.Order || 0) - (b.Order || 0));
    
    // Group tickets by pipeline
    const ticketsByPipeline = {};
    sortedPipelines.forEach(p => {
        ticketsByPipeline[p.Id] = [];
    });
    
    ticketsCache.forEach(ticket => {
        const pipelineId = ticket.PipelineId || ticket.Pipeline?.Id;
        if (ticketsByPipeline[pipelineId]) {
            ticketsByPipeline[pipelineId].push(ticket);
        }
    });
    
    // Build kanban HTML
    let html = '';
    
    sortedPipelines.forEach(pipeline => {
        const tickets = ticketsByPipeline[pipeline.Id] || [];
        const color = pipeline.Color || '#6366f1';
        
        html += `
            <div class="kanban-column">
                <div class="bg-base-200 rounded-lg overflow-hidden h-full flex flex-col">
                    <!-- Column Header -->
                    <div class="p-3 flex items-center justify-between" style="border-top: 3px solid ${color};">
                        <div class="flex items-center gap-2">
                            <h3 class="font-bold text-sm">${pipeline.Name || 'Unnamed'}</h3>
                            <span class="badge badge-sm">${tickets.length}</span>
                        </div>
                        <div class="dropdown dropdown-end">
                            <button tabindex="0" class="btn btn-ghost btn-xs btn-circle">
                                <i class="fa-solid fa-ellipsis-v"></i>
                            </button>
                            <ul tabindex="0" class="dropdown-content menu bg-base-100 rounded-box z-50 w-40 p-2 shadow-lg">
                                <li><a onclick="editPipeline(${pipeline.Id})"><i class="fa-solid fa-edit w-4"></i> แก้ไข</a></li>
                                <li><a onclick="deletePipeline(${pipeline.Id})" class="text-error"><i class="fa-solid fa-trash w-4"></i> ลบ</a></li>
                            </ul>
                        </div>
                    </div>
                    
                    <!-- Tickets List -->
                    <div class="tickets-list p-2 flex-1 space-y-2 min-h-0">
                        ${tickets.map(ticket => renderTicketCard(ticket, color)).join('')}
                        
                        ${tickets.length === 0 ? `
                            <div class="text-center py-8 text-base-content/40 text-sm">
                                <i class="fa-solid fa-inbox text-2xl mb-2"></i>
                                <p>ไม่มี Ticket</p>
                            </div>
                        ` : ''}
                    </div>
                    
                    <!-- Add Ticket Button -->
                    <div class="p-2 border-t border-base-300">
                        <button class="btn btn-ghost btn-sm w-full gap-2" onclick="createTicketPopup(${pipeline.Id})">
                            <i class="fa-solid fa-plus"></i> เพิ่ม Ticket
                        </button>
                    </div>
                </div>
            </div>
        `;
    });
    
    // Add "Add Pipeline" column
    html += `
        <div class="kanban-column">
            <div class="bg-base-200/50 border-2 border-dashed border-base-300 rounded-lg h-full flex items-center justify-center min-h-[200px]">
                <button class="btn btn-ghost gap-2" onclick="createModalPopup()">
                    <i class="fa-solid fa-plus"></i> เพิ่ม Pipeline
                </button>
            </div>
        </div>
    `;
    
    container.innerHTML = html;
}

/**
 * Render single ticket card
 */
function renderTicketCard(ticket, pipelineColor) {
    const priority = PriorityMap[ticket.Priority || 0];
    const now = new Date();
    const lastUpdated = new Date(ticket.LastUpdate || ticket.CreatedDate);
    const daysDiff = Math.floor((now - lastUpdated) / (1000 * 60 * 60 * 24));
    
    // Determine status
    let statusClass = 'status-active';
    let statusText = 'Active';
    if (daysDiff > 90) {
        statusClass = 'status-dropped';
        statusText = 'Dropped';
    } else if (daysDiff > 30) {
        statusClass = 'status-inactive';
        statusText = 'Inactive';
    }
    
    // Find related data
    const contact = contactsCache.find(c => c.Id === ticket.ContactId);
    const product = productsCache.find(p => p.Id === ticket.ProductId);
    const saleArea = saleAreasCache.find(sa => sa.Id === ticket.SaleAreaId);
    
    // Get users using getUserById (handles cache miss and server fetch)
    const creator = getUserById(ticket.CreatedByUserId);
    const assignee = getUserById(ticket.AssignedToUserId);
    
    // Format dates
    const createdDate = ticket.CreatedDate ? new Date(ticket.CreatedDate).toLocaleDateString('th-TH', {
        day: 'numeric',
        month: 'short',
        year: '2-digit'
    }) : '';
    
    const lastUpdateDate = ticket.LastUpdate ? new Date(ticket.LastUpdate).toLocaleDateString('th-TH', {
        day: 'numeric',
        month: 'short',
        year: '2-digit'
    }) : '';
    
    // Job Type badge color
    const jobTypeBadge = {
        'Sale_Support': 'badge-info',
        'Service_Contract': 'badge-success',
        'Warranty': 'badge-warning',
        'Out_of_Warranty': 'badge-error',
        'Demo': 'badge-secondary'
    };
    
    const jobTypeClass = jobTypeBadge[ticket.JobType] || 'badge-ghost';
    const jobTypeText = ticket.JobType?.replace(/_/g, ' ') || '';
    
    // ResponseOnTime badge - null/undefined = true (On Time)
    const isOnTime = ticket.ResponseOnTime !== false;
    const responseOnTimeBadge = isOnTime 
        ? '<span class="badge badge-success badge-xs"><i class="fa-solid fa-check mr-1"></i>On Time</span>'
        : '<span class="badge badge-error badge-xs"><i class="fa-solid fa-x mr-1"></i>Late</span>';
    
    return `
        <div class="ticket-card card bg-base-100 shadow-sm cursor-pointer ${priority.class}" 
             onclick="openTicketDetail(${ticket.Id})"
             style="border-left-color: ${pipelineColor}">
            <div class="card-body p-3">
                <!-- Title & Priority -->
                <div class="flex items-start justify-between gap-2">
                    <h4 class="font-medium text-sm line-clamp-2">${ticket.Title || 'Untitled'}</h4>
                    <span class="badge ${priority.badge} badge-sm flex-shrink-0" title="${priority.name}">
                        ${priority.emoji} ${priority.name}
                    </span>
                </div>
                
                <!-- Instrument Info -->
                ${ticket.Instumental || ticket.Model ? `
                    <div class="bg-base-200/50 rounded-lg p-2 mt-2 text-xs">
                        ${ticket.Instumental ? `
                            <div class="flex items-center gap-1 font-medium text-primary">
                                <i class="fa-solid fa-microscope"></i>
                                <span>${ticket.Instumental}</span>
                            </div>
                        ` : ''}
                        ${ticket.Model ? `
                            <div class="flex items-center gap-1 text-base-content/70 mt-1">
                                <i class="fa-solid fa-cube"></i>
                                <span>${ticket.Model}</span>
                            </div>
                        ` : ''}
                        ${ticket.SerialNumber ? `
                            <div class="flex items-center gap-1 text-base-content/50 mt-1">
                                <i class="fa-solid fa-barcode"></i>
                                <span class="font-mono text-[10px]">${ticket.SerialNumber}</span>
                            </div>
                        ` : ''}
                    </div>
                ` : ''}
                
                <!-- Job Type & Status Tags -->
                <div class="flex flex-wrap gap-1 mt-2">
                    ${jobTypeText ? `<span class="badge ${jobTypeClass} badge-xs">${jobTypeText}</span>` : ''}
                    ${ticket.InstumentalStatus ? `<span class="badge badge-outline badge-xs">${ticket.InstumentalStatus.replace(/_/g, ' ')}</span>` : ''}
                    ${responseOnTimeBadge}
                </div>
                
                <!-- Product & SaleArea Tags -->
                <div class="flex flex-wrap gap-1 mt-1">
                    ${product ? `<span class="badge badge-ghost badge-xs"><i class="fa-solid fa-box mr-1"></i>${product.Name}</span>` : ''}
                    ${saleArea ? `<span class="badge badge-ghost badge-xs"><i class="fa-solid fa-map-marker-alt mr-1"></i>${saleArea.Name}</span>` : ''}
                </div>
                
                <!-- Contact -->
                ${contact ? `
                    <div class="flex items-center gap-1 mt-2 text-xs text-base-content/60">
                        <i class="fa-solid fa-building"></i>
                        <span class="truncate">${contact.Name}</span>
                    </div>
                ` : ''}
                
                <!-- Users: Created By & Assignee -->
                <div class="flex flex-wrap gap-1 mt-2">
                    ${creator ? `<span class="badge badge-neutral badge-xs"><i class="fa-solid fa-user-pen mr-1"></i>${creator.Name}</span>` : ''}
                    ${assignee ? `<span class="badge badge-primary badge-xs"><i class="fa-solid fa-user-check mr-1"></i>${assignee.Name}</span>` : ''}
                </div>
                
                <!-- Footer -->
                <div class="flex items-center justify-between mt-3 pt-2 border-t border-base-200">
                    <div class="flex flex-col gap-0.5 text-xs text-base-content/50">
                        <div class="flex items-center gap-1">
                            <i class="fa-regular fa-calendar-plus"></i>
                            <span>${createdDate}</span>
                        </div>
                        ${lastUpdateDate ? `
                            <div class="flex items-center gap-1">
                                <i class="fa-regular fa-calendar-check"></i>
                                <span>${lastUpdateDate}</span>
                            </div>
                        ` : ''}
                    </div>
                    
                    <span class="badge badge-xs ${statusClass}">${statusText}</span>
                </div>
            </div>
        </div>
    `;
}

/**
 * Render Table View
 */
function renderTableView() {
    const tableContainer = document.getElementById('tableContainer');
    const tableElement = document.getElementById('ticketTable');
    
    let html = `
        <thead>
            <tr>
                <th>ID</th>
                <th>Title</th>
                <th>Instrument</th>
                <th>Model</th>
                <th>S/N</th>
                <th>Pipeline</th>
                <th>Priority</th>
                <th>JobType</th>
                <th>ResponseOnTime</th>
                <th>Contact</th>
                <th>Product</th>
                <th>SaleArea</th>
                <th>Created By</th>
                <th>Assigned To</th>
                <th>Status</th>
                <th>Created</th>
                <th>LastUpdate</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
    `;
    
    ticketsCache.forEach(ticket => {
        const priority = PriorityMap[ticket.Priority || 0];
        const pipeline = pipelineCache.find(p => p.Id === (ticket.PipelineId || ticket.Pipeline?.Id));
        const contact = contactsCache.find(c => c.Id === ticket.ContactId);
        const product = productsCache.find(p => p.Id === ticket.ProductId);
        const saleArea = saleAreasCache.find(sa => sa.Id === ticket.SaleAreaId);
        const creator = getUserById(ticket.CreatedByUserId);
        const assignee = getUserById(ticket.AssignedToUserId);
        
        const now = new Date();
        const lastUpdated = new Date(ticket.LastUpdate || ticket.CreatedDate);
        const daysDiff = Math.floor((now - lastUpdated) / (1000 * 60 * 60 * 24));
        
        let statusClass = 'badge-success';
        let statusText = 'Active';
        if (daysDiff > 90) {
            statusClass = 'badge-error';
            statusText = 'Dropped';
        } else if (daysDiff > 30) {
            statusClass = 'badge-warning';
            statusText = 'Inactive';
        }
        
        const createdDate = ticket.CreatedDate ? new Date(ticket.CreatedDate).toLocaleDateString('th-TH') : '';
        const lastUpdateDate = ticket.LastUpdate ? new Date(ticket.LastUpdate).toLocaleDateString('th-TH') : '';
        
        // Job Type badge color
        const jobTypeBadge = {
            'Sale_Support': 'badge-info',
            'Service_Contract': 'badge-success',
            'Warranty': 'badge-warning',
            'Out_of_Warranty': 'badge-error',
            'Demo': 'badge-secondary'
        };
        const jobTypeClass = jobTypeBadge[ticket.JobType] || 'badge-ghost';
        const jobTypeText = ticket.JobType?.replace(/_/g, ' ') || '-';
        
        // ResponseOnTime badge
        const responseOnTimeBadge = ticket.ResponseOnTime === true 
            ? '<span class="badge badge-success badge-sm"><i class="fa-solid fa-check mr-1"></i>On Time</span>'
            : ticket.ResponseOnTime === false 
                ? '<span class="badge badge-error badge-sm"><i class="fa-solid fa-x mr-1"></i>Late</span>'
                : '-';
        
        html += `
            <tr class="hover cursor-pointer" onclick="openTicketDetail(${ticket.Id})">
                <td class="font-mono text-xs whitespace-nowrap">#${ticket.Id}</td>
                <td class="font-medium max-w-[200px] truncate">${ticket.Title || 'Untitled'}</td>
                <td class="text-xs whitespace-nowrap">${ticket.Instumental || '-'}</td>
                <td class="text-xs whitespace-nowrap">${ticket.Model || '-'}</td>
                <td class="font-mono text-xs whitespace-nowrap">${ticket.SerialNumber || '-'}</td>
                <td class="whitespace-nowrap"><span class="badge badge-ghost badge-sm">${pipeline?.Name || '-'}</span></td>
                <td class="whitespace-nowrap"><span class="badge ${priority.badge} badge-sm">${priority.emoji} ${priority.name}</span></td>
                <td class="whitespace-nowrap"><span class="badge ${jobTypeClass} badge-sm">${jobTypeText}</span></td>
                <td class="whitespace-nowrap">${responseOnTimeBadge}</td>
                <td class="whitespace-nowrap">${contact?.Name || '-'}</td>
                <td class="whitespace-nowrap">${product?.Name || '-'}</td>
                <td class="whitespace-nowrap">${saleArea?.Name || '-'}</td>
                <td class="whitespace-nowrap">${creator ? `<span class="badge badge-neutral badge-sm">${creator.Name}</span>` : '-'}</td>
                <td class="whitespace-nowrap">${assignee ? `<span class="badge badge-primary badge-sm">${assignee.Name}</span>` : '-'}</td>
                <td class="whitespace-nowrap"><span class="badge ${statusClass} badge-sm">${statusText}</span></td>
                <td class="text-xs whitespace-nowrap">${createdDate}</td>
                <td class="text-xs whitespace-nowrap">${lastUpdateDate}</td>
                <td class="whitespace-nowrap">
                    <div class="flex gap-1">
                        <button class="btn btn-ghost btn-xs" onclick="event.stopPropagation(); editTicket(${ticket.Id})">
                            <i class="fa-solid fa-edit"></i>
                        </button>
                        <button class="btn btn-ghost btn-xs text-error" onclick="event.stopPropagation(); deleteTicket(${ticket.Id})">
                            <i class="fa-solid fa-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    });
    
    html += '</tbody>';
    tableElement.innerHTML = html;
}

/**
 * Toggle view mode
 */
function toggleViewMode(mode) {
    currentViewMode = mode;
    
    const cardBtn = document.getElementById('cardViewBtn');
    const tableBtn = document.getElementById('tableViewBtn');
    const vizBtn = document.getElementById('vizViewBtn');
    const cardContainer = document.getElementById('cardViewContainer');
    const tableContainer = document.getElementById('tableContainer');
    const vizContainer = document.getElementById('vizContainer');
    
    // Reset all buttons
    cardBtn.classList.remove('btn-active');
    tableBtn.classList.remove('btn-active');
    vizBtn.classList.remove('btn-active');
    
    // Hide all containers
    cardContainer.classList.add('hidden');
    tableContainer.classList.add('hidden');
    vizContainer.classList.add('hidden');
    
    if (mode === 'card') {
        cardBtn.classList.add('btn-active');
        cardContainer.classList.remove('hidden');
        renderKanbanView();
    } else if (mode === 'table') {
        tableBtn.classList.add('btn-active');
        tableContainer.classList.remove('hidden');
        renderTableView();
    } else if (mode === 'viz') {
        vizBtn.classList.add('btn-active');
        vizContainer.classList.remove('hidden');
        renderVisualization();
    }
}

// ============================================
// Visualization Functions
// ============================================

// Chart instances storage
let chartInstances = {};

/**
 * Render all visualization charts
 */
function renderVisualization() {
    if (!ticketsCache || ticketsCache.length === 0) {
        console.log('No tickets data for visualization');
        return;
    }
    
    const now = new Date();
    
    // Calculate stats
    let activeCount = 0, inactiveCount = 0, droppedCount = 0, onTimeCount = 0;
    let totalResponseDays = 0, responseCount = 0;
    
    ticketsCache.forEach(ticket => {
        const lastUpdated = new Date(ticket.LastUpdate || ticket.CreatedDate);
        const daysDiff = Math.floor((now - lastUpdated) / (1000 * 60 * 60 * 24));
        
        if (daysDiff > 90) droppedCount++;
        else if (daysDiff > 30) inactiveCount++;
        else activeCount++;
        
        // ResponseOnTime - null/undefined = true
        if (ticket.ResponseOnTime !== false) onTimeCount++;
        
        // Calculate response days (from created to last update)
        if (ticket.CreatedDate && ticket.LastUpdate) {
            const created = new Date(ticket.CreatedDate);
            const updated = new Date(ticket.LastUpdate);
            const respDays = Math.floor((updated - created) / (1000 * 60 * 60 * 24));
            if (respDays >= 0) {
                totalResponseDays += respDays;
                responseCount++;
            }
        }
    });
    
    // Update summary stats
    document.getElementById('vizTotalTickets').textContent = ticketsCache.length;
    document.getElementById('vizActiveTickets').textContent = activeCount;
    document.getElementById('vizInactiveTickets').textContent = inactiveCount;
    document.getElementById('vizDroppedTickets').textContent = droppedCount;
    document.getElementById('vizOnTimeRate').textContent = ticketsCache.length > 0 
        ? Math.round((onTimeCount / ticketsCache.length) * 100) + '%' 
        : '0%';
    document.getElementById('vizAvgResponse').textContent = responseCount > 0 
        ? Math.round(totalResponseDays / responseCount) 
        : '0';
    
    // Render all charts
    renderPipelineChart();
    renderPriorityChart();
    renderJobTypeChart();
    renderInstrumentChart();
    renderTimelineChart();
    renderAssigneeChart();
    renderProductChart();
    renderSaleAreaChart();
    renderOnTimeChart();
    renderStatusChart();
    renderTimeByPipelineChart();
}

/**
 * Helper: Destroy existing chart and create new one
 */
function createChart(canvasId, config) {
    // Destroy existing chart if exists
    if (chartInstances[canvasId]) {
        chartInstances[canvasId].destroy();
    }
    
    const container = document.getElementById(canvasId);
    container.innerHTML = '<canvas></canvas>';
    const ctx = container.querySelector('canvas').getContext('2d');
    
    chartInstances[canvasId] = new Chart(ctx, config);
    return chartInstances[canvasId];
}

/**
 * Chart: Tickets by Pipeline
 */
function renderPipelineChart() {
    const data = {};
    pipelineCache.forEach(p => { data[p.Name] = 0; });
    
    ticketsCache.forEach(ticket => {
        const pipeline = pipelineCache.find(p => p.Id === ticket.PipelineId);
        if (pipeline) data[pipeline.Name]++;
    });
    
    const colors = pipelineCache.map(p => p.Color || '#6366f1');
    
    createChart('chartPipeline', {
        type: 'doughnut',
        data: {
            labels: Object.keys(data),
            datasets: [{
                data: Object.values(data),
                backgroundColor: colors,
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'right' }
            }
        }
    });
}

/**
 * Chart: Tickets by Priority
 */
function renderPriorityChart() {
    const data = { 'No Priority': 0, 'Low': 0, 'Normal': 0, 'High': 0, 'Urgent': 0, 'Critical': 0 };
    const priorityNames = ['No Priority', 'Low', 'Normal', 'High', 'Urgent', 'Critical'];
    const colors = ['#9ca3af', '#38bdf8', '#22c55e', '#f59e0b', '#ef4444', '#dc2626'];
    
    ticketsCache.forEach(ticket => {
        const name = priorityNames[ticket.Priority || 0] || 'No Priority';
        data[name]++;
    });
    
    createChart('chartPriority', {
        type: 'bar',
        data: {
            labels: Object.keys(data),
            datasets: [{
                label: 'Tickets',
                data: Object.values(data),
                backgroundColor: colors
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true } }
        }
    });
}

/**
 * Chart: Tickets by Job Type
 */
function renderJobTypeChart() {
    const data = {};
    
    ticketsCache.forEach(ticket => {
        const jobType = ticket.JobType?.replace(/_/g, ' ') || 'Unknown';
        data[jobType] = (data[jobType] || 0) + 1;
    });
    
    const colors = ['#6366f1', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'];
    
    createChart('chartJobType', {
        type: 'pie',
        data: {
            labels: Object.keys(data),
            datasets: [{
                data: Object.values(data),
                backgroundColor: colors.slice(0, Object.keys(data).length)
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { position: 'right' } }
        }
    });
}

/**
 * Chart: Tickets by Instrument
 */
function renderInstrumentChart() {
    const data = {};
    
    ticketsCache.forEach(ticket => {
        const instrument = ticket.Instumental || 'Unknown';
        data[instrument] = (data[instrument] || 0) + 1;
    });
    
    // Sort by count and take top 10
    const sorted = Object.entries(data).sort((a, b) => b[1] - a[1]).slice(0, 10);
    
    createChart('chartInstrument', {
        type: 'bar',
        data: {
            labels: sorted.map(s => s[0]),
            datasets: [{
                label: 'Tickets',
                data: sorted.map(s => s[1]),
                backgroundColor: '#8b5cf6'
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: { x: { beginAtZero: true } }
        }
    });
}

/**
 * Chart: Tickets Timeline (Monthly)
 */
function renderTimelineChart() {
    const data = {};
    
    ticketsCache.forEach(ticket => {
        if (ticket.CreatedDate) {
            const date = new Date(ticket.CreatedDate);
            const key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
            data[key] = (data[key] || 0) + 1;
        }
    });
    
    // Sort by date
    const sorted = Object.entries(data).sort((a, b) => a[0].localeCompare(b[0]));
    
    createChart('chartTimeline', {
        type: 'line',
        data: {
            labels: sorted.map(s => s[0]),
            datasets: [{
                label: 'Tickets Created',
                data: sorted.map(s => s[1]),
                borderColor: '#22c55e',
                backgroundColor: 'rgba(34, 197, 94, 0.1)',
                fill: true,
                tension: 0.3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true } }
        }
    });
}

/**
 * Chart: Tickets by Assignee
 */
function renderAssigneeChart() {
    const data = {};
    
    ticketsCache.forEach(ticket => {
        const assignee = getUserById(ticket.AssignedToUserId);
        const name = assignee?.Name || 'Unassigned';
        data[name] = (data[name] || 0) + 1;
    });
    
    // Sort by count and take top 10
    const sorted = Object.entries(data).sort((a, b) => b[1] - a[1]).slice(0, 10);
    
    createChart('chartAssignee', {
        type: 'bar',
        data: {
            labels: sorted.map(s => s[0]),
            datasets: [{
                label: 'Tickets',
                data: sorted.map(s => s[1]),
                backgroundColor: '#6366f1'
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: { x: { beginAtZero: true } }
        }
    });
}

/**
 * Chart: Tickets by Product
 */
function renderProductChart() {
    const data = {};
    
    ticketsCache.forEach(ticket => {
        const product = productsCache.find(p => p.Id === ticket.ProductId);
        const name = product?.Name || 'Unknown';
        data[name] = (data[name] || 0) + 1;
    });
    
    const sorted = Object.entries(data).sort((a, b) => b[1] - a[1]).slice(0, 10);
    const colors = ['#f472b6', '#fb923c', '#a3e635', '#22d3ee', '#818cf8', '#e879f9', '#fbbf24', '#34d399', '#60a5fa', '#f87171'];
    
    createChart('chartProduct', {
        type: 'doughnut',
        data: {
            labels: sorted.map(s => s[0]),
            datasets: [{
                data: sorted.map(s => s[1]),
                backgroundColor: colors.slice(0, sorted.length)
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { position: 'right' } }
        }
    });
}

/**
 * Chart: Tickets by Sale Area
 */
function renderSaleAreaChart() {
    const data = {};
    
    ticketsCache.forEach(ticket => {
        const saleArea = saleAreasCache.find(sa => sa.Id === ticket.SaleAreaId);
        const name = saleArea?.Name || 'Unknown';
        data[name] = (data[name] || 0) + 1;
    });
    
    const sorted = Object.entries(data).sort((a, b) => b[1] - a[1]);
    
    createChart('chartSaleArea', {
        type: 'bar',
        data: {
            labels: sorted.map(s => s[0]),
            datasets: [{
                label: 'Tickets',
                data: sorted.map(s => s[1]),
                backgroundColor: '#ef4444'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true } }
        }
    });
}

/**
 * Chart: Response On Time Analysis
 */
function renderOnTimeChart() {
    let onTime = 0, late = 0;
    
    ticketsCache.forEach(ticket => {
        if (ticket.ResponseOnTime === false) late++;
        else onTime++;
    });
    
    createChart('chartOnTime', {
        type: 'doughnut',
        data: {
            labels: ['On Time', 'Late'],
            datasets: [{
                data: [onTime, late],
                backgroundColor: ['#22c55e', '#ef4444'],
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { 
                legend: { position: 'bottom' },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const value = context.raw;
                            const percentage = Math.round((value / total) * 100);
                            return `${context.label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

/**
 * Chart: Ticket Status Distribution
 */
function renderStatusChart() {
    const now = new Date();
    let active = 0, inactive = 0, dropped = 0;
    
    ticketsCache.forEach(ticket => {
        const lastUpdated = new Date(ticket.LastUpdate || ticket.CreatedDate);
        const daysDiff = Math.floor((now - lastUpdated) / (1000 * 60 * 60 * 24));
        
        if (daysDiff > 90) dropped++;
        else if (daysDiff > 30) inactive++;
        else active++;
    });
    
    createChart('chartStatus', {
        type: 'pie',
        data: {
            labels: ['Active', 'Inactive (>30d)', 'Dropped (>90d)'],
            datasets: [{
                data: [active, inactive, dropped],
                backgroundColor: ['#22c55e', '#f59e0b', '#ef4444']
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { position: 'bottom' } }
        }
    });
}

/**
 * Chart: Box Plot - Time Between Create Date and Update Date by Pipeline
 * Shows distribution with individual dots that can be clicked
 */
function renderTimeByPipelineChart() {
    const container = document.getElementById('chartTimeByPipeline');
    if (!container) return;
    
    // Clear existing content
    container.innerHTML = '<canvas id="chartTimeByPipelineCanvas"></canvas>';
    
    const canvas = document.getElementById('chartTimeByPipelineCanvas');
    const ctx = canvas.getContext('2d');
    
    // Group tickets by pipeline and calculate days between create and update
    const pipelineData = {};
    
    // Initialize pipelines
    pipelineCache.forEach(p => {
        pipelineData[p.Id] = { 
            name: p.Name, 
            color: p.Color || '#6366f1', 
            tickets: [] 
        };
    });
    
    // Calculate days between CreatedDate and LastUpdate for each ticket
    ticketsCache.forEach(ticket => {
        const pipelineId = ticket.PipelineId;
        if (pipelineData[pipelineId]) {
            const createdDate = new Date(ticket.CreatedDate);
            const lastUpdate = new Date(ticket.LastUpdate || ticket.CreatedDate);
            const daysDiff = Math.max(0, Math.floor((lastUpdate - createdDate) / (1000 * 60 * 60 * 24)));
            
            pipelineData[pipelineId].tickets.push({
                id: ticket.Id,
                title: ticket.Title || 'No Title',
                days: daysDiff,
                createdDate: createdDate,
                lastUpdate: lastUpdate
            });
        }
    });
    
    // Sort pipelines by order
    const sortedPipelines = [...pipelineCache].sort((a, b) => (a.Order || 0) - (b.Order || 0));
    
    // Prepare labels
    const labels = sortedPipelines.map(p => pipelineData[p.Id]?.name || p.Name);
    
    // Prepare box plot data
    const boxPlotData = sortedPipelines.map(p => {
        const tickets = pipelineData[p.Id]?.tickets || [];
        const days = tickets.map(t => t.days).sort((a, b) => a - b);
        
        if (days.length === 0) return null;
        
        return days;
    });
    
    // Prepare scatter data with ticket info for tooltips
    const scatterDatasets = [];
    const ticketInfoMap = {}; // Map to store ticket info for click events
    
    sortedPipelines.forEach((pipeline, pipelineIndex) => {
        const data = pipelineData[pipeline.Id];
        if (!data || data.tickets.length === 0) return;
        
        const scatterPoints = data.tickets.map((ticket, ticketIdx) => {
            // Add some horizontal jitter for better visibility
            const jitter = (Math.random() - 0.5) * 0.3;
            
            // Store ticket info for click handling
            const pointKey = `${pipelineIndex}_${ticketIdx}`;
            ticketInfoMap[pointKey] = ticket;
            
            return {
                x: pipelineIndex + jitter,
                y: ticket.days,
                ticketId: ticket.id,
                ticketTitle: ticket.title,
                ticketDays: ticket.days
            };
        });
        
        scatterDatasets.push({
            type: 'scatter',
            label: `${data.name} Tickets`,
            data: scatterPoints,
            backgroundColor: data.color + '99', // Add transparency
            borderColor: data.color,
            borderWidth: 1,
            pointRadius: 6,
            pointHoverRadius: 9,
            pointStyle: 'circle',
            order: 1 // Draw on top of box plot
        });
    });
    
    // Check if boxplot controller is available
    const hasBoxPlotPlugin = typeof Chart.controllers !== 'undefined' && 
                             (Chart.controllers.boxplot || Chart.registry?.controllers?.get('boxplot'));
    
    if (hasBoxPlotPlugin) {
        // Use Box Plot with Scatter overlay
        new Chart(ctx, {
            type: 'boxplot',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Days Distribution',
                        data: boxPlotData,
                        backgroundColor: sortedPipelines.map(p => (pipelineData[p.Id]?.color || '#6366f1') + '40'),
                        borderColor: sortedPipelines.map(p => pipelineData[p.Id]?.color || '#6366f1'),
                        borderWidth: 2,
                        outlierBackgroundColor: 'rgba(0,0,0,0)', // Hide default outliers
                        outlierBorderColor: 'rgba(0,0,0,0)',
                        order: 2
                    },
                    ...scatterDatasets
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                onClick: (event, elements) => {
                    if (elements.length > 0) {
                        const element = elements[0];
                        const datasetIndex = element.datasetIndex;
                        const dataset = event.chart.data.datasets[datasetIndex];
                        
                        if (dataset.type === 'scatter' && dataset.data[element.index]) {
                            const point = dataset.data[element.index];
                            if (point.ticketId) {
                                openTicketDetail(point.ticketId);
                            }
                        }
                    }
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                if (context.dataset.type === 'scatter' && context.raw) {
                                    return [
                                        `📋 ${context.raw.ticketTitle}`,
                                        `⏱️ ${context.raw.ticketDays} days`,
                                        `🔗 Click to view details`
                                    ];
                                }
                                return context.formattedValue;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Days between Create and Update'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Pipeline'
                        }
                    }
                }
            }
        });
    } else {
        // Fallback: Use scatter chart with manual box plot drawing
        console.log('Box plot plugin not available, using scatter with stats');
        
        // Calculate box plot stats for each pipeline
        const statsData = sortedPipelines.map((pipeline, idx) => {
            const tickets = pipelineData[pipeline.Id]?.tickets || [];
            const days = tickets.map(t => t.days).sort((a, b) => a - b);
            
            if (days.length === 0) return null;
            
            const n = days.length;
            const min = days[0];
            const max = days[n - 1];
            const q1 = days[Math.floor(n * 0.25)];
            const median = days[Math.floor(n * 0.5)];
            const q3 = days[Math.floor(n * 0.75)];
            
            return { min, q1, median, q3, max, color: pipelineData[pipeline.Id]?.color || '#6366f1' };
        });
        
        // Create scatter chart with all points
        const allScatterPoints = [];
        sortedPipelines.forEach((pipeline, pipelineIndex) => {
            const data = pipelineData[pipeline.Id];
            if (!data || data.tickets.length === 0) return;
            
            data.tickets.forEach(ticket => {
                const jitter = (Math.random() - 0.5) * 0.3;
                allScatterPoints.push({
                    x: pipelineIndex + jitter,
                    y: ticket.days,
                    ticketId: ticket.id,
                    ticketTitle: ticket.title,
                    ticketDays: ticket.days,
                    pipelineColor: data.color
                });
            });
        });
        
        // Custom plugin for drawing box plots
        const boxPlotPlugin = {
            id: 'customBoxPlot',
            beforeDatasetsDraw(chart) {
                const ctx = chart.ctx;
                const xAxis = chart.scales.x;
                const yAxis = chart.scales.y;
                
                statsData.forEach((stats, idx) => {
                    if (!stats) return;
                    
                    const x = xAxis.getPixelForValue(idx);
                    const boxWidth = 40;
                    
                    const yMin = yAxis.getPixelForValue(stats.min);
                    const yMax = yAxis.getPixelForValue(stats.max);
                    const yQ1 = yAxis.getPixelForValue(stats.q1);
                    const yQ3 = yAxis.getPixelForValue(stats.q3);
                    const yMedian = yAxis.getPixelForValue(stats.median);
                    
                    ctx.save();
                    
                    // Draw whiskers (vertical lines)
                    ctx.strokeStyle = stats.color;
                    ctx.lineWidth = 2;
                    
                    // Lower whisker
                    ctx.beginPath();
                    ctx.moveTo(x, yQ1);
                    ctx.lineTo(x, yMin);
                    ctx.stroke();
                    
                    // Upper whisker
                    ctx.beginPath();
                    ctx.moveTo(x, yQ3);
                    ctx.lineTo(x, yMax);
                    ctx.stroke();
                    
                    // Min/Max caps
                    ctx.beginPath();
                    ctx.moveTo(x - boxWidth/4, yMin);
                    ctx.lineTo(x + boxWidth/4, yMin);
                    ctx.stroke();
                    
                    ctx.beginPath();
                    ctx.moveTo(x - boxWidth/4, yMax);
                    ctx.lineTo(x + boxWidth/4, yMax);
                    ctx.stroke();
                    
                    // Draw box (Q1 to Q3)
                    ctx.fillStyle = stats.color + '40';
                    ctx.fillRect(x - boxWidth/2, yQ3, boxWidth, yQ1 - yQ3);
                    
                    ctx.strokeStyle = stats.color;
                    ctx.strokeRect(x - boxWidth/2, yQ3, boxWidth, yQ1 - yQ3);
                    
                    // Draw median line
                    ctx.strokeStyle = stats.color;
                    ctx.lineWidth = 3;
                    ctx.beginPath();
                    ctx.moveTo(x - boxWidth/2, yMedian);
                    ctx.lineTo(x + boxWidth/2, yMedian);
                    ctx.stroke();
                    
                    ctx.restore();
                });
            }
        };
        
        new Chart(ctx, {
            type: 'scatter',
            data: {
                datasets: [{
                    label: 'Tickets',
                    data: allScatterPoints,
                    backgroundColor: allScatterPoints.map(p => p.pipelineColor + '99'),
                    borderColor: allScatterPoints.map(p => p.pipelineColor),
                    borderWidth: 1,
                    pointRadius: 6,
                    pointHoverRadius: 9
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                onClick: (event, elements) => {
                    if (elements.length > 0) {
                        const element = elements[0];
                        const point = allScatterPoints[element.index];
                        if (point && point.ticketId) {
                            openTicketDetail(point.ticketId);
                        }
                    }
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const point = context.raw;
                                if (point) {
                                    return [
                                        `📋 ${point.ticketTitle}`,
                                        `⏱️ ${point.ticketDays} days`,
                                        `🔗 Click to view details`
                                    ];
                                }
                                return '';
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        type: 'linear',
                        min: -0.5,
                        max: labels.length - 0.5,
                        title: {
                            display: true,
                            text: 'Pipeline'
                        },
                        ticks: {
                            callback: function(value, index) {
                                const intVal = Math.round(value);
                                if (intVal >= 0 && intVal < labels.length && value === intVal) {
                                    return labels[intVal];
                                }
                                return '';
                            },
                            stepSize: 1
                        }
                    },
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Days between Create and Update'
                        }
                    }
                }
            },
            plugins: [boxPlotPlugin]
        });
    }
}

// ============================================
// Pipeline Modal Functions
// ============================================

/**
 * Open pipeline modal for create
 */
function createModalPopup() {
    document.getElementById('pipelineId').value = '';
    document.getElementById('pipelineName').value = '';
    document.getElementById('pipelineOrder').value = pipelineCache.length + 1;
    document.getElementById('pipelineColor').value = '#6366f1';
    document.getElementById('pipelineModalTitle').innerHTML = '<i class="fa-solid fa-layer-group text-primary mr-2"></i>Add Pipeline';
    
    document.getElementById('pipelineModal').showModal();
}

/**
 * Open pipeline modal for edit
 */
function editPipeline(pipelineId) {
    const pipeline = pipelineCache.find(p => p.Id === pipelineId);
    if (!pipeline) return;
    
    document.getElementById('pipelineId').value = pipeline.Id;
    document.getElementById('pipelineName').value = pipeline.Name || '';
    document.getElementById('pipelineOrder').value = pipeline.Order || 1;
    document.getElementById('pipelineColor').value = pipeline.Color || '#6366f1';
    document.getElementById('pipelineModalTitle').innerHTML = '<i class="fa-solid fa-layer-group text-primary mr-2"></i>Edit Pipeline';
    
    document.getElementById('pipelineModal').showModal();
}

/**
 * Save pipeline
 */
function savePipeline() {
    const id = document.getElementById('pipelineId').value;
    const name = document.getElementById('pipelineName').value;
    const order = parseInt(document.getElementById('pipelineOrder').value) || 1;
    const color = document.getElementById('pipelineColor').value;
    
    if (!name) {
        xalert('กรุณากรอกชื่อ Pipeline', 1, 3000);
        return;
    }
    
    const token = readToken();
    const isEdit = !!id;
    const endpoint = isEdit 
        ? `${url}/biomedapi/v2/helpdesk/pipeline/update`
        : `${url}/biomedapi/v2/helpdesk/pipeline/create`;
    
    const data = {
        Id: isEdit ? parseInt(id) : undefined,
        Name: name,
        Order: order,
        Color: color
    };
    
    const xhr = new XMLHttpRequest();
    xhr.open('POST', endpoint, true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.setRequestHeader('Authorization', `Bearer ${token}`);
    
    xhr.onreadystatechange = function() {
        if (xhr.readyState === XMLHttpRequest.DONE) {
            if (xhr.status === 200) {
                xalert(`Pipeline ${isEdit ? 'updated' : 'created'} successfully`, 0, 3000);
                document.getElementById('pipelineModal').close();
                
                // Reload pipelines
                GetHelpdeskPipeline((error, pipelines) => {
                    if (!error) {
                        pipelineCache = pipelines || [];
                        renderKanbanView();
                    }
                });
            } else {
                xalert('Error: ' + xhr.responseText, 1, -1);
            }
        }
    };
    
    xhr.send(JSON.stringify(data));
}

/**
 * Delete pipeline
 */
function deletePipeline(pipelineId) {
    if (!confirm('ต้องการลบ Pipeline นี้หรือไม่?')) return;
    
    const token = readToken();
    
    const xhr = new XMLHttpRequest();
    xhr.open('DELETE', `${url}/biomedapi/v2/helpdesk/pipeline/delete/${pipelineId}`, true);
    xhr.setRequestHeader('Authorization', `Bearer ${token}`);
    
    xhr.onreadystatechange = function() {
        if (xhr.readyState === XMLHttpRequest.DONE) {
            if (xhr.status === 200) {
                xalert('Pipeline deleted successfully', 0, 3000);
                
                // Reload pipelines
                GetHelpdeskPipeline((error, pipelines) => {
                    if (!error) {
                        pipelineCache = pipelines || [];
                        renderKanbanView();
                    }
                });
            } else {
                xalert('Error: ' + xhr.responseText, 1, -1);
            }
        }
    };
    
    xhr.send();
}

// ============================================
// Ticket Modal Functions
// ============================================

/**
 * Open ticket modal for create
 */
function createTicketPopup(pipelineId) {
    document.getElementById('ticketId').value = '';
    document.getElementById('ticketName').value = '';
    document.getElementById('ticketDescription').value = '';
    document.getElementById('ticketPriority').value = '2';
    document.getElementById('ticketExpectedDate').value = '';
    document.getElementById('ticketModalTitle').innerHTML = '<i class="fa-solid fa-ticket text-primary mr-2"></i>Add Ticket';
    
    // Populate pipeline dropdown
    const pipelineSelect = document.getElementById('ticketPipeline');
    pipelineSelect.innerHTML = pipelineCache.map(p => 
        `<option value="${p.Id}" ${p.Id === pipelineId ? 'selected' : ''}>${p.Name}</option>`
    ).join('');
    
    // Populate contact dropdown
    const contactSelect = document.getElementById('ticketContact');
    contactSelect.innerHTML = '<option value="">-- เลือก Contact --</option>' + 
        contactsCache.map(c => `<option value="${c.Id}">${c.Name}</option>`).join('');
    
    // Populate product dropdown
    const productSelect = document.getElementById('ticketProduct');
    productSelect.innerHTML = '<option value="">-- เลือกสินค้า --</option>' + 
        productsCache.map(p => `<option value="${p.Id}">${p.Name}</option>`).join('');
    
    // Populate sale area dropdown
    const saleAreaSelect = document.getElementById('ticketSaleArea');
    saleAreaSelect.innerHTML = '<option value="">-- เลือกพื้นที่ขาย --</option>' + 
        saleAreasCache.map(sa => `<option value="${sa.Id}">${sa.Name}</option>`).join('');
    
    // Initialize assign multiselect
    const assignContainer = document.getElementById('ticketAssignContainer');
    assignContainer.innerHTML = '<div id="ticketAssignSelect"></div>';
    
    ticketAssignSelect = new MultiSelect('ticketAssignSelect', {
        options: usersCache.map(u => ({ value: u.Id.toString(), label: u.Name })),
        placeholder: 'เลือกผู้รับผิดชอบ...',
        badgeClass: 'badge-secondary',
        searchable: true
    });
    
    document.getElementById('ticketModal').showModal();
}

/**
 * Save ticket
 */
function saveTicket() {
    const id = document.getElementById('ticketId').value;
    const name = document.getElementById('ticketName').value;
    const description = document.getElementById('ticketDescription').value;
    const pipelineId = document.getElementById('ticketPipeline').value;
    const priority = document.getElementById('ticketPriority').value;
    const contactId = document.getElementById('ticketContact').value;
    const productId = document.getElementById('ticketProduct').value;
    const saleAreaId = document.getElementById('ticketSaleArea').value;
    
    if (!name) {
        xalert('กรุณากรอกชื่อ Ticket', 1, 3000);
        return;
    }
    
    const token = readToken();
    const isEdit = !!id;
    const endpoint = isEdit 
        ? `${url}/biomedapi/v2/helpdesk/ticket/update`
        : `${url}/biomedapi/v2/helpdesk/ticket/create`;
    
    const data = {
        Id: isEdit ? parseInt(id) : undefined,
        Title: name,
        Description: description,
        PipelineId: parseInt(pipelineId),
        Priority: parseInt(priority),
        ContactId: contactId ? parseInt(contactId) : null,
        ProductId: productId ? parseInt(productId) : null,
        SaleAreaId: saleAreaId ? parseInt(saleAreaId) : null
    };
    
    const xhr = new XMLHttpRequest();
    xhr.open('POST', endpoint, true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.setRequestHeader('Authorization', `Bearer ${token}`);
    
    xhr.onreadystatechange = function() {
        if (xhr.readyState === XMLHttpRequest.DONE) {
            if (xhr.status === 200) {
                xalert(`Ticket ${isEdit ? 'updated' : 'created'} successfully`, 0, 3000);
                document.getElementById('ticketModal').close();
                
                // Redirect to detail page
                const ticketId = xhr.responseText;
                if (!isEdit && ticketId) {
                    window.location.href = `helpdesk-detail.html?leadid=${ticketId}`;
                } else {
                    applyFilters();
                }
            } else {
                xalert('Error: ' + xhr.responseText, 1, -1);
            }
        }
    };
    
    xhr.send(JSON.stringify(data));
}

/**
 * Open ticket detail modal
 */
function openTicketDetail(ticketId) {
    // Redirect to detail page
    window.location.href = `helpdesk-detail.html?leadid=${ticketId}`;
}

/**
 * Edit ticket
 */
function editTicket(ticketId) {
    const ticket = ticketsCache.find(t => t.Id === ticketId);
    if (!ticket) return;
    
    document.getElementById('ticketId').value = ticket.Id;
    document.getElementById('ticketName').value = ticket.Title || '';
    document.getElementById('ticketDescription').value = ticket.Description || '';
    document.getElementById('ticketPriority').value = ticket.Priority || 2;
    document.getElementById('ticketModalTitle').innerHTML = '<i class="fa-solid fa-ticket text-primary mr-2"></i>Edit Ticket';
    
    // Populate dropdowns and select values
    const pipelineSelect = document.getElementById('ticketPipeline');
    pipelineSelect.innerHTML = pipelineCache.map(p => 
        `<option value="${p.Id}" ${p.Id === ticket.PipelineId ? 'selected' : ''}>${p.Name}</option>`
    ).join('');
    
    const contactSelect = document.getElementById('ticketContact');
    contactSelect.innerHTML = '<option value="">-- เลือก Contact --</option>' + 
        contactsCache.map(c => `<option value="${c.Id}" ${c.Id === ticket.ContactId ? 'selected' : ''}>${c.Name}</option>`).join('');
    
    const productSelect = document.getElementById('ticketProduct');
    productSelect.innerHTML = '<option value="">-- เลือกสินค้า --</option>' + 
        productsCache.map(p => `<option value="${p.Id}" ${p.Id === ticket.ProductId ? 'selected' : ''}>${p.Name}</option>`).join('');
    
    const saleAreaSelect = document.getElementById('ticketSaleArea');
    saleAreaSelect.innerHTML = '<option value="">-- เลือกพื้นที่ขาย --</option>' + 
        saleAreasCache.map(sa => `<option value="${sa.Id}" ${sa.Id === ticket.SaleAreaId ? 'selected' : ''}>${sa.Name}</option>`).join('');
    
    // Initialize assign multiselect
    const assignContainer = document.getElementById('ticketAssignContainer');
    assignContainer.innerHTML = '<div id="ticketAssignSelect"></div>';
    
    ticketAssignSelect = new MultiSelect('ticketAssignSelect', {
        options: usersCache.map(u => ({ value: u.Id.toString(), label: u.Name })),
        placeholder: 'เลือกผู้รับผิดชอบ...',
        badgeClass: 'badge-secondary',
        searchable: true
    });
    
    document.getElementById('ticketModal').showModal();
}

/**
 * Delete ticket
 */
function deleteTicket(ticketId) {
    if (!confirm('ต้องการลบ Ticket นี้หรือไม่?')) return;
    
    const token = readToken();
    
    const xhr = new XMLHttpRequest();
    xhr.open('DELETE', `${url}/biomedapi/v2/helpdesk/ticket/delete/${ticketId}`, true);
    xhr.setRequestHeader('Authorization', `Bearer ${token}`);
    
    xhr.onreadystatechange = function() {
        if (xhr.readyState === XMLHttpRequest.DONE) {
            if (xhr.status === 200) {
                xalert('Ticket deleted successfully', 0, 3000);
                applyFilters();
            } else {
                xalert('Error: ' + xhr.responseText, 1, -1);
            }
        }
    };
    
    xhr.send();
}

// ============================================
// API Helper Functions
// ============================================

/**
 * Get Helpdesk Pipelines
 */
function GetHelpdeskPipeline(callback) {
    const token = readToken();
    
    const xhr = new XMLHttpRequest();
    xhr.open('GET', `${url}/biomedapi/v2/helpdesk/pipeline`, true);
    xhr.setRequestHeader('Authorization', `Bearer ${token}`);
    
    xhr.onreadystatechange = function() {
        if (xhr.readyState === XMLHttpRequest.DONE) {
            if (xhr.status === 200) {
                const data = JSON.parse(xhr.responseText);
                callback(null, data);
            } else {
                callback(xhr.responseText, null);
            }
        }
    };
    
    xhr.send();
}

/**
 * Get Tickets
 */
function getTickets(query, callback) {
    const token = readToken();
    
    const xhr = new XMLHttpRequest();
    xhr.open('POST', `${url}/biomedapi/v2/helpdesk/tickets`, true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.setRequestHeader('Authorization', `Bearer ${token}`);
    
    xhr.onreadystatechange = function() {
        if (xhr.readyState === XMLHttpRequest.DONE) {
            if (xhr.status === 200) {
                const data = JSON.parse(xhr.responseText);
                callback(null, data);
            } else {
                callback(xhr.responseText, null);
            }
        }
    };
    
    xhr.send(JSON.stringify(query));
}
