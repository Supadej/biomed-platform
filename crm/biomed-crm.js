/**
 * Biomed CRM - daisyUI Version (Standalone)
 * Minimal dependency on biomed-global.js
 * 
 * Dependencies from biomed-global.js:
 * - readToken() - for authentication
 * - getColor() - for color management
 * - url - API base URL
 * - Translator - Quarter mapping
 */

// ============================================
// Cache Variables
// ============================================
let pipelineCache = [];
let leadCache = [];
let usersCache = [];
let contactsCache = [];
let productsCache = [];
let saleAreasCache = [];
let targetsCache = [];
let myUserCache = null;

// ============================================
// Quarter Mode: 'fiscal' (FYQ) or 'standard' (YQ)
// ============================================
let quarterMode = localStorage.getItem('crmQuarterMode') || 'fiscal';

// Build standard (calendar year) Translator: "Q1 2023", "Q2 2023", ...
const StandardTranslator = [];
for (let year = 2023; year <= new Date().getFullYear() + 2; year++) {
  for (let q = 1; q <= 4; q++) {
    StandardTranslator.push(`Q${q} ${year}`);
  }
}

/**
 * Get the active Translator array based on current quarter mode
 */
function getActiveTranslator() {
  return quarterMode === 'standard' ? StandardTranslator : Translator;
}

/**
 * Switch quarter mode between 'fiscal' (FYQ), 'standard' (YQ), or 'manual'
 */
function setQuarterMode(mode) {
  quarterMode = mode;
  localStorage.setItem('crmQuarterMode', mode);

  // Update toggle button UI
  const btnFYQ = document.getElementById('btnFYQ');
  const btnYQ = document.getElementById('btnYQ');
  const btnManual = document.getElementById('btnManual');
  const desc = document.getElementById('quarterModeDesc');
  const slidersContainer = document.getElementById('quarterSlidersContainer');
  const manualContainer = document.getElementById('manualDateContainer');

  btnFYQ?.classList.remove('btn-active');
  btnYQ?.classList.remove('btn-active');
  btnManual?.classList.remove('btn-active');

  if (mode === 'fiscal') {
    btnFYQ?.classList.add('btn-active');
    if (desc) desc.textContent = 'Fiscal Year Quarter (Q1=May-Jul)';
    if (slidersContainer) slidersContainer.classList.remove('hidden');
    if (manualContainer) manualContainer.classList.add('hidden');
    reinitializeDateSliders();
  } else if (mode === 'standard') {
    btnYQ?.classList.add('btn-active');
    if (desc) desc.textContent = 'Year Quarter (Q1=Jan-Mar)';
    if (slidersContainer) slidersContainer.classList.remove('hidden');
    if (manualContainer) manualContainer.classList.add('hidden');
    reinitializeDateSliders();
  } else if (mode === 'manual') {
    btnManual?.classList.add('btn-active');
    if (desc) desc.textContent = 'Manual Date Range';
    if (slidersContainer) slidersContainer.classList.add('hidden');
    if (manualContainer) manualContainer.classList.remove('hidden');
    _initManualDateDefaults();
  }
}

/**
 * Set default values for manual date inputs (current month range)
 * Only sets values if the inputs are currently empty
 */
function _initManualDateDefaults() {
  const now = new Date();
  const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1);
  const endOfMonth = new Date(now.getFullYear(), now.getMonth() + 1, 0);
  
  // Format as YYYY-MM-DD for <input type="date">
  const fmt = (d) => d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
  
  const fields = ['manualCreationStart', 'manualCreationEnd', 'manualUpdateStart', 'manualUpdateEnd', 'manualExpectedStart', 'manualExpectedEnd'];
  fields.forEach(id => {
    const el = document.getElementById(id);
    if (el && !el.value) {
      if (id.endsWith('Start')) el.value = fmt(startOfMonth);
      if (id.endsWith('End')) el.value = fmt(endOfMonth);
    }
  });
}

/**
 * Get date range for standard (calendar year) quarter
 */
function getStandardDateRangeFromQuarterIndex(quarterIndex) {
  if (quarterIndex < 0 || quarterIndex >= StandardTranslator.length) return null;
  const quarterStr = StandardTranslator[quarterIndex]; // e.g. "Q1 2023"
  const match = quarterStr.match(/Q(\d)\s+(\d{4})/);
  if (!match) return null;

  const q = parseInt(match[1]);
  const year = parseInt(match[2]);
  // Standard: Q1=Jan-Mar, Q2=Apr-Jun, Q3=Jul-Sep, Q4=Oct-Dec
  const startMonth = (q - 1) * 3; // 0,3,6,9
  const endMonth = startMonth + 2;  // 2,5,8,11

  const startDate = new Date(year, startMonth, 1);
  const endDate = new Date(year, endMonth + 1, 0);
  endDate.setHours(23, 59, 59);
  return { startDate, endDate };
}

/**
 * Get standard quarter and year by date (calendar year quarters)
 */
function getStandardQuarterAndYearByDate(date) {
  const month = date.getMonth();
  const year = date.getFullYear();
  let quarter;
  if (month <= 2) quarter = 'Q1';
  else if (month <= 5) quarter = 'Q2';
  else if (month <= 8) quarter = 'Q3';
  else quarter = 'Q4';
  return { quarter, year, month };
}

// ============================================
// Utility Functions (Self-contained)
// ============================================

function AutoCommaLocal(number) {
    if (number == null || isNaN(number)) return '0';
    // Round to max 2 decimal places
    const rounded = Math.round(number * 100) / 100;
    // Format with commas and max 2 decimal places
    return rounded.toLocaleString('en-US', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 2
    });
}

function formatDateOnlyLocal(date) {
    if (!date) return '-';
    const options = { day: '2-digit', month: 'short', year: 'numeric' };
    return new Date(date).toLocaleDateString('th-TH', options);
}

function getRemainingDaysLocal(endDate) {
    const today = new Date();
    const targetDate = new Date(endDate);
    const timeDiff = targetDate.getTime() - today.getTime();
    const daysDiff = Math.ceil(timeDiff / (1000 * 3600 * 24));
    if (daysDiff >= 0) {
        return (daysDiff <= 30 ? '⚠️ ' : '') + daysDiff + " วันที่เหลือ";
    }
    return '❌ เกิน ' + Math.abs(daysDiff) + ' วัน';
}

function timeFormaterLocal(input) {
    const options = {
        month: "numeric",
        day: "numeric",
        year: "numeric",
        hour: "numeric",
        minute: "numeric",
        second: "numeric",
        hour12: true,
    };
    return new Date(input).toLocaleString("en-US", options);
}

function getQuarterAndYearByDateLocal(date) {
    const month = date.getMonth();
    const year = month <= 3 ? date.getFullYear() : date.getFullYear() + 1;
    let quarter;
    if (month == 4 || month == 5 || month == 6) quarter = "Q1";
    if (month == 7 || month == 8 || month == 9) quarter = "Q2";
    if (month == 10 || month == 11 || month == 0) quarter = "Q3";
    if (month == 1 || month == 2 || month == 3) quarter = "Q4";
    return { quarter, year, month };
}

// ============================================
// API Functions (Using correct endpoints)
// ============================================

/**
 * Get current user with SaleAreaUsers and ProductUsers
 * Endpoint: GET /biomedapi/myuser (same as myUserRequest in biomed-global.js)
 */
async function crmGetMyUser() {
    const token = readToken();
    if (!token) return null;

    // Check sessionStorage cache first (same as myUserRequest)
    const cached = sessionStorage.getItem("myUser");
    if (cached) {
        return JSON.parse(cached);
    }

    try {
        const response = await fetch(url + '/biomedapi/myuser', {
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}` 
            }
        });
        if (!response.ok) throw new Error('Failed to fetch user');
        const user = await response.json();
        // Save to sessionStorage (same as myUserRequest)
        sessionStorage.setItem("myUser", JSON.stringify(user));
        return user;
    } catch (error) {
        console.error('Error fetching current user:', error);
        return null;
    }
}

/**
 * Get all users
 * Endpoint: GET /biomedapi/users
 * Filters out disabled users (Enabled === false) and sorts by FirstName
 */
async function crmGetUsers() {
    const token = readToken();
    if (!token) return [];

    // Check session cache
    const cached = sessionStorage.getItem('users');
    if (cached) {
        const allUsers = JSON.parse(cached);
        // Filter out disabled users (Enabled === false, but null/undefined counts as enabled)
        usersCache = allUsers
            .filter(u => u.Enabled !== false)
            .sort((a, b) => (a.FirstName || '').localeCompare(b.FirstName || ''));
        return usersCache;
    }

    try {
        const response = await fetch(url + '/biomedapi/users', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!response.ok) throw new Error('Failed to fetch users');
        const allUsers = await response.json();
        // Store all users in session (including disabled for getUserById)
        sessionStorage.setItem('users', JSON.stringify(allUsers));
        // Filter out disabled users (Enabled === false, but null/undefined counts as enabled)
        usersCache = allUsers
            .filter(u => u.Enabled !== false)
            .sort((a, b) => (a.FirstName || '').localeCompare(b.FirstName || ''));
        return usersCache;
    } catch (error) {
        console.error('Error fetching users:', error);
        return [];
    }
}

/**
 * Get CRM pipelines
 * Endpoint: GET /biomedapi/v2/crm/pipelines
 */
async function crmGetPipelines() {
    const token = readToken();
    if (!token) return [];

    // Check session cache
    const cached = sessionStorage.getItem('pipelines');
    if (cached) {
        pipelineCache = JSON.parse(cached);
        return pipelineCache;
    }

    try {
        const response = await fetch(url + '/biomedapi/v2/crm/pipelines', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!response.ok) throw new Error('Failed to fetch pipelines');
        pipelineCache = await response.json();
        pipelineCache.sort((a, b) => a.Order - b.Order);
        sessionStorage.setItem('pipelines', JSON.stringify(pipelineCache));
        return pipelineCache;
    } catch (error) {
        console.error('Error fetching pipelines:', error);
        return [];
    }
}

/**
 * Get leads with filter
 * Endpoint: POST /biomedapi/v2/crm/leads
 */
async function crmGetLeads(query = {}) {
    const token = readToken();
    if (!token) return [];

    try {
        const response = await fetch(url + '/biomedapi/v2/crm/leads', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(query)
        });
        if (!response.ok) throw new Error('Failed to fetch leads');
        leadCache = await response.json();
        return leadCache;
    } catch (error) {
        console.error('Error fetching leads:', error);
        return [];
    }
}

/**
 * Get all contacts
 * Endpoint: GET /biomedapi/contacts
 * Sorted by Name
 */
async function crmGetContacts() {
    const token = readToken();
    if (!token) return [];

    const cached = sessionStorage.getItem('contacts');
    if (cached) {
        contactsCache = JSON.parse(cached);
        // Sort by Name
        contactsCache.sort((a, b) => (a.Name || '').localeCompare(b.Name || ''));
        return contactsCache;
    }

    try {
        const response = await fetch(url + '/biomedapi/contacts', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!response.ok) throw new Error('Failed to fetch contacts');
        contactsCache = await response.json();
        sessionStorage.setItem('contacts', JSON.stringify(contactsCache));
        // Sort by Name
        contactsCache.sort((a, b) => (a.Name || '').localeCompare(b.Name || ''));
        return contactsCache;
    } catch (error) {
        console.error('Error fetching contacts:', error);
        return [];
    }
}

/**
 * Get all products
 * Endpoint: GET /biomedapi/products
 */
async function crmGetProducts() {
    const token = readToken();
    if (!token) return [];

    const cached = sessionStorage.getItem('products');
    if (cached) {
        productsCache = JSON.parse(cached);
        return productsCache;
    }

    try {
        const response = await fetch(url + '/biomedapi/products', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!response.ok) throw new Error('Failed to fetch products');
        productsCache = await response.json();
        sessionStorage.setItem('products', JSON.stringify(productsCache));
        return productsCache;
    } catch (error) {
        console.error('Error fetching products:', error);
        return [];
    }
}

/**
 * Get all sale areas
 * Endpoint: GET /biomedapi/saleareas
 */
async function crmGetSaleAreas() {
    const token = readToken();
    if (!token) return [];

    const cached = sessionStorage.getItem('saleareas');
    if (cached) {
        saleAreasCache = JSON.parse(cached);
        return saleAreasCache;
    }

    try {
        const response = await fetch(url + '/biomedapi/saleareas', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!response.ok) throw new Error('Failed to fetch sale areas');
        saleAreasCache = await response.json();
        sessionStorage.setItem('saleareas', JSON.stringify(saleAreasCache));
        return saleAreasCache;
    } catch (error) {
        console.error('Error fetching sale areas:', error);
        return [];
    }
}

/**
 * Get targets with filter
 * Endpoint: POST /biomedapi/targets
 */
async function crmGetTargets(query = {}) {
    const token = readToken();
    if (!token) return [];

    try {
        const response = await fetch(url + '/biomedapi/targets', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(query)
        });
        if (!response.ok) throw new Error('Failed to fetch targets');
        targetsCache = await response.json();
        return targetsCache;
    } catch (error) {
        console.error('Error fetching targets:', error);
        return [];
    }
}

// ============================================
// Helper Functions
// ============================================

function getUniqueLeads(leads) {
    return leads.reduce((acc, lead) => {
        if (!acc.some(existingLead => existingLead.Id === lead.Id)) {
            acc.push(lead);
        }
        return acc;
    }, []);
}

function getUserById(userId) {
    // First try usersCache (enabled users only)
    let user = usersCache.find(u => u.Id === userId);
    if (user) return user;
    
    // If not found, try sessionStorage which has all users (including disabled)
    const cached = sessionStorage.getItem('users');
    if (cached) {
        const allUsers = JSON.parse(cached);
        return allUsers.find(u => u.Id === userId);
    }
    return null;
}

function getContactById(contactId) {
    return contactsCache.find(c => c.Id === contactId);
}

function getProductById(productId) {
    return productsCache.find(p => p.Id === productId);
}

function getSaleAreaById(saleAreaId) {
    return saleAreasCache.find(s => s.Id === saleAreaId);
}

function getPipelineById(pipelineId) {
    return pipelineCache.find(p => p.Id === pipelineId);
}

/**
 * Process targets locally using cached data (faster than processTargets in biomed-global.js)
 */
async function processTargetsLocal(targets) {
    if (!targets || targets.length === 0) return targets;

    // Sort by EndDate descending
    const sortedTargets = targets.sort((a, b) => new Date(b.EndDate).getTime() - new Date(a.EndDate).getTime());
    
    // Load products and saleAreas if not cached
    if (productsCache.length === 0) {
        productsCache = await crmGetProducts();
    }
    if (saleAreasCache.length === 0) {
        saleAreasCache = await crmGetSaleAreas();
    }

    // Process each target using cache
    for (const target of sortedTargets) {
        target.Product = productsCache.find(p => p.Id === target.ProductID) || null;
        target.SaleArea = saleAreasCache.find(s => s.Id === target.SaleAreaID) || null;
        target.Leads = [];
        target.Color = await getColor(target.ProductID);
    }

    // Get leads for all targets in one query
    const minStartDate = sortedTargets.reduce((min, t) => new Date(t.StartDate) < min ? new Date(t.StartDate) : min, new Date(sortedTargets[0].StartDate));
    const maxEndDate = sortedTargets.reduce((max, t) => new Date(t.EndDate) > max ? new Date(t.EndDate) : max, new Date(sortedTargets[0].EndDate));

    const productIDs = [...new Set(sortedTargets.map(t => t.ProductID))];
    const saleAreaIDs = [...new Set(sortedTargets.map(t => t.SaleAreaID))];

    const leadsQuery = {
        ProductIDs: productIDs,
        SaleAreaIDs: saleAreaIDs,
        ExpectedStart: timeFormaterLocal(minStartDate),
        ExpectedEnd: timeFormaterLocal(maxEndDate),
        DeepSearch: true
    };

    const allLeads = await crmGetLeads(leadsQuery);

    // Match leads to targets
    for (const lead of allLeads) {
        const target = sortedTargets.find(t =>
            t.ProductID === lead.ProductId &&
            t.SaleAreaID === lead.SaleAreaId &&
            new Date(lead.Expected) >= new Date(t.StartDate) &&
            new Date(lead.Expected) <= new Date(t.EndDate)
        );
        if (target) {
            target.Leads.push(lead);
        }
    }

    return sortedTargets;
}

// ============================================
// Target Display
// ============================================

async function targetDisplay(saleAreaIDs = null, productIDs = null, expectedStart = null, expectedEnd = null) {
    console.log("=== targetDisplay() called ===");
    console.log("Input params - saleAreaIDs:", saleAreaIDs, "productIDs:", productIDs);
    
    const targetsContainer = document.getElementById('targetsContainer');
    if (!targetsContainer) return;

    targetsContainer.innerHTML = `
        <div class="flex items-center justify-center py-8 text-base-content/50">
            <span class="loading loading-spinner loading-md mr-2"></span>
            กำลังโหลดเป้าหมาย...
        </div>
    `;

    try {
        const myUser = await crmGetMyUser();
        console.log("targetDisplay myUser:", myUser);
        console.log("targetDisplay myUser.SaleAreaUsers:", myUser?.SaleAreaUsers);
        console.log("targetDisplay myUser.ProductUsers:", myUser?.ProductUsers);
        
        if (!myUser) {
            targetsContainer.innerHTML = '<div class="alert alert-error">กรุณาเข้าสู่ระบบ</div>';
            return;
        }

        // Use user's sale areas and products if not provided or empty array
        const querySaleAreaIDs = (saleAreaIDs && saleAreaIDs.length > 0) ? saleAreaIDs : (myUser.SaleAreaUsers?.map(sa => sa.SaleAreaId) || []);
        const queryProductIDs = (productIDs && productIDs.length > 0) ? productIDs : (myUser.ProductUsers?.map(pu => pu.ProductId) || []);
        
        console.log("Final querySaleAreaIDs:", querySaleAreaIDs);
        console.log("Final queryProductIDs:", queryProductIDs);

        // Build query for targets API (API expects lowercase keys)
        const query = {
            saleAreaIDs: querySaleAreaIDs,
            productIDs: queryProductIDs,
            expectedStart: expectedStart,
            expectedEnd: expectedEnd,
            DeepSearch: true
        };

        console.log("Target Query:", query);

        // Use promiseTargets and processTargets from biomed-global.js
        const rawTargets = await promiseTargets(query);
        console.log("Raw Targets:", rawTargets);

        if (!rawTargets || rawTargets.length === 0) {
            targetsContainer.innerHTML = `
                <div class="text-center py-8 text-base-content/50">
                    <i class="fa-solid fa-bullseye text-3xl mb-2"></i>
                    <p>ไม่มีเป้าหมายในขณะนี้</p>
                </div>
            `;
            return;
        }

        // Process targets using local function (faster, uses cache)
        console.log(`Processing ${rawTargets.length} targets...`);
        const targets = await processTargetsLocal(rawTargets);
        console.log("Processed Targets:", targets);
        
        // Save to cache for detail modal
        targetsCache = targets;

        // Build beautiful target cards
        let html = `
            <div class="mb-3">
                <h3 class="text-lg font-bold flex items-center gap-2 mb-3">
                    <i class="fa-solid fa-bullseye text-secondary"></i>
                    เป้าหมายของคุณ
                    <span class="badge badge-secondary">${targets.length}</span>
                </h3>
            </div>
            <div class="targets-scroll">
        `;

        // Calculate totals
        const totalTarget = targets.reduce((sum, t) => sum + (t.TargetValue || 0), 0);
        const totalExpected = targets.reduce((sum, t) => sum + t.Leads.reduce((s, l) => s + (l.ExpectedRevenue || 0), 0), 0);
        const totalAchieved = targets.reduce((sum, t) => sum + t.Leads.reduce((s, l) => s + (l.AchivedRevenue || 0), 0), 0);
        const totalLeads = targets.reduce((sum, t) => sum + t.Leads.length, 0);
        const overallPercent = totalTarget > 0 ? Math.round((totalAchieved / totalTarget) * 100) : 0;

        // Summary card
        html += `
            <div class="target-card card bg-gradient-to-br from-primary to-secondary text-primary-content shadow-xl flex-shrink-0">
                <div class="card-body p-4">
                    <h4 class="font-bold text-lg flex items-center gap-2">
                        <i class="fa-solid fa-chart-pie"></i> ภาพรวมเป้าหมาย
                    </h4>
                    <div class="grid grid-cols-2 gap-2 mt-2 text-xs">
                        <div class="bg-white/20 rounded-lg p-2 text-center">
                            <div class="text-xl font-bold">${targets.length}</div>
                            <div class="opacity-80">เป้าหมาย</div>
                        </div>
                        <div class="bg-white/20 rounded-lg p-2 text-center">
                            <div class="text-xl font-bold">${totalLeads}</div>
                            <div class="opacity-80">Leads</div>
                        </div>
                    </div>
                    <div class="mt-3 space-y-1 text-xs">
                        <div class="flex justify-between">
                            <span>เป้าหมาย</span>
                            <span class="font-bold">${AutoCommaLocal(totalTarget)} ฿</span>
                        </div>
                        <div class="flex justify-between">
                            <span>คาดหวัง</span>
                            <span class="font-bold">${AutoCommaLocal(totalExpected)} ฿</span>
                        </div>
                        <div class="flex justify-between">
                            <span>สำเร็จ</span>
                            <span class="font-bold">${AutoCommaLocal(totalAchieved)} ฿ (${overallPercent}%)</span>
                        </div>
                    </div>
                    <progress class="progress progress-accent w-full mt-2" value="${overallPercent}" max="100"></progress>
                </div>
            </div>
        `;

        // Individual target cards
        for (const target of targets) {
            const sumExpected = target.Leads.reduce((sum, l) => sum + (l.ExpectedRevenue || 0), 0);
            const sumAchieved = target.Leads.reduce((sum, l) => sum + (l.AchivedRevenue || 0), 0);
            const achievedPercent = target.TargetValue > 0 ? Math.round((sumAchieved / target.TargetValue) * 100) : 0;
            const remainDays = getRemainingDaysLocal(target.EndDate);
            
            // Status badge based on remaining days
            const now = new Date();
            const endDate = new Date(target.EndDate);
            const daysLeft = Math.ceil((endDate - now) / (1000 * 60 * 60 * 24));
            
            let statusBadge = '';
            let borderColor = target.Color?.color?.code || '#6366f1';
            
            if (daysLeft <= 0) {
                statusBadge = `<span class="badge badge-error badge-sm">หมดเวลา</span>`;
            } else if (daysLeft <= 7) {
                statusBadge = `<span class="badge badge-warning badge-sm">${daysLeft} วัน</span>`;
            } else if (daysLeft <= 30) {
                statusBadge = `<span class="badge badge-info badge-sm">${daysLeft} วัน</span>`;
            } else {
                statusBadge = `<span class="badge badge-success badge-sm">${daysLeft} วัน</span>`;
            }

            // Emoji based on achievement
            let emoji = '😢';
            if (achievedPercent >= 100) emoji = '😎';
            else if (achievedPercent >= 90) emoji = '😍';
            else if (achievedPercent >= 80) emoji = '😊';

            html += `
                <div class="target-card card bg-base-100 shadow-lg flex-shrink-0 cursor-pointer hover:shadow-xl transition-all" 
                     style="border-left: 4px solid ${borderColor}"
                     onclick="showTargetDetail(${target.Id})"
                     title="คลิกเพื่อดูรายละเอียด">
                    <div class="card-body p-4">
                        <!-- Header -->
                        <div class="flex items-start justify-between gap-2">
                            <div class="flex-1 min-w-0">
                                <h4 class="font-bold text-sm">${target.Product?.Name || 'N/A'}-${target.SaleArea?.Name || 'N/A'}</h4>
                                <p class="text-xs text-base-content/60 truncate">${target.Name || ''}</p>
                            </div>
                            ${statusBadge}
                        </div>
                        
                        <!-- Progress Circle -->
                        <div class="flex items-center justify-center my-3">
                            <div class="radial-progress text-primary" style="--value:${Math.min(achievedPercent, 100)}; --size:5rem; --thickness:6px;" role="progressbar">
                                <span class="text-lg font-bold">${achievedPercent}%</span>
                            </div>
                        </div>
                        
                        <!-- Stats -->
                        <div class="space-y-1.5 text-xs">
                            <div class="flex justify-between items-center">
                                <span class="text-base-content/60">Target</span>
                                <span class="font-bold">${AutoCommaLocal(target.TargetValue || 0)} ฿</span>
                            </div>
                            <div class="flex justify-between items-center">
                                <span class="text-base-content/60">Expected</span>
                                <span class="font-bold text-info">${AutoCommaLocal(sumExpected)} ฿</span>
                            </div>
                            <div class="flex justify-between items-center">
                                <span class="text-base-content/60">Achieved</span>
                                <span class="font-bold text-success">${AutoCommaLocal(sumAchieved)} ฿ ${emoji}</span>
                            </div>
                            <div class="flex justify-between items-center">
                                <span class="text-base-content/60">Leads</span>
                                <span class="font-bold">${target.Leads.length} รายการ</span>
                            </div>
                        </div>
                        
                        <!-- Date -->
                        <div class="text-[10px] text-base-content/50 mt-2 pt-2 border-t border-base-200 text-center">
                            <i class="fa-regular fa-calendar mr-1"></i>
                            ${formatDateOnlyLocal(target.StartDate)} - ${formatDateOnlyLocal(target.EndDate)}
                        </div>
                    </div>
                </div>
            `;
        }

        html += '</div>';
        targetsContainer.innerHTML = html;

    } catch (error) {
        console.error('Error displaying targets:', error);
        targetsContainer.innerHTML = `
            <div class="alert alert-error">
                <i class="fa-solid fa-exclamation-circle"></i>
                <span>เกิดข้อผิดพลาดในการโหลดเป้าหมาย: ${error.message}</span>
            </div>
        `;
    }
}

// ============================================
// Pipeline/Lead Display (Card View)
// ============================================

async function displayLeads(query = {}) {
    const cardViewContainer = document.getElementById('cardViewContainer');
    if (!cardViewContainer) return;

    cardViewContainer.innerHTML = `
        <div class="card-body p-4">
            <div class="flex items-center justify-center py-16 text-base-content/50">
                <span class="loading loading-spinner loading-lg mr-3"></span>
                กำลังโหลด Pipeline...
            </div>
        </div>
    `;

    try {
        const myUser = await crmGetMyUser();
        if (!myUser) {
            cardViewContainer.innerHTML = '<div class="card-body"><div class="alert alert-error">ไม่สามารถโหลดข้อมูลผู้ใช้ได้</div></div>';
            return;
        }

        // SaleAreaIDs and ProductIDs should already be set by applyFilters()
        // This is a fallback for direct calls to displayLeads()
        if (!query.SaleAreaIDs || query.SaleAreaIDs.length === 0) {
            query.SaleAreaIDs = myUser.SaleAreaUsers?.map(sa => sa.SaleAreaId) || [];
        }
        if (!query.ProductIDs || query.ProductIDs.length === 0) {
            query.ProductIDs = myUser.ProductUsers?.map(pu => pu.ProductId) || [];
        }

        // Load all data in parallel
        const [pipelines, leads, users, contacts, products, saleAreas] = await Promise.all([
            crmGetPipelines(),
            crmGetLeads(query),
            crmGetUsers(),
            crmGetContacts(),
            crmGetProducts(),
            crmGetSaleAreas()
        ]);

        // Store in cache
        pipelineCache = pipelines;
        leadCache = getUniqueLeads(leads);
        usersCache = users;
        contactsCache = contacts;
        productsCache = products;
        saleAreasCache = saleAreas;

        console.log("Loaded:", pipelines.length, "pipelines,", leadCache.length, "leads");

        // Update alert bar
        updateAlertBar();

        // Build pipeline columns
        let html = '<div class="card-body p-4"><div class="kanban-container">';

        for (const pipeline of pipelines) {
            const pipelineLeads = leadCache.filter(l => l.CRMPipelineId === pipeline.Id);
            const totalValue = pipelineLeads.reduce((sum, l) => sum + (l.ExpectedRevenue || 0), 0);

            // Count statuses
            const thirtyDaysAgo = new Date();
            thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
            const ninetyDaysAgo = new Date();
            ninetyDaysAgo.setDate(ninetyDaysAgo.getDate() - 90);

            let activeCount = 0, inactiveCount = 0, droppedCount = 0;
            pipelineLeads.forEach(lead => {
                const lastUpdated = new Date(lead.LastUpdated);
                if (lastUpdated < ninetyDaysAgo) droppedCount++;
                else if (lastUpdated < thirtyDaysAgo) inactiveCount++;
                else activeCount++;
            });

            html += `
                <div class="kanban-column bg-base-200 rounded-xl">
                    <div class="p-3 rounded-t-xl bg-primary text-primary-content">
                        <div class="flex items-center justify-between">
                            <h3 class="font-semibold text-sm">${pipeline.PipelineName}</h3>
                            <div class="dropdown dropdown-end">
                                <button tabindex="0" class="btn btn-ghost btn-xs btn-circle">
                                    <i class="fa-solid fa-ellipsis-vertical"></i>
                                </button>
                                <ul tabindex="0" class="dropdown-content menu bg-base-100 rounded-box z-50 w-40 p-2 shadow-lg text-base-content">
                                    <li><a onclick="editPipeline(${pipeline.Id})"><i class="fa-solid fa-pen"></i> แก้ไข</a></li>
                                    <li><a onclick="deletePipeline(${pipeline.Id})" class="text-error"><i class="fa-solid fa-trash"></i> ลบ</a></li>
                                </ul>
                            </div>
                        </div>
                        <p class="text-xs opacity-80">${AutoCommaLocal(totalValue)} THB | ${pipelineLeads.length} รายการ</p>
                        <div class="flex gap-1 mt-2">
                            <span class="badge badge-success badge-xs">${activeCount}</span>
                            <span class="badge badge-warning badge-xs">${inactiveCount}</span>
                            <span class="badge badge-error badge-xs">${droppedCount}</span>
                        </div>
                    </div>
                    <div class="p-2 space-y-2 flex-1 overflow-y-auto min-h-0" id="pipeline-${pipeline.Id}">
            `;

            // Render leads in this pipeline
            for (const lead of pipelineLeads) {
                html += await renderLeadCard(lead);
            }

            if (pipelineLeads.length === 0) {
                html += `
                    <div class="text-center py-6 text-base-content/50">
                        <i class="fa-solid fa-inbox text-2xl mb-2"></i>
                        <p class="text-xs">ไม่มีรายการ</p>
                    </div>
                `;
            }

            html += `
                    </div>
                    <div class="p-2 border-t border-base-300">
                        <button class="btn btn-ghost btn-sm w-full" onclick="createNewLead(${pipeline.Id})">
                            <i class="fa-solid fa-plus"></i> เพิ่มรายการ
                        </button>
                    </div>
                </div>
            `;
        }

        html += '</div></div>';
        cardViewContainer.innerHTML = html;

    } catch (error) {
        console.error('Error displaying leads:', error);
        cardViewContainer.innerHTML = '<div class="card-body"><div class="alert alert-error">เกิดข้อผิดพลาดในการโหลด Pipeline</div></div>';
    }
}

async function renderLeadCard(lead) {
    const user = getUserById(lead.MainUserId);
    const contact = getContactById(lead.MainCustomerId);
    const product = getProductById(lead.ProductId);
    const saleArea = getSaleAreaById(lead.SaleAreaId);
    const color = await getColor(lead.ProductId || 0);

    // Determine status badge
    const lastUpdated = new Date(lead.LastUpdated);
    const thirtyDaysAgo = new Date();
    thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
    const ninetyDaysAgo = new Date();
    ninetyDaysAgo.setDate(ninetyDaysAgo.getDate() - 90);

    let statusBadge = '';
    if (lastUpdated < ninetyDaysAgo) {
        statusBadge = '<span class="badge badge-error badge-xs">❌</span>';
    } else if (lastUpdated < thirtyDaysAgo) {
        statusBadge = '<span class="badge badge-warning badge-xs">⚠️</span>';
    } else {
        statusBadge = '<span class="badge badge-success badge-xs">✓</span>';
    }

    const leadLink = `crm-detail.html?leadid=${lead.Id}`;

    return `
        <div class="lead-card card bg-base-100 shadow-sm cursor-pointer hover:shadow-md transition-all" 
             style="border-left-color: ${color.color.code}" 
             onclick="window.location.href='${leadLink}'">
            <div class="card-body p-3">
                <div class="flex items-start justify-between">
                    <h4 class="font-medium text-sm line-clamp-1 flex-1">${statusBadge} ${lead.LeadName || 'ไม่ระบุชื่อ'}</h4>
                </div>
                <p class="text-xs text-base-content/60">Product: ${product?.Name || 'N/A'}</p>
                <p class="text-xs text-base-content/60">Sale Area: ${saleArea?.Name || 'N/A'}</p>
                <p class="text-xs">Expect: <span class="font-bold text-primary">${AutoCommaLocal(lead.ExpectedRevenue || 0)}</span> THB</p>
                <p class="text-xs">Achieved: <span class="font-bold text-success">${AutoCommaLocal(lead.AchivedRevenue || 0)}</span> THB</p>
                ${contact ? `<p class="text-xs text-base-content/60">ลูกค้า: ${contact.Name || '-'}</p>` : ''}
                <p class="text-xs text-base-content/60">Due: ${formatDateOnlyLocal(lead.Expected)}</p>
                ${user ? `
                    <div class="mt-2">
                        <span class="badge badge-xs truncate max-w-full" style="background-color: ${(await getColor(user.Id)).color.code}; color: ${(await getColor(user.Id)).textColor}">
                            ${user.FirstName || ''} ${user.LastName || ''}
                        </span>
                    </div>
                ` : ''}
            </div>
        </div>
    `;
}

// ============================================
// Alert Bar
// ============================================

function updateAlertBar() {
    const alertBar = document.getElementById('alertBar');
    if (!alertBar) return;

    const totalLeads = leadCache.length;
    const totalExpected = leadCache.reduce((sum, l) => sum + (l.ExpectedRevenue || 0), 0);
    const totalAchieved = leadCache.reduce((sum, l) => sum + (l.AchivedRevenue || 0), 0);
    const ratio = totalExpected > 0 ? Math.round((totalAchieved / totalExpected) * 100) : 0;

    alertBar.innerHTML = `
        <i class="fa-solid fa-chart-line"></i>
        <span>
            <strong>${totalLeads}</strong> รายการ | 
            คาดหวัง <strong>${AutoCommaLocal(totalExpected)}</strong> THB | 
            สำเร็จ <strong>${AutoCommaLocal(totalAchieved)}</strong> THB (${ratio}%)
        </span>
    `;
}

// ============================================
// View Toggle
// ============================================

function toggleViewMode(mode) {
    const cardView = document.getElementById('cardViewContainer');
    const tableView = document.getElementById('tableContainer');
    const vizView = document.getElementById('vizContainer');
    const cardBtn = document.getElementById('cardViewBtn');
    const tableBtn = document.getElementById('tableViewBtn');
    const vizBtn = document.getElementById('vizViewBtn');

    // Hide all views first
    cardView?.classList.add('hidden');
    tableView?.classList.add('hidden');
    vizView?.classList.add('hidden');
    
    // Remove active from all buttons
    cardBtn?.classList.remove('btn-active');
    tableBtn?.classList.remove('btn-active');
    vizBtn?.classList.remove('btn-active');

    if (mode === 'card') {
        cardView?.classList.remove('hidden');
        cardBtn?.classList.add('btn-active');
    } else if (mode === 'table') {
        tableView?.classList.remove('hidden');
        tableBtn?.classList.add('btn-active');
        displayTableView();
    } else if (mode === 'viz') {
        vizView?.classList.remove('hidden');
        vizBtn?.classList.add('btn-active');
        renderVisualization();
    }
}

// Table sorting state
let tableSortColumn = null;
let tableSortDirection = 'asc';

function displayTableView() {
    const tableContainer = document.getElementById('tableContainer');
    if (!tableContainer) return;

    // Sort leads if sort column is set
    let sortedLeads = [...leadCache];
    if (tableSortColumn) {
        sortedLeads.sort((a, b) => {
            let valA, valB;
            
            switch (tableSortColumn) {
                case 'name':
                    valA = (a.LeadName || '').toLowerCase();
                    valB = (b.LeadName || '').toLowerCase();
                    break;
                case 'pipeline':
                    valA = (getPipelineById(a.CRMPipelineId)?.PipelineName || '').toLowerCase();
                    valB = (getPipelineById(b.CRMPipelineId)?.PipelineName || '').toLowerCase();
                    break;
                case 'product':
                    valA = (getProductById(a.ProductId)?.Name || '').toLowerCase();
                    valB = (getProductById(b.ProductId)?.Name || '').toLowerCase();
                    break;
                case 'saleArea':
                    valA = (getSaleAreaById(a.SaleAreaId)?.Name || '').toLowerCase();
                    valB = (getSaleAreaById(b.SaleAreaId)?.Name || '').toLowerCase();
                    break;
                case 'expected':
                    valA = a.ExpectedRevenue || 0;
                    valB = b.ExpectedRevenue || 0;
                    break;
                case 'achieved':
                    valA = a.AchivedRevenue || 0;
                    valB = b.AchivedRevenue || 0;
                    break;
                case 'dueDate':
                    valA = new Date(a.Expected || 0).getTime();
                    valB = new Date(b.Expected || 0).getTime();
                    break;
                case 'user':
                    const userA = getUserById(a.MainUserId);
                    const userB = getUserById(b.MainUserId);
                    valA = userA ? (userA.FirstName + ' ' + userA.LastName).toLowerCase() : '';
                    valB = userB ? (userB.FirstName + ' ' + userB.LastName).toLowerCase() : '';
                    break;
                default:
                    valA = 0;
                    valB = 0;
            }
            
            if (valA < valB) return tableSortDirection === 'asc' ? -1 : 1;
            if (valA > valB) return tableSortDirection === 'asc' ? 1 : -1;
            return 0;
        });
    }

    // Helper function to render sort icon
    const sortIcon = (column) => {
        if (tableSortColumn !== column) {
            return '<i class="fa-solid fa-sort text-base-content/30 ml-1"></i>';
        }
        return tableSortDirection === 'asc' 
            ? '<i class="fa-solid fa-sort-up text-primary ml-1"></i>'
            : '<i class="fa-solid fa-sort-down text-primary ml-1"></i>';
    };

    // Build table HTML
    let html = `
        <div class="card-body p-4">
            <div class="overflow-x-auto">
                <table class="table table-zebra table-sm">
                    <thead>
                        <tr>
                            <th class="cursor-pointer hover:bg-base-200 select-none" onclick="sortTable('name')">Lead Name ${sortIcon('name')}</th>
                            <th class="cursor-pointer hover:bg-base-200 select-none" onclick="sortTable('pipeline')">Pipeline ${sortIcon('pipeline')}</th>
                            <th class="cursor-pointer hover:bg-base-200 select-none" onclick="sortTable('product')">Product ${sortIcon('product')}</th>
                            <th class="cursor-pointer hover:bg-base-200 select-none" onclick="sortTable('saleArea')">Sale Area ${sortIcon('saleArea')}</th>
                            <th class="cursor-pointer hover:bg-base-200 select-none" onclick="sortTable('expected')">Expected ${sortIcon('expected')}</th>
                            <th class="cursor-pointer hover:bg-base-200 select-none" onclick="sortTable('achieved')">Achieved ${sortIcon('achieved')}</th>
                            <th class="cursor-pointer hover:bg-base-200 select-none" onclick="sortTable('dueDate')">Due Date ${sortIcon('dueDate')}</th>
                            <th class="cursor-pointer hover:bg-base-200 select-none" onclick="sortTable('user')">User ${sortIcon('user')}</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
    `;

    for (const lead of sortedLeads) {
        const pipeline = getPipelineById(lead.CRMPipelineId);
        const product = getProductById(lead.ProductId);
        const saleArea = getSaleAreaById(lead.SaleAreaId);
        const user = getUserById(lead.MainUserId);

        html += `
            <tr>
                <td><a href="crm-detail.html?leadid=${lead.Id}" class="link link-primary">${lead.LeadName || '-'}</a></td>
                <td><span class="badge badge-primary badge-sm">${pipeline?.PipelineName || '-'}</span></td>
                <td>${product?.Name || '-'}</td>
                <td>${saleArea?.Name || '-'}</td>
                <td class="text-right font-medium">${AutoCommaLocal(lead.ExpectedRevenue || 0)}</td>
                <td class="text-right font-medium text-success">${AutoCommaLocal(lead.AchivedRevenue || 0)}</td>
                <td>${formatDateOnlyLocal(lead.Expected)}</td>
                <td>${user ? user.FirstName + ' ' + user.LastName : '-'}</td>
                <td>
                    <a href="crm-detail.html?leadid=${lead.Id}" class="btn btn-ghost btn-xs">
                        <i class="fa-solid fa-eye"></i>
                    </a>
                </td>
            </tr>
        `;
    }

    html += '</tbody></table></div></div>';
    tableContainer.innerHTML = html;
}

// Sort table by column
function sortTable(column) {
    if (tableSortColumn === column) {
        // Toggle direction if same column
        tableSortDirection = tableSortDirection === 'asc' ? 'desc' : 'asc';
    } else {
        // New column, default to ascending
        tableSortColumn = column;
        tableSortDirection = 'asc';
    }
    displayTableView();
}

// ============================================
// Visualization Functions
// ============================================

// Color palette for charts
const chartColors = [
    '#6366f1', '#8b5cf6', '#ec4899', '#f43f5e', '#f97316',
    '#eab308', '#22c55e', '#14b8a6', '#06b6d4', '#3b82f6',
    '#a855f7', '#d946ef', '#0ea5e9', '#10b981', '#84cc16'
];

function renderVisualization() {
    // Update summary stats
    updateVizSummaryStats();
    
    // Render all charts
    renderPipelineChart();
    renderProductChart();
    renderSaleAreaChart();
    renderUserChart();
    renderMonthlyTrendChart();
    renderLeadStatusList();
    renderTopProducts();
    renderTopUsers();
    renderTopContacts();
    renderExpectedVsAchievedChart();
    
    // Render target charts
    renderTargetOverview();
    renderTargetByProduct();
    renderTargetBySaleArea();
    renderTargetTimeline();
}

// Helper function to format large numbers with 2 decimal places
function formatRevenue(value) {
    return AutoCommaLocal(Math.round(value * 100) / 100);
}

// Helper function to get user avatar HTML
function getUserAvatarHtml(user, size = 'w-8 h-8') {
    if (user?.ProfilePic) {
        return `<img src="assets/profile/${user.ProfilePic}.jpg" class="rounded-full ${size} object-cover" onerror="this.parentElement.innerHTML='<div class=\\'bg-neutral text-neutral-content rounded-full ${size} flex items-center justify-center\\'><span class=\\'text-xs\\'>${(user.FirstName?.[0] || '') + (user.LastName?.[0] || '')}</span></div>'" />`;
    }
    const initials = ((user?.FirstName?.[0] || '') + (user?.LastName?.[0] || '')).toUpperCase();
    return `<div class="bg-neutral text-neutral-content rounded-full ${size} flex items-center justify-center"><span class="text-xs">${initials}</span></div>`;
}

function updateVizSummaryStats() {
    const totalLeads = leadCache.length;
    const totalExpected = leadCache.reduce((sum, l) => sum + (l.ExpectedRevenue || 0), 0);
    const totalAchieved = leadCache.reduce((sum, l) => sum + (l.AchivedRevenue || 0), 0);
    const achievementRate = totalExpected > 0 ? Math.round((totalAchieved / totalExpected) * 100) : 0;
    
    // Count leads this month
    const now = new Date();
    const leadsThisMonth = leadCache.filter(l => {
        const created = new Date(l.Created);
        return created.getMonth() === now.getMonth() && created.getFullYear() === now.getFullYear();
    }).length;
    
    // Calculate conversion rate (leads with Achieved > 0)
    const convertedLeads = leadCache.filter(l => (l.AchivedRevenue || 0) > 0).length;
    const conversionRate = totalLeads > 0 ? Math.round((convertedLeads / totalLeads) * 100) : 0;
    
    // Update DOM
    const el = (id) => document.getElementById(id);
    if (el('vizTotalLeads')) el('vizTotalLeads').textContent = totalLeads;
    if (el('vizLeadsThisMonth')) el('vizLeadsThisMonth').textContent = `+${leadsThisMonth}`;
    if (el('vizExpectedRevenue')) el('vizExpectedRevenue').textContent = `฿${formatRevenue(totalExpected)}`;
    if (el('vizAchievedRevenue')) el('vizAchievedRevenue').textContent = `฿${formatRevenue(totalAchieved)}`;
    if (el('vizAchievementRate')) el('vizAchievementRate').textContent = `${achievementRate}%`;
    if (el('vizConversionRate')) el('vizConversionRate').textContent = `${conversionRate}%`;
}

function renderPipelineChart() {
    const container = document.getElementById('vizPipelineChart');
    if (!container) return;
    
    // Group leads by pipeline using ID as key to prevent duplicates
    const pipelineData = {};
    leadCache.forEach(lead => {
        const pipelineId = lead.CRMPipelineId;
        const pipeline = getPipelineById(pipelineId);
        if (!pipelineData[pipelineId]) {
            pipelineData[pipelineId] = { name: pipeline?.PipelineName || 'Unknown', count: 0, order: pipeline?.Order || 999 };
        }
        pipelineData[pipelineId].count++;
    });
    
    // Sort by pipeline order
    const entries = Object.values(pipelineData).sort((a, b) => a.order - b.order);
    const total = entries.reduce((sum, p) => sum + p.count, 0);
    
    if (entries.length === 0) {
        container.innerHTML = '<div class="flex items-center justify-center h-full text-base-content/50">ไม่มีข้อมูล</div>';
        return;
    }
    
    // Build donut chart with interactive segments
    let html = '<div class="flex items-center justify-between h-full">';
    html += '<div class="relative w-48 h-48" id="pipelineDonut">';
    
    // Create SVG donut chart with hover effects
    let cumulativePercent = 0;
    html += `<svg viewBox="0 0 100 100" class="w-full h-full transform -rotate-90">`;
    
    entries.forEach((entry, i) => {
        const percent = (entry.count / total) * 100;
        const dashArray = `${percent} ${100 - percent}`;
        const dashOffset = -cumulativePercent;
        const color = chartColors[i % chartColors.length];
        html += `<circle class="donut-segment cursor-pointer transition-all duration-200 hover:opacity-80" 
                 cx="50" cy="50" r="40" fill="transparent" stroke="${color}" 
                 stroke-width="20" stroke-dasharray="${dashArray}" stroke-dashoffset="${dashOffset}"
                 data-name="${entry.name}" data-count="${entry.count}" data-percent="${Math.round(percent)}" />`;
        cumulativePercent += percent;
    });
    
    html += '</svg>';
    
    // Center text (will be updated on hover)
    html += '<div id="donutCenter" class="absolute inset-0 flex items-center justify-center flex-col pointer-events-none">';
    html += `<span class="text-2xl font-bold" id="donutCount">${total}</span>`;
    html += '<span class="text-xs text-base-content/60" id="donutLabel">Leads</span>';
    html += '</div></div>';
    
    // Legend with hover interaction
    html += '<div class="flex-1 ml-4 space-y-2 max-h-64 overflow-y-auto">';
    entries.forEach((entry, i) => {
        const percent = Math.round((entry.count / total) * 100);
        const color = chartColors[i % chartColors.length];
        html += `
            <div class="flex items-center gap-2 text-sm cursor-pointer hover:bg-base-200 rounded px-2 py-1 transition-colors legend-item"
                 data-index="${i}" data-name="${entry.name}" data-count="${entry.count}" data-percent="${percent}">
                <div class="w-3 h-3 rounded-full shrink-0" style="background-color: ${color}"></div>
                <span class="flex-1 truncate">${entry.name}</span>
                <span class="font-medium">${entry.count}</span>
                <span class="text-base-content/50">(${percent}%)</span>
            </div>
        `;
    });
    html += '</div></div>';
    
    container.innerHTML = html;
    
    // Add hover interactions
    const donutCount = document.getElementById('donutCount');
    const donutLabel = document.getElementById('donutLabel');
    const segments = container.querySelectorAll('.donut-segment');
    const legendItems = container.querySelectorAll('.legend-item');
    
    const showInfo = (name, count, percent) => {
        donutCount.textContent = count;
        donutLabel.textContent = name;
    };
    
    const resetInfo = () => {
        donutCount.textContent = total;
        donutLabel.textContent = 'Leads';
    };
    
    segments.forEach((seg, i) => {
        seg.addEventListener('mouseenter', () => {
            showInfo(seg.dataset.name, seg.dataset.count, seg.dataset.percent);
            seg.setAttribute('stroke-width', '24');
        });
        seg.addEventListener('mouseleave', () => {
            resetInfo();
            seg.setAttribute('stroke-width', '20');
        });
    });
    
    legendItems.forEach((item, i) => {
        item.addEventListener('mouseenter', () => {
            showInfo(item.dataset.name, item.dataset.count, item.dataset.percent);
            if (segments[i]) segments[i].setAttribute('stroke-width', '24');
        });
        item.addEventListener('mouseleave', () => {
            resetInfo();
            if (segments[i]) segments[i].setAttribute('stroke-width', '20');
        });
    });
}

function renderProductChart() {
    const container = document.getElementById('vizProductChart');
    if (!container) return;
    
    // Group revenue by product
    const productData = {};
    leadCache.forEach(lead => {
        const product = getProductById(lead.ProductId);
        const name = product?.Name || 'Unknown';
        if (!productData[name]) productData[name] = { expected: 0, achieved: 0 };
        productData[name].expected += lead.ExpectedRevenue || 0;
        productData[name].achieved += lead.AchivedRevenue || 0;
    });
    
    // Sort by achieved revenue and take top 8
    const sorted = Object.entries(productData)
        .sort((a, b) => b[1].achieved - a[1].achieved)
        .slice(0, 8);
    
    if (sorted.length === 0) {
        container.innerHTML = '<div class="flex items-center justify-center h-full text-base-content/50">ไม่มีข้อมูล</div>';
        return;
    }
    
    const maxValue = Math.max(...sorted.map(([, d]) => Math.max(d.expected, d.achieved)));
    
    let html = '<div class="flex flex-col h-full"><div class="space-y-3 flex-1 overflow-y-auto">';
    sorted.forEach(([name, data], i) => {
        const expectedPercent = maxValue > 0 ? (data.expected / maxValue) * 100 : 0;
        const achievedPercent = maxValue > 0 ? (data.achieved / maxValue) * 100 : 0;
        html += `
            <div>
                <div class="flex justify-between text-sm mb-1">
                    <span class="truncate max-w-[200px]">${name}</span>
                    <span class="font-medium text-success">฿${AutoCommaLocal(data.achieved)}</span>
                </div>
                <div class="h-4 bg-base-200 rounded-full overflow-hidden relative">
                    <div class="h-full bg-base-300 rounded-full absolute top-0 left-0" style="width: ${expectedPercent}%"></div>
                    <div class="h-full bg-success rounded-full absolute top-0 left-0" style="width: ${achievedPercent}%"></div>
                </div>
            </div>
        `;
    });
    html += '</div>';
    html += '<div class="flex gap-4 pt-3 text-xs justify-center border-t border-base-200 mt-3">';
    html += '<span class="flex items-center gap-1"><span class="w-3 h-3 bg-base-300 rounded"></span> Expected</span>';
    html += '<span class="flex items-center gap-1"><span class="w-3 h-3 bg-success rounded"></span> Achieved</span>';
    html += '</div></div>';
    
    container.innerHTML = html;
}

function renderSaleAreaChart() {
    const container = document.getElementById('vizSaleAreaChart');
    if (!container) return;
    
    // Group revenue by sale area
    const areaData = {};
    leadCache.forEach(lead => {
        const area = getSaleAreaById(lead.SaleAreaId);
        const name = area?.Name || 'Unknown';
        if (!areaData[name]) areaData[name] = { expected: 0, achieved: 0, count: 0 };
        areaData[name].expected += lead.ExpectedRevenue || 0;
        areaData[name].achieved += lead.AchivedRevenue || 0;
        areaData[name].count++;
    });
    
    // Sort by achieved revenue
    const sorted = Object.entries(areaData)
        .sort((a, b) => b[1].achieved - a[1].achieved)
        .slice(0, 8);
    
    if (sorted.length === 0) {
        container.innerHTML = '<div class="flex items-center justify-center h-full text-base-content/50">ไม่มีข้อมูล</div>';
        return;
    }
    
    const maxValue = Math.max(...sorted.map(([, d]) => d.achieved));
    
    let html = '<div class="space-y-3 h-full overflow-y-auto">';
    sorted.forEach(([name, data], i) => {
        const percent = maxValue > 0 ? (data.achieved / maxValue) * 100 : 0;
        html += `
            <div class="flex items-center gap-3">
                <span class="text-sm w-32 truncate shrink-0">${name}</span>
                <div class="flex-1 h-6 bg-base-200 rounded-full overflow-hidden">
                    <div class="h-full rounded-full flex items-center px-2 transition-all duration-500" 
                         style="width: ${Math.max(percent, 5)}%; background-color: ${chartColors[i % chartColors.length]}">
                        <span class="text-xs text-white font-medium ${percent < 20 ? 'hidden' : ''}">${data.count} leads</span>
                    </div>
                </div>
                <span class="text-sm font-medium w-28 text-right">฿${AutoCommaLocal(data.achieved)}</span>
            </div>
        `;
    });
    html += '</div>';
    
    container.innerHTML = html;
}

function renderUserChart() {
    const container = document.getElementById('vizUserChart');
    if (!container) return;
    
    // Group revenue by user using ID as key
    const userData = {};
    leadCache.forEach(lead => {
        const userId = lead.MainUserId;
        const user = getUserById(userId);
        if (!userData[userId]) {
            userData[userId] = { 
                user: user,
                name: user ? `${user.FirstName} ${user.LastName}` : 'Unknown', 
                expected: 0, 
                achieved: 0, 
                count: 0 
            };
        }
        userData[userId].expected += lead.ExpectedRevenue || 0;
        userData[userId].achieved += lead.AchivedRevenue || 0;
        userData[userId].count++;
    });
    
    // Sort by achieved revenue
    const sorted = Object.values(userData)
        .sort((a, b) => b.achieved - a.achieved)
        .slice(0, 8);
    
    if (sorted.length === 0) {
        container.innerHTML = '<div class="flex items-center justify-center h-full text-base-content/50">ไม่มีข้อมูล</div>';
        return;
    }
    
    const maxValue = Math.max(...sorted.map(d => d.achieved));
    
    let html = '<div class="space-y-3 h-full overflow-y-auto">';
    sorted.forEach((data, i) => {
        const percent = maxValue > 0 ? (data.achieved / maxValue) * 100 : 0;
        html += `
            <div class="flex items-center gap-3">
                <div class="avatar shrink-0">
                    ${getUserAvatarHtml(data.user, 'w-8 h-8')}
                </div>
                <span class="text-sm w-24 truncate shrink-0">${data.name}</span>
                <div class="flex-1 h-5 bg-base-200 rounded-full overflow-hidden">
                    <div class="h-full bg-success rounded-full" style="width: ${Math.max(percent, 3)}%"></div>
                </div>
                <span class="text-sm font-medium w-28 text-right">฿${formatRevenue(data.achieved)}</span>
            </div>
        `;
    });
    html += '</div>';
    
    container.innerHTML = html;
}

function renderMonthlyTrendChart() {
    const container = document.getElementById('vizMonthlyTrendChart');
    if (!container) return;
    
    const now = new Date();
    const currentYear = now.getFullYear();
    const monthNames = ['ม.ค.', 'ก.พ.', 'มี.ค.', 'เม.ย.', 'พ.ค.', 'มิ.ย.', 'ก.ค.', 'ส.ค.', 'ก.ย.', 'ต.ค.', 'พ.ย.', 'ธ.ค.'];
    const monthFullNames = ['มกราคม', 'กุมภาพันธ์', 'มีนาคม', 'เมษายน', 'พฤษภาคม', 'มิถุนายน', 'กรกฎาคม', 'สิงหาคม', 'กันยายน', 'ตุลาคม', 'พฤศจิกายน', 'ธันวาคม'];
    
    // Initialize data for current year and past 2 years
    const yearlyData = {};
    for (let year = currentYear - 2; year <= currentYear; year++) {
        yearlyData[year] = {};
        for (let month = 1; month <= 12; month++) {
            yearlyData[year][month] = { expected: 0, achieved: 0 };
        }
    }
    
    // Fill with data
    leadCache.forEach(lead => {
        const created = new Date(lead.Created || lead.Expected);
        const year = created.getFullYear();
        const month = created.getMonth() + 1;
        if (yearlyData[year] && yearlyData[year][month]) {
            yearlyData[year][month].expected += lead.ExpectedRevenue || 0;
            yearlyData[year][month].achieved += lead.AchivedRevenue || 0;
        }
    });
    
    // Find max value across all years for scaling
    let maxValue = 1;
    Object.values(yearlyData).forEach(yearData => {
        Object.values(yearData).forEach(monthData => {
            maxValue = Math.max(maxValue, monthData.achieved, monthData.expected);
        });
    });
    
    // SVG dimensions
    const width = 800;
    const height = 250;
    const padding = { top: 20, right: 30, bottom: 40, left: 60 };
    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;
    
    const getX = (month) => padding.left + ((month - 1) / 11) * chartWidth;
    const getY = (val) => padding.top + chartHeight - (val / maxValue) * chartHeight;
    
    // Year colors
    const yearColors = {
        [currentYear]: '#22c55e',      // green - current year
        [currentYear - 1]: '#3b82f6',  // blue - last year
        [currentYear - 2]: '#9ca3af',  // gray - 2 years ago
    };
    
    let html = '<div class="h-full flex flex-col relative">';
    
    // Tooltip element
    html += '<div id="chartTooltip" class="absolute hidden bg-base-100 shadow-xl rounded-lg p-3 z-50 border border-base-300 pointer-events-none" style="min-width: 150px;"></div>';
    
    html += `<svg viewBox="0 0 ${width} ${height}" class="flex-1 w-full" id="monthlyTrendSvg">`;
    
    // Grid lines
    for (let i = 0; i <= 4; i++) {
        const y = padding.top + (chartHeight / 4) * i;
        const value = maxValue * (1 - i / 4);
        html += `<line x1="${padding.left}" y1="${y}" x2="${width - padding.right}" y2="${y}" stroke="#e5e7eb" stroke-dasharray="4"/>`;
        html += `<text x="${padding.left - 10}" y="${y + 4}" text-anchor="end" class="fill-base-content/50" font-size="10">฿${formatRevenue(value / 1000000)}M</text>`;
    }
    
    // X-axis labels
    for (let month = 1; month <= 12; month++) {
        const x = getX(month);
        html += `<text x="${x}" y="${height - 10}" text-anchor="middle" class="fill-base-content/50" font-size="11">${monthNames[month - 1]}</text>`;
    }
    
    // Draw lines for each year
    Object.keys(yearlyData).sort().forEach(year => {
        const data = yearlyData[year];
        const color = yearColors[year];
        const opacity = year == currentYear ? 1 : (year == currentYear - 1 ? 0.7 : 0.4);
        const strokeWidth = year == currentYear ? 3 : 2;
        
        // Create path
        let path = '';
        for (let month = 1; month <= 12; month++) {
            const x = getX(month);
            const y = getY(data[month].achieved);
            if (month === 1) {
                path = `M ${x} ${y}`;
            } else {
                path += ` L ${x} ${y}`;
            }
        }
        
        html += `<path d="${path}" fill="none" stroke="${color}" stroke-width="${strokeWidth}" stroke-opacity="${opacity}" stroke-linecap="round" stroke-linejoin="round"/>`;
        
        // Add interactive dots for all years
        for (let month = 1; month <= 12; month++) {
            const x = getX(month);
            const y = getY(data[month].achieved);
            const value = data[month].achieved;
            const dotSize = year == currentYear ? 6 : 4;
            html += `<circle class="chart-dot cursor-pointer" cx="${x}" cy="${y}" r="${dotSize}" fill="${color}" 
                     fill-opacity="${opacity}"
                     data-year="${year}" data-month="${month}" data-monthname="${monthFullNames[month-1]}" 
                     data-value="${value}" data-color="${color}"/>`;
        }
    });
    
    html += '</svg>';
    
    // Legend
    html += '<div class="flex gap-6 justify-center pt-3 border-t border-base-200 text-sm">';
    html += `<span class="flex items-center gap-2"><span class="w-6 h-1 rounded" style="background: ${yearColors[currentYear]}"></span> ${currentYear}</span>`;
    html += `<span class="flex items-center gap-2"><span class="w-6 h-1 rounded opacity-70" style="background: ${yearColors[currentYear - 1]}"></span> ${currentYear - 1}</span>`;
    html += `<span class="flex items-center gap-2"><span class="w-6 h-1 rounded opacity-40" style="background: ${yearColors[currentYear - 2]}"></span> ${currentYear - 2}</span>`;
    html += '</div></div>';
    
    container.innerHTML = html;
    
    // Add interactive tooltip
    const tooltip = document.getElementById('chartTooltip');
    const svg = document.getElementById('monthlyTrendSvg');
    const dots = container.querySelectorAll('.chart-dot');
    
    dots.forEach(dot => {
        dot.addEventListener('mouseenter', (e) => {
            const year = dot.dataset.year;
            const monthName = dot.dataset.monthname;
            const value = parseFloat(dot.dataset.value);
            const color = dot.dataset.color;
            
            tooltip.innerHTML = `
                <div class="text-xs text-base-content/60 mb-1">${monthName} ${year}</div>
                <div class="text-lg font-bold" style="color: ${color}">฿${formatRevenue(value)}</div>
            `;
            tooltip.classList.remove('hidden');
            
            // Position tooltip
            const rect = container.getBoundingClientRect();
            const dotRect = dot.getBoundingClientRect();
            tooltip.style.left = `${dotRect.left - rect.left - 50}px`;
            tooltip.style.top = `${dotRect.top - rect.top - 60}px`;
            
            // Enlarge dot
            dot.setAttribute('r', parseInt(dot.getAttribute('r')) + 3);
        });
        
        dot.addEventListener('mouseleave', () => {
            tooltip.classList.add('hidden');
            const year = dot.dataset.year;
            dot.setAttribute('r', year == currentYear ? 6 : 4);
        });
    });
}

function renderLeadStatusList() {
    const container = document.getElementById('vizLeadStatusList');
    if (!container) return;
    
    // Count leads per pipeline
    const pipelineCount = {};
    leadCache.forEach(lead => {
        const pipeline = getPipelineById(lead.CRMPipelineId);
        const name = pipeline?.PipelineName || 'Unknown';
        if (!pipelineCount[name]) pipelineCount[name] = 0;
        pipelineCount[name]++;
    });
    
    const total = leadCache.length;
    const sorted = Object.entries(pipelineCount).sort((a, b) => b[1] - a[1]);
    
    if (sorted.length === 0) {
        container.innerHTML = '<div class="flex items-center justify-center h-48 text-base-content/50">ไม่มีข้อมูล</div>';
        return;
    }
    
    let html = '';
    sorted.forEach(([name, count], i) => {
        const percent = Math.round((count / total) * 100);
        html += `
            <div class="flex items-center gap-3">
                <div class="w-2 h-2 rounded-full" style="background-color: ${chartColors[i % chartColors.length]}"></div>
                <span class="flex-1 text-sm truncate">${name}</span>
                <span class="text-sm font-medium">${count}</span>
                <div class="w-16 h-2 bg-base-200 rounded-full overflow-hidden">
                    <div class="h-full rounded-full" style="width: ${percent}%; background-color: ${chartColors[i % chartColors.length]}"></div>
                </div>
                <span class="text-xs text-base-content/50 w-10 text-right">${percent}%</span>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

function renderTopProducts() {
    const container = document.getElementById('vizTopProducts');
    if (!container) return;
    
    // Group by product
    const productData = {};
    leadCache.forEach(lead => {
        const product = getProductById(lead.ProductId);
        const name = product?.Name || 'Unknown';
        if (!productData[name]) productData[name] = { achieved: 0, count: 0 };
        productData[name].achieved += lead.AchivedRevenue || 0;
        productData[name].count++;
    });
    
    const sorted = Object.entries(productData)
        .sort((a, b) => b[1].achieved - a[1].achieved)
        .slice(0, 5);
    
    if (sorted.length === 0) {
        container.innerHTML = '<div class="flex items-center justify-center h-48 text-base-content/50">ไม่มีข้อมูล</div>';
        return;
    }
    
    let html = '';
    sorted.forEach(([name, data], i) => {
        const medals = ['🥇', '🥈', '🥉', '4️⃣', '5️⃣'];
        html += `
            <div class="flex items-center gap-3 p-2 rounded-lg hover:bg-base-200 transition-colors">
                <span class="text-lg">${medals[i]}</span>
                <div class="flex-1 min-w-0">
                    <p class="text-sm font-medium truncate">${name}</p>
                    <p class="text-xs text-base-content/50">${data.count} leads</p>
                </div>
                <span class="text-sm font-bold text-success">฿${AutoCommaLocal(data.achieved)}</span>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

function renderTopUsers() {
    const container = document.getElementById('vizTopUsers');
    if (!container) return;
    
    // Group by user using ID as key
    const userData = {};
    leadCache.forEach(lead => {
        const userId = lead.MainUserId;
        const user = getUserById(userId);
        if (!userData[userId]) {
            userData[userId] = { 
                user: user,
                name: user ? `${user.FirstName} ${user.LastName}` : 'Unknown', 
                achieved: 0, 
                count: 0 
            };
        }
        userData[userId].achieved += lead.AchivedRevenue || 0;
        userData[userId].count++;
    });
    
    const sorted = Object.values(userData)
        .sort((a, b) => b.achieved - a.achieved)
        .slice(0, 5);
    
    if (sorted.length === 0) {
        container.innerHTML = '<div class="flex items-center justify-center h-48 text-base-content/50">ไม่มีข้อมูล</div>';
        return;
    }
    
    let html = '';
    sorted.forEach((data, i) => {
        const medals = ['🥇', '🥈', '🥉', '4️⃣', '5️⃣'];
        html += `
            <div class="flex items-center gap-3 p-2 rounded-lg hover:bg-base-200 transition-colors">
                <span class="text-lg">${medals[i]}</span>
                <div class="avatar">
                    ${getUserAvatarHtml(data.user, 'w-8 h-8')}
                </div>
                <div class="flex-1 min-w-0">
                    <p class="text-sm font-medium truncate">${data.name}</p>
                    <p class="text-xs text-base-content/50">${data.count} leads</p>
                </div>
                <span class="text-sm font-bold text-success">฿${formatRevenue(data.achieved)}</span>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

function renderTopContacts() {
    const container = document.getElementById('vizTopContacts');
    if (!container) return;
    
    // Group leads by MainCustomer (Contact)
    const contactData = {};
    leadCache.forEach(lead => {
        const contactId = lead.MainCustomerId;
        if (!contactId) return;
        
        // Get contact info from cache or from lead's MainCustomer object
        const contact = getContactById(contactId) || lead.MainCustomer;
        
        if (!contactData[contactId]) {
            contactData[contactId] = { 
                contactId: contactId,
                name: contact?.Name || 'Unknown',
                company: contact?.Company || '',
                achieved: 0, 
                expected: 0,
                count: 0 
            };
        }
        contactData[contactId].achieved += lead.AchivedRevenue || 0;
        contactData[contactId].expected += lead.ExpectedRevenue || 0;
        contactData[contactId].count++;
    });
    
    const sorted = Object.values(contactData)
        .sort((a, b) => b.achieved - a.achieved)
        .slice(0, 5);
    
    if (sorted.length === 0) {
        container.innerHTML = '<div class="flex items-center justify-center h-48 text-base-content/50">ไม่มีข้อมูล</div>';
        return;
    }
    
    let html = '';
    sorted.forEach((data, i) => {
        const medals = ['🥇', '🥈', '🥉', '4️⃣', '5️⃣'];
        // Get initials for avatar from Name
        const name = data.name || 'Unknown';
        const nameParts = name.split(' ').filter(p => p);
        const initials = nameParts.length >= 2 
            ? (nameParts[0][0] + nameParts[nameParts.length - 1][0]).toUpperCase()
            : (name.substring(0, 2)).toUpperCase();
        
        html += `
            <div class="flex items-center gap-3 p-2 rounded-lg hover:bg-base-200 transition-colors cursor-pointer" onclick="window.location.href='contact-detail.html?id=${data.contactId}'">
                <span class="text-lg">${medals[i]}</span>
                <div class="avatar">
                    <div class="bg-accent text-accent-content rounded-full w-8 h-8 flex items-center justify-center">
                        <span class="text-xs font-bold">${initials}</span>
                    </div>
                </div>
                <div class="flex-1 min-w-0">
                    <p class="text-sm font-medium truncate">${name}</p>
                    <p class="text-xs text-base-content/50 truncate">${data.company || data.count + ' leads'}</p>
                </div>
                <span class="text-sm font-bold text-success">฿${formatRevenue(data.achieved)}</span>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

function renderExpectedVsAchievedChart() {
    const container = document.getElementById('vizExpectedVsAchievedChart');
    if (!container) return;
    
    // Group by pipeline using ID as key
    const pipelineData = {};
    leadCache.forEach(lead => {
        const pipelineId = lead.CRMPipelineId;
        const pipeline = getPipelineById(pipelineId);
        if (!pipelineData[pipelineId]) {
            pipelineData[pipelineId] = { 
                name: pipeline?.PipelineName || 'Unknown', 
                order: pipeline?.Order ?? 999,
                expected: 0, 
                achieved: 0 
            };
        }
        pipelineData[pipelineId].expected += lead.ExpectedRevenue || 0;
        pipelineData[pipelineId].achieved += lead.AchivedRevenue || 0;
    });

    // Add target totals per pipeline (from targetsCache)
    let totalTarget = 0;
    if (targetsCache && targetsCache.length > 0) {
        totalTarget = targetsCache.reduce((s, t) => s + (t.TargetValue || 0), 0);
    }
    
    // Sort by pipeline Order (ascending) - lower order first
    const sorted = Object.values(pipelineData).sort((a, b) => {
        const orderA = a.order ?? 999;
        const orderB = b.order ?? 999;
        return orderA - orderB;
    });
    
    if (sorted.length === 0) {
        container.innerHTML = '<div class="flex items-center justify-center h-full text-base-content/50">ไม่มีข้อมูล</div>';
        return;
    }

    // Calculate totals
    const totalExpected = sorted.reduce((s, d) => s + d.expected, 0);
    const totalAchieved = sorted.reduce((s, d) => s + d.achieved, 0);
    const targetPctAchieved = totalTarget > 0 ? Math.round((totalAchieved / totalTarget) * 100) : 0;
    const targetPctExpected = totalTarget > 0 ? Math.round((totalExpected / totalTarget) * 100) : 0;
    const achievedOfExpected = totalExpected > 0 ? Math.round((totalAchieved / totalExpected) * 100) : 0;
    
    // Summary row at top
    let html = '';
    if (totalTarget > 0) {
        const gap = totalTarget - totalAchieved;
        let overallColor = 'text-error';
        if (targetPctAchieved >= 100) overallColor = 'text-success';
        else if (targetPctAchieved >= 75) overallColor = 'text-info';
        else if (targetPctAchieved >= 50) overallColor = 'text-warning';

        html += `<div class="grid grid-cols-3 gap-3 mb-4">
            <div class="stat bg-base-200 rounded-box p-3">
                <div class="stat-title text-xs">🎯 Target</div>
                <div class="stat-value text-base text-primary">฿${formatRevenue(totalTarget)}</div>
            </div>
            <div class="stat bg-base-200 rounded-box p-3">
                <div class="stat-title text-xs">📊 Expected</div>
                <div class="stat-value text-base text-info">฿${formatRevenue(totalExpected)}</div>
                <div class="stat-desc">${targetPctExpected}% ของ Target</div>
            </div>
            <div class="stat bg-base-200 rounded-box p-3">
                <div class="stat-title text-xs">✅ Achieved</div>
                <div class="stat-value text-base text-success">฿${formatRevenue(totalAchieved)}</div>
                <div class="stat-desc ${overallColor} font-bold">${targetPctAchieved}% ของ Target · ${achievedOfExpected}% ของ Expected</div>
            </div>
        </div>`;

        // Overall progress bar: Target → Expected → Achieved
        const maxBar = totalTarget;
        const expBarPct = maxBar > 0 ? Math.min((totalExpected / maxBar) * 100, 100) : 0;
        const achBarPct = maxBar > 0 ? Math.min((totalAchieved / maxBar) * 100, 100) : 0;
        html += `<div class="mb-4">
            <div class="h-6 bg-base-200 rounded-full overflow-hidden relative">
                <div class="h-full rounded-full absolute top-0 left-0 bg-primary/20" style="width: 100%"></div>
                <div class="h-full bg-info/50 rounded-full absolute top-0 left-0" style="width: ${expBarPct}%"></div>
                <div class="h-full bg-success rounded-full absolute top-0 left-0" style="width: ${achBarPct}%"></div>
                <div class="absolute inset-0 flex items-center justify-center text-xs font-bold">
                    Achieved ${targetPctAchieved}% · Expected ${targetPctExpected}% · Target 100%
                </div>
            </div>
            <div class="flex gap-4 mt-2 text-xs justify-center">
                <span class="flex items-center gap-1"><span class="w-3 h-3 bg-primary/20 rounded"></span> Target</span>
                <span class="flex items-center gap-1"><span class="w-3 h-3 bg-info/50 rounded"></span> Expected</span>
                <span class="flex items-center gap-1"><span class="w-3 h-3 bg-success rounded"></span> Achieved</span>
            </div>
        </div>`;
    }

    const maxValue = Math.max(...sorted.map(d => Math.max(d.expected, d.achieved)));
    
    html += '<div class="flex h-full gap-4">';
    
    // Chart area
    html += '<div class="flex-1 flex items-end gap-2 pb-6">';
    sorted.forEach((data, i) => {
        const expectedHeight = maxValue > 0 ? (data.expected / maxValue) * 100 : 0;
        const achievedHeight = maxValue > 0 ? (data.achieved / maxValue) * 100 : 0;
        const expPct = totalExpected > 0 ? Math.round((data.expected / totalExpected) * 100) : 0;
        const achPct = totalAchieved > 0 ? Math.round((data.achieved / totalAchieved) * 100) : 0;
        html += `
            <div class="flex-1 flex flex-col items-center gap-1 min-w-0">
                <div class="flex gap-1 items-end h-48 w-full justify-center">
                    <div class="w-5 bg-info/50 rounded-t transition-all duration-500 relative group" style="height: ${Math.max(expectedHeight, 2)}%">
                        <div class="absolute -top-8 left-1/2 -translate-x-1/2 bg-base-300 text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 whitespace-nowrap z-10">
                            ฿${formatRevenue(data.expected)} (${expPct}%)
                        </div>
                    </div>
                    <div class="w-5 bg-success rounded-t transition-all duration-500 relative group" style="height: ${Math.max(achievedHeight, 2)}%">
                        <div class="absolute -top-8 left-1/2 -translate-x-1/2 bg-base-300 text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 whitespace-nowrap z-10">
                            ฿${formatRevenue(data.achieved)} (${achPct}%)
                        </div>
                    </div>
                </div>
                <span class="text-xs text-center truncate w-full px-1" title="${data.name}">${data.name}</span>
            </div>
        `;
    });
    html += '</div>';
    
    // Legend
    html += `
        <div class="flex flex-col justify-center gap-3 pr-4">
            <div class="flex items-center gap-2">
                <div class="w-4 h-4 bg-info/50 rounded"></div>
                <span class="text-sm">Expected</span>
            </div>
            <div class="flex items-center gap-2">
                <div class="w-4 h-4 bg-success rounded"></div>
                <span class="text-sm">Achieved</span>
            </div>
        </div>
    `;
    
    html += '</div>';
    
    container.innerHTML = html;
}

// ============================================
// Target Visualization Functions
// ============================================

function renderTargetOverview() {
    const container = document.getElementById('vizTargetOverview');
    if (!container) return;

    if (!targetsCache || targetsCache.length === 0) {
        container.innerHTML = '<div class="flex items-center justify-center h-48 text-base-content/50"><i class="fa-solid fa-bullseye text-3xl mr-3 opacity-30"></i>ไม่มีข้อมูล Target</div>';
        return;
    }

    const targets = targetsCache;

    // Summary stats
    const totalTargetValue = targets.reduce((s, t) => s + (t.TargetValue || 0), 0);
    const totalAchieved = targets.reduce((s, t) => s + t.Leads.reduce((ls, l) => ls + (l.AchivedRevenue || 0), 0), 0);
    const totalExpected = targets.reduce((s, t) => s + t.Leads.reduce((ls, l) => ls + (l.ExpectedRevenue || 0), 0), 0);
    const totalLeads = targets.reduce((s, t) => s + t.Leads.length, 0);
    const overallPercent = totalTargetValue > 0 ? Math.round((totalAchieved / totalTargetValue) * 100) : 0;
    const expectedPercent = totalTargetValue > 0 ? Math.round((totalExpected / totalTargetValue) * 100) : 0;
    const gap = totalTargetValue - totalAchieved;

    // Overall color
    let overallColor = 'text-error';
    if (overallPercent >= 100) overallColor = 'text-success';
    else if (overallPercent >= 75) overallColor = 'text-info';
    else if (overallPercent >= 50) overallColor = 'text-warning';

    let html = '';

    // Summary stat cards
    html += `<div class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
        <div class="stat bg-base-200 rounded-box p-3">
            <div class="stat-title text-xs">เป้าหมายรวม</div>
            <div class="stat-value text-lg text-primary">฿${formatRevenue(totalTargetValue)}</div>
            <div class="stat-desc">${targets.length} เป้าหมาย</div>
        </div>
        <div class="stat bg-base-200 rounded-box p-3">
            <div class="stat-title text-xs">สำเร็จแล้ว</div>
            <div class="stat-value text-lg text-success">฿${formatRevenue(totalAchieved)}</div>
            <div class="stat-desc ${overallColor} font-bold">${overallPercent}% ของเป้า</div>
        </div>
        <div class="stat bg-base-200 rounded-box p-3">
            <div class="stat-title text-xs">คาดหวัง</div>
            <div class="stat-value text-lg text-info">฿${formatRevenue(totalExpected)}</div>
            <div class="stat-desc">${expectedPercent}% ของเป้า</div>
        </div>
        <div class="stat bg-base-200 rounded-box p-3">
            <div class="stat-title text-xs">ส่วนต่าง</div>
            <div class="stat-value text-lg ${gap > 0 ? 'text-error' : 'text-success'}">฿${formatRevenue(Math.abs(gap))}</div>
            <div class="stat-desc">${gap > 0 ? 'ยังขาดอยู่' : 'เกินเป้า! 🎉'}</div>
        </div>
    </div>`;

    container.innerHTML = html;
}

function renderTargetByProduct() {
    const container = document.getElementById('vizTargetByProduct');
    if (!container) return;

    if (!targetsCache || targetsCache.length === 0) {
        container.innerHTML = '<div class="flex items-center justify-center h-full text-base-content/50">ไม่มีข้อมูล Target</div>';
        return;
    }

    // Group targets by product
    const productData = {};
    targetsCache.forEach(target => {
        const name = target.Product?.Name || 'Unknown';
        if (!productData[name]) productData[name] = { target: 0, achieved: 0, expected: 0, color: target.Color?.color?.code || '#6366f1' };
        productData[name].target += target.TargetValue || 0;
        productData[name].achieved += target.Leads.reduce((s, l) => s + (l.AchivedRevenue || 0), 0);
        productData[name].expected += target.Leads.reduce((s, l) => s + (l.ExpectedRevenue || 0), 0);
    });

    const sorted = Object.entries(productData).sort((a, b) => b[1].target - a[1].target);

    if (sorted.length === 0) {
        container.innerHTML = '<div class="flex items-center justify-center h-full text-base-content/50">ไม่มีข้อมูล</div>';
        return;
    }

    let html = '<div class="flex flex-col h-full"><div class="space-y-4 flex-1 overflow-y-auto">';
    sorted.forEach(([name, data]) => {
        // % relative to this item's own target
        const achieveRatio = data.target > 0 ? Math.round((data.achieved / data.target) * 100) : 0;
        const expectedRatio = data.target > 0 ? Math.round((data.expected / data.target) * 100) : 0;
        // Bar widths: target = 100%, others proportional to target
        const achievedBarW = data.target > 0 ? Math.min((data.achieved / data.target) * 100, 100) : 0;
        const expectedBarW = data.target > 0 ? Math.min((data.expected / data.target) * 100, 100) : 0;

        html += `
            <div>
                <div class="flex justify-between text-sm mb-1">
                    <span class="truncate max-w-[180px] font-medium">${name}</span>
                    <span class="text-xs ${achieveRatio >= 100 ? 'text-success' : achieveRatio >= 50 ? 'text-warning' : 'text-error'} font-bold">${achieveRatio}%</span>
                </div>
                <div class="h-5 bg-base-200 rounded-full overflow-hidden relative">
                    <div class="h-full rounded-full absolute top-0 left-0 z-[1]" style="width: 100%; background-color: ${data.color}; opacity: 0.15;"></div>
                    <div class="h-full bg-info/50 rounded-full absolute top-0 left-0 z-[2]" style="width: ${expectedBarW}%"></div>
                    <div class="h-full bg-success rounded-full absolute top-0 left-0 z-[3]" style="width: ${achievedBarW}%"></div>
                </div>
                <div class="flex justify-between text-[10px] text-base-content/50 mt-0.5">
                    <span>Achieved ฿${AutoCommaLocal(data.achieved)} (${achieveRatio}%)</span>
                    <span>Expected ฿${AutoCommaLocal(data.expected)} (${expectedRatio}%)</span>
                    <span>Target ฿${AutoCommaLocal(data.target)}</span>
                </div>
            </div>`;
    });
    html += '</div>';
    html += '<div class="flex gap-4 pt-3 text-xs justify-center border-t border-base-200 mt-3">';
    html += '<span class="flex items-center gap-1"><span class="w-3 h-3 bg-base-300 rounded opacity-30"></span> Target</span>';
    html += '<span class="flex items-center gap-1"><span class="w-3 h-3 bg-info/60 rounded"></span> Expected</span>';
    html += '<span class="flex items-center gap-1"><span class="w-3 h-3 bg-success rounded"></span> Achieved</span>';
    html += '</div></div>';

    container.innerHTML = html;
}

function renderTargetBySaleArea() {
    const container = document.getElementById('vizTargetBySaleArea');
    if (!container) return;

    if (!targetsCache || targetsCache.length === 0) {
        container.innerHTML = '<div class="flex items-center justify-center h-full text-base-content/50">ไม่มีข้อมูล Target</div>';
        return;
    }

    // Group targets by sale area
    const areaData = {};
    targetsCache.forEach(target => {
        const name = target.SaleArea?.Name || 'Unknown';
        if (!areaData[name]) areaData[name] = { target: 0, achieved: 0, expected: 0 };
        areaData[name].target += target.TargetValue || 0;
        areaData[name].achieved += target.Leads.reduce((s, l) => s + (l.AchivedRevenue || 0), 0);
        areaData[name].expected += target.Leads.reduce((s, l) => s + (l.ExpectedRevenue || 0), 0);
    });

    const sorted = Object.entries(areaData).sort((a, b) => b[1].target - a[1].target);

    if (sorted.length === 0) {
        container.innerHTML = '<div class="flex items-center justify-center h-full text-base-content/50">ไม่มีข้อมูล</div>';
        return;
    }

    let html = '<div class="flex flex-col h-full"><div class="space-y-4 flex-1 overflow-y-auto">';
    sorted.forEach(([name, data], i) => {
        // % relative to this item's own target
        const achieveRatio = data.target > 0 ? Math.round((data.achieved / data.target) * 100) : 0;
        const expectedRatio = data.target > 0 ? Math.round((data.expected / data.target) * 100) : 0;
        // Bar widths: target = 100%, others proportional to target
        const achievedBarW = data.target > 0 ? Math.min((data.achieved / data.target) * 100, 100) : 0;
        const expectedBarW = data.target > 0 ? Math.min((data.expected / data.target) * 100, 100) : 0;

        html += `
            <div>
                <div class="flex justify-between text-sm mb-1">
                    <span class="truncate max-w-[180px] font-medium">${name}</span>
                    <span class="text-xs ${achieveRatio >= 100 ? 'text-success' : achieveRatio >= 50 ? 'text-warning' : 'text-error'} font-bold">${achieveRatio}%</span>
                </div>
                <div class="h-5 bg-base-200 rounded-full overflow-hidden relative">
                    <div class="h-full rounded-full absolute top-0 left-0 z-[1]" style="width: 100%; background-color: ${chartColors[i % chartColors.length]}; opacity: 0.15;"></div>
                    <div class="h-full bg-info/50 rounded-full absolute top-0 left-0 z-[2]" style="width: ${expectedBarW}%"></div>
                    <div class="h-full bg-success rounded-full absolute top-0 left-0 z-[3]" style="width: ${achievedBarW}%"></div>
                </div>
                <div class="flex justify-between text-[10px] text-base-content/50 mt-0.5">
                    <span>Achieved ฿${AutoCommaLocal(data.achieved)} (${achieveRatio}%)</span>
                    <span>Expected ฿${AutoCommaLocal(data.expected)} (${expectedRatio}%)</span>
                    <span>Target ฿${AutoCommaLocal(data.target)}</span>
                </div>
            </div>`;
    });
    html += '</div>';
    html += '<div class="flex gap-4 pt-3 text-xs justify-center border-t border-base-200 mt-3">';
    html += '<span class="flex items-center gap-1"><span class="w-3 h-3 bg-base-300 rounded opacity-25"></span> Target</span>';
    html += '<span class="flex items-center gap-1"><span class="w-3 h-3 bg-info/60 rounded"></span> Expected</span>';
    html += '<span class="flex items-center gap-1"><span class="w-3 h-3 bg-success rounded"></span> Achieved</span>';
    html += '</div></div>';

    container.innerHTML = html;
}

function renderTargetTimeline() {
    const container = document.getElementById('vizTargetTimeline');
    if (!container) return;

    if (!targetsCache || targetsCache.length === 0) {
        container.innerHTML = '<div class="flex items-center justify-center h-48 text-base-content/50"><i class="fa-solid fa-timeline text-3xl mr-3 opacity-30"></i>ไม่มีข้อมูล Target</div>';
        return;
    }

    // Sort targets by start date
    const targets = [...targetsCache].sort((a, b) => new Date(a.StartDate) - new Date(b.StartDate));

    // Find the global time range
    const allDates = targets.flatMap(t => [new Date(t.StartDate), new Date(t.EndDate)]);
    allDates.push(new Date()); // include today
    const minDate = new Date(Math.min(...allDates));
    const maxDate = new Date(Math.max(...allDates));
    const totalDays = Math.max(1, Math.ceil((maxDate - minDate) / (1000 * 60 * 60 * 24)));
    const now = new Date();
    const todayPct = Math.max(0, Math.min(100, ((now - minDate) / (maxDate - minDate)) * 100));

    let html = '<div class="overflow-x-auto">';
    html += '<div class="relative" style="min-width: 600px;">';

    // Today marker line
    html += `<div class="absolute top-0 bottom-0 w-0.5 bg-error/60 z-10" style="left: ${todayPct}%;">
        <div class="absolute -top-0 -translate-x-1/2 badge badge-error badge-xs whitespace-nowrap">Today</div>
    </div>`;

    // Month labels at top
    html += '<div class="flex text-[10px] text-base-content/40 mb-2 relative h-4">';
    const startMonth = new Date(minDate.getFullYear(), minDate.getMonth(), 1);
    const tempDate = new Date(startMonth);
    const monthShort = ['ม.ค.', 'ก.พ.', 'มี.ค.', 'เม.ย.', 'พ.ค.', 'มิ.ย.', 'ก.ค.', 'ส.ค.', 'ก.ย.', 'ต.ค.', 'พ.ย.', 'ธ.ค.'];
    while (tempDate <= maxDate) {
        const pct = Math.max(0, ((tempDate - minDate) / (maxDate - minDate)) * 100);
        if (pct >= 0 && pct <= 100) {
            html += `<span class="absolute" style="left: ${pct}%">${monthShort[tempDate.getMonth()]} ${tempDate.getFullYear() % 100}</span>`;
        }
        tempDate.setMonth(tempDate.getMonth() + 1);
    }
    html += '</div>';

    // Target rows
    targets.forEach((target, i) => {
        const start = new Date(target.StartDate);
        const end = new Date(target.EndDate);
        const leftPct = ((start - minDate) / (maxDate - minDate)) * 100;
        const widthPct = Math.max(2, ((end - start) / (maxDate - minDate)) * 100);
        
        const sumAchieved = target.Leads.reduce((s, l) => s + (l.AchivedRevenue || 0), 0);
        const pct = target.TargetValue > 0 ? Math.min(100, Math.round((sumAchieved / target.TargetValue) * 100)) : 0;
        const borderColor = target.Color?.color?.code || chartColors[i % chartColors.length];
        
        const daysLeft = Math.ceil((end - now) / (1000 * 60 * 60 * 24));
        const isExpired = daysLeft <= 0;
        const opacity = isExpired ? 'opacity-50' : '';

        html += `
            <div class="flex items-center gap-2 mb-2 ${opacity}">
                <div class="w-32 shrink-0 text-xs truncate font-medium" title="${target.Product?.Name} - ${target.SaleArea?.Name}">
                    ${target.Product?.Name || 'N/A'}
                    <div class="text-[10px] text-base-content/50 truncate">${target.SaleArea?.Name || ''}</div>
                </div>
                <div class="flex-1 relative h-8 bg-base-200 rounded">
                    <div class="absolute h-full rounded" style="left: ${leftPct}%; width: ${widthPct}%; background-color: ${borderColor}; opacity: 0.2;"></div>
                    <div class="absolute h-full rounded-l" style="left: ${leftPct}%; width: ${widthPct * (pct / 100)}%; background-color: ${borderColor};"></div>
                    <div class="absolute h-full flex items-center text-[10px] font-bold px-1" style="left: ${leftPct}%; width: ${widthPct}%;">
                        <span class="${pct > 30 ? 'text-white' : ''} truncate">${pct}% — ฿${AutoCommaLocal(sumAchieved)} / ฿${AutoCommaLocal(target.TargetValue || 0)}</span>
                    </div>
                </div>
            </div>`;
    });

    html += '</div></div>';

    container.innerHTML = html;
}

// ============================================
// Create/Edit Pipeline
// ============================================

function createModalPopup(pipelineId = null) {
    console.log('createModalPopup called, pipelineId:', pipelineId);
    
    const modal = document.getElementById('eventModal');
    console.log('Modal element:', modal);
    
    if (!modal) {
        console.error('Modal element not found!');
        return;
    }

    const pipeline = pipelineId ? pipelineCache.find(p => p.Id === pipelineId) : null;
    const title = pipeline ? 'แก้ไข Pipeline' : 'เพิ่ม Pipeline ใหม่';
    const icon = pipeline ? 'fa-pen' : 'fa-layer-group';

    modal.innerHTML = `
        <div class="modal-box">
            <form method="dialog">
                <button class="btn btn-sm btn-circle btn-ghost absolute right-2 top-2">✕</button>
            </form>
            <h3 class="text-lg font-bold flex items-center gap-2 mb-4">
                <i class="fa-solid ${icon} text-primary"></i>
                ${title}
            </h3>
            <div class="space-y-4">
                <div class="form-control">
                    <label class="label">
                        <span class="label-text font-medium">ชื่อ Pipeline</span>
                    </label>
                    <input type="text" id="pipelineTitle" class="input input-bordered w-full" placeholder="กรอกชื่อ Pipeline..." value="${pipeline?.PipelineName || ''}" required>
                </div>
                <div class="form-control">
                    <label class="label">
                        <span class="label-text font-medium">ลำดับการแสดงผล</span>
                    </label>
                    <input type="number" id="pipelineOrder" class="input input-bordered w-full" placeholder="0" value="${pipeline?.Order || 0}">
                    <label class="label">
                        <span class="label-text-alt text-base-content/50">ตัวเลขน้อย = แสดงก่อน</span>
                    </label>
                </div>
            </div>
            <div class="modal-action">
                <form method="dialog">
                    <button class="btn btn-ghost">ยกเลิก</button>
                </form>
                <button class="btn btn-primary" onclick="savePipeline(${pipelineId})">
                    <i class="fa-solid fa-save"></i> บันทึก
                </button>
            </div>
        </div>
        <form method="dialog" class="modal-backdrop">
            <button>close</button>
        </form>
    `;

    console.log('Modal innerHTML set, calling showModal()');
    modal.showModal();
    console.log('showModal() called');
}

async function savePipeline(pipelineId) {
    const token = readToken();
    const name = document.getElementById('pipelineTitle').value;
    const order = parseInt(document.getElementById('pipelineOrder').value) || 0;

    if (!name) {
        alert('กรุณากรอกชื่อ Pipeline');
        return;
    }

    const endpoint = pipelineId
        ? url + '/biomedapi/v2/crm/pipelines/update'
        : url + '/biomedapi/v2/crm/pipelines/create';

    const data = { PipelineName: name, Order: order };
    if (pipelineId) data.Id = pipelineId;

    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        if (!response.ok) throw new Error(await response.text());

        document.getElementById('eventModal')?.close();
        sessionStorage.removeItem('pipelines');
        location.reload();
    } catch (error) {
        alert('เกิดข้อผิดพลาด: ' + error.message);
    }
}

function editPipeline(pipelineId) {
    createModalPopup(pipelineId);
}

// ============================================
// Show Target Detail Modal
// ============================================

async function showTargetDetail(targetId) {
    const modal = document.getElementById('eventModal');
    if (!modal) return;
    
    // Find target from cache
    const target = targetsCache.find(t => t.Id === targetId);
    if (!target) {
        console.error('Target not found:', targetId);
        return;
    }
    
    // Calculate stats
    const sumExpected = target.Leads.reduce((sum, l) => sum + (l.ExpectedRevenue || 0), 0);
    const sumAchieved = target.Leads.reduce((sum, l) => sum + (l.AchivedRevenue || 0), 0);
    const achievedPercent = target.TargetValue > 0 ? Math.round((sumAchieved / target.TargetValue) * 100) : 0;
    const expectedPercent = target.TargetValue > 0 ? Math.round((sumExpected / target.TargetValue) * 100) : 0;
    
    // Calculate remaining days
    const now = new Date();
    const startDate = new Date(target.StartDate);
    const endDate = new Date(target.EndDate);
    const totalDays = Math.ceil((endDate - startDate) / (1000 * 60 * 60 * 24));
    const daysLeft = Math.ceil((endDate - now) / (1000 * 60 * 60 * 24));
    const daysPassed = totalDays - daysLeft;
    const progressPercent = totalDays > 0 ? Math.round((daysPassed / totalDays) * 100) : 0;
    
    // Status color
    let statusClass = 'badge-success';
    let statusText = 'กำลังดำเนินการ';
    if (daysLeft <= 0) {
        statusClass = 'badge-error';
        statusText = 'หมดเวลาแล้ว';
    } else if (daysLeft <= 7) {
        statusClass = 'badge-warning';
        statusText = 'ใกล้หมดเวลา';
    }
    
    // Build leads table
    let leadsHTML = '';
    if (target.Leads.length > 0) {
        leadsHTML = `
            <div class="overflow-x-auto max-h-64">
                <table class="table table-xs table-zebra">
                    <thead class="sticky top-0 bg-base-200">
                        <tr>
                            <th class="text-xs">ชื่อ Lead</th>
                            <th class="text-xs text-right">Expected</th>
                            <th class="text-xs text-right">Achieved</th>
                            <th class="text-xs text-center">สถานะ</th>
                            <th class="text-xs text-center">Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${target.Leads.map(lead => {
                            const leadPercent = lead.ExpectedRevenue > 0 ? Math.round((lead.AchivedRevenue || 0) / lead.ExpectedRevenue * 100) : 0;
                            let leadStatus = 'badge-ghost';
                            if (leadPercent >= 100) leadStatus = 'badge-success';
                            else if (leadPercent >= 50) leadStatus = 'badge-info';
                            else if (leadPercent > 0) leadStatus = 'badge-warning';
                            
                            return `
                                <tr class="hover">
                                    <td class="font-medium text-xs">${lead.LeadName || 'ไม่มีชื่อ'}</td>
                                    <td class="text-right text-xs text-info">${AutoCommaLocal(lead.ExpectedRevenue || 0)} ฿</td>
                                    <td class="text-right text-xs text-success">${AutoCommaLocal(lead.AchivedRevenue || 0)} ฿</td>
                                    <td class="text-center">
                                        <span class="badge ${leadStatus} badge-xs">${leadPercent}%</span>
                                    </td>
                                    <td class="text-center">
                                        <a href="crm-detail.html?leadid=${lead.Id}" class="btn btn-xs btn-ghost btn-circle" title="ดูรายละเอียด">
                                            <i class="fa-solid fa-arrow-right text-primary"></i>
                                        </a>
                                    </td>
                                </tr>
                            `;
                        }).join('')}
                    </tbody>
                </table>
            </div>
        `;
    } else {
        leadsHTML = `
            <div class="text-center py-6 text-base-content/50">
                <i class="fa-solid fa-inbox text-3xl mb-2"></i>
                <p class="text-sm">ยังไม่มี Lead ในเป้าหมายนี้</p>
            </div>
        `;
    }
    
    const borderColor = target.Color?.color?.code || '#6366f1';
    
    modal.innerHTML = `
        <div class="modal-box max-w-2xl" style="border-top: 4px solid ${borderColor}">
            <form method="dialog">
                <button class="btn btn-sm btn-circle btn-ghost absolute right-2 top-2">✕</button>
            </form>
            
            <!-- Header -->
            <div class="mb-4">
                <div class="flex items-center gap-2 mb-1">
                    <i class="fa-solid fa-bullseye text-secondary text-xl"></i>
                    <h3 class="text-lg font-bold">${target.Name || 'เป้าหมาย'}</h3>
                    <span class="badge ${statusClass}">${statusText}</span>
                </div>
                <p class="text-sm text-base-content/60">
                    ${target.Product?.Name || 'N/A'} • ${target.SaleArea?.Name || 'N/A'}
                </p>
            </div>
            
            <!-- Stats Grid -->
            <div class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
                <div class="stat bg-base-200 rounded-lg p-3">
                    <div class="stat-title text-xs">เป้าหมาย</div>
                    <div class="stat-value text-primary text-lg">${AutoCommaLocal(target.TargetValue || 0)}</div>
                    <div class="stat-desc text-xs">บาท</div>
                </div>
                <div class="stat bg-base-200 rounded-lg p-3">
                    <div class="stat-title text-xs">คาดหวัง</div>
                    <div class="stat-value text-info text-lg">${AutoCommaLocal(sumExpected)}</div>
                    <div class="stat-desc text-xs">${expectedPercent}% ของเป้า</div>
                </div>
                <div class="stat bg-base-200 rounded-lg p-3">
                    <div class="stat-title text-xs">สำเร็จ</div>
                    <div class="stat-value text-success text-lg">${AutoCommaLocal(sumAchieved)}</div>
                    <div class="stat-desc text-xs">${achievedPercent}% ของเป้า</div>
                </div>
                <div class="stat bg-base-200 rounded-lg p-3">
                    <div class="stat-title text-xs">Leads</div>
                    <div class="stat-value text-secondary text-lg">${target.Leads.length}</div>
                    <div class="stat-desc text-xs">รายการ</div>
                </div>
            </div>
            
            <!-- Timeline -->
            <div class="bg-base-200 rounded-lg p-3 mb-4">
                <div class="flex items-center justify-between mb-2">
                    <span class="text-xs font-medium">
                        <i class="fa-regular fa-calendar mr-1"></i> ระยะเวลา
                    </span>
                    <span class="text-xs ${daysLeft <= 7 ? 'text-warning font-bold' : 'text-base-content/60'}">
                        ${daysLeft > 0 ? `เหลือ ${daysLeft} วัน` : `เกินมา ${Math.abs(daysLeft)} วัน`}
                    </span>
                </div>
                <div class="flex items-center gap-2 text-xs text-base-content/60 mb-2">
                    <span>${formatDateOnlyLocal(target.StartDate)}</span>
                    <div class="flex-1 h-2 bg-base-300 rounded-full overflow-hidden">
                        <div class="h-full ${daysLeft <= 0 ? 'bg-error' : daysLeft <= 7 ? 'bg-warning' : 'bg-primary'}" 
                             style="width: ${Math.min(progressPercent, 100)}%"></div>
                    </div>
                    <span>${formatDateOnlyLocal(target.EndDate)}</span>
                </div>
                <div class="text-xs text-center text-base-content/50">
                    ผ่านไปแล้ว ${daysPassed} วัน จากทั้งหมด ${totalDays} วัน (${progressPercent}%)
                </div>
            </div>
            
            <!-- Achievement Progress -->
            <div class="bg-base-200 rounded-lg p-3 mb-4">
                <div class="flex items-center justify-between mb-2">
                    <span class="text-xs font-medium">
                        <i class="fa-solid fa-chart-line mr-1"></i> ความคืบหน้า
                    </span>
                    <span class="text-xs font-bold ${achievedPercent >= 100 ? 'text-success' : achievedPercent >= 80 ? 'text-info' : 'text-warning'}">
                        ${achievedPercent}%
                    </span>
                </div>
                <progress class="progress ${achievedPercent >= 100 ? 'progress-success' : achievedPercent >= 80 ? 'progress-info' : 'progress-warning'} w-full" 
                          value="${achievedPercent}" max="100"></progress>
                <div class="flex justify-between text-xs text-base-content/50 mt-1">
                    <span>0%</span>
                    <span>50%</span>
                    <span>100%</span>
                </div>
            </div>
            
            <!-- Leads List -->
            <div class="mb-4">
                <h4 class="font-bold text-sm mb-2 flex items-center gap-2">
                    <i class="fa-solid fa-users text-primary"></i>
                    รายการ Leads (${target.Leads.length})
                </h4>
                ${leadsHTML}
            </div>
            
            <div class="modal-action">
                <form method="dialog">
                    <button class="btn">ปิด</button>
                </form>
            </div>
        </div>
        <form method="dialog" class="modal-backdrop">
            <button>close</button>
        </form>
    `;
    
    modal.showModal();
}

async function deletePipeline(pipelineId) {
    if (!confirm('ต้องการลบ Pipeline นี้หรือไม่?')) return;

    const token = readToken();
    try {
        const response = await fetch(url + '/biomedapi/v2/crm/pipelines/delete', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ Id: pipelineId })
        });

        if (!response.ok) throw new Error(await response.text());

        sessionStorage.removeItem('pipelines');
        location.reload();
    } catch (error) {
        alert('เกิดข้อผิดพลาด: ' + error.message);
    }
}

// ============================================
// Create New Lead
// ============================================

async function createNewLead(pipelineId = null) {
    const modal = document.getElementById('eventModal');
    if (!modal) return;

    const pipelines = pipelineCache;

    modal.innerHTML = `
        <div class="modal-box max-w-lg">
            <form method="dialog">
                <button class="btn btn-sm btn-circle btn-ghost absolute right-2 top-2">✕</button>
            </form>
            <h3 class="text-lg font-bold flex items-center gap-2 mb-4">
                <i class="fa-solid fa-user-plus text-primary"></i>
                เพิ่ม Lead ใหม่
            </h3>
            <div class="space-y-4">
                <div class="form-control">
                    <label class="label">
                        <span class="label-text font-medium">ชื่อ Lead <span class="text-error">*</span></span>
                    </label>
                    <input type="text" id="leadName" class="input input-bordered w-full" placeholder="กรอกชื่อ Lead..." required>
                </div>
                
                <div class="form-control">
                    <label class="label">
                        <span class="label-text font-medium">Pipeline <span class="text-error">*</span></span>
                    </label>
                    <select id="leadPipeline" class="select select-bordered w-full">
                        ${pipelines.map(p => `<option value="${p.Id}" ${p.Id === pipelineId ? 'selected' : ''}>${p.PipelineName}</option>`).join('')}
                    </select>
                    <label class="label">
                        <span class="label-text-alt text-base-content/50">เลือก Pipeline ที่ต้องการเพิ่ม Lead</span>
                    </label>
                </div>
            </div>
            <div class="modal-action">
                <form method="dialog">
                    <button class="btn btn-ghost">ยกเลิก</button>
                </form>
                <button class="btn btn-primary" onclick="submitNewLead()">
                    <i class="fa-solid fa-plus"></i> สร้าง Lead
                </button>
            </div>
        </div>
        <form method="dialog" class="modal-backdrop">
            <button>close</button>
        </form>
    `;

    modal.showModal();
}

async function submitNewLead() {
    const token = readToken();
    const leadName = document.getElementById('leadName').value;
    const pipelineId = parseInt(document.getElementById('leadPipeline').value);

    if (!leadName) {
        alert('กรุณากรอกชื่อ Lead');
        return;
    }

    try {
        const response = await fetch(url + '/biomedapi/v2/crm/leads/create', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                LeadName: leadName,
                PipelineId: pipelineId
            })
        });

        if (!response.ok) throw new Error(await response.text());

        const leadId = await response.text();
        document.getElementById('eventModal')?.close();

        // Redirect to detail page
        window.location.href = `crm-detail.html?leadid=${leadId}`;
    } catch (error) {
        alert('เกิดข้อผิดพลาด: ' + error.message);
    }
}

// ============================================
// Filter Components (MultiSelect & RangeSlider)
// ============================================

// Store filter components
let filterComponents = {
    userSelect: null,
    productSelect: null,
    saleAreaSelect: null,
    creationSlider: null,
    updateSlider: null,
    expectedSlider: null
};

/**
 * Initialize all filter components after data is loaded
 */
async function initializeFilterComponents() {
    console.log('Initializing filter components...');

    // Check if MultiSelect class is available
    if (typeof MultiSelect === 'undefined') {
        console.warn('MultiSelect class not found, skipping filter initialization');
        return;
    }

    // User MultiSelect
    if (document.getElementById('userFilter')) {
        const userOptions = usersCache.map(u => ({
            value: u.Id.toString(),
            label: `${u.FirstName || ''} ${u.LastName || ''}`.trim() || u.Username
        }));

        filterComponents.userSelect = new MultiSelect('userFilter', {
            options: userOptions,
            placeholder: 'เลือกผู้รับผิดชอบ...',
            badgeClass: 'badge-secondary',
            searchable: true,
            showSelectAll: true,
            text: {
                search: 'ค้นหาผู้ใช้...',
                selectAll: 'เลือกทั้งหมด',
                clearAll: 'ล้างทั้งหมด',
                noResults: 'ไม่พบผู้ใช้'
            }
        });
    }

    // Product MultiSelect
    if (document.getElementById('productFilter')) {
        const productOptions = productsCache.map(p => ({
            value: p.Id.toString(),
            label: p.Name
        }));

        filterComponents.productSelect = new MultiSelect('productFilter', {
            options: productOptions,
            placeholder: 'เลือกสินค้า...',
            badgeClass: 'badge-accent',
            searchable: true,
            showSelectAll: true,
            text: {
                search: 'ค้นหาสินค้า...',
                selectAll: 'เลือกทั้งหมด',
                clearAll: 'ล้างทั้งหมด',
                noResults: 'ไม่พบสินค้า'
            }
        });
    }

    // Sale Area MultiSelect
    if (document.getElementById('saleAreaFilter')) {
        const saleAreaOptions = saleAreasCache.map(s => ({
            value: s.Id.toString(),
            label: s.Name
        }));

        filterComponents.saleAreaSelect = new MultiSelect('saleAreaFilter', {
            options: saleAreaOptions,
            placeholder: 'เลือกพื้นที่ขาย...',
            badgeClass: 'badge-info',
            searchable: true,
            showSelectAll: true,
            text: {
                search: 'ค้นหาพื้นที่...',
                selectAll: 'เลือกทั้งหมด',
                clearAll: 'ล้างทั้งหมด',
                noResults: 'ไม่พบพื้นที่'
            }
        });
    }

    // Initialize RangeSliders for date filtering
    initializeDateSliders();

    console.log('Filter components initialized');
}

/**
 * Initialize date range sliders
 */
function initializeDateSliders() {
    _createDateSliders();
}

/**
 * Reinitialize sliders when quarter mode changes (preserves relative positions)
 */
function reinitializeDateSliders() {
    _createDateSliders();
}

/**
 * Internal: create/recreate all date sliders
 */
function _createDateSliders() {
    // Check if RangeSlider class is available
    if (typeof RangeSlider === 'undefined') {
        console.warn('RangeSlider class not found, skipping slider initialization');
        return;
    }

    const trans = getActiveTranslator();
    const translatorLength = trans.length;

    // Format function for quarter display using active translator
    const formatQuarter = (val) => {
        const t = getActiveTranslator();
        const idx = Math.round(val);
        if (t && t[idx]) return t[idx];
        return `Q${idx}`;
    };

    // Helper: get current quarter index in active translator
    function getCurrentQuarterIndex() {
        let currentIndex = Math.floor(translatorLength / 2);
        const now = new Date();
        let qy;
        if (quarterMode === 'standard') {
            qy = getStandardQuarterAndYearByDate(now);
        } else if (typeof getQuarterAndYearByDate === 'function') {
            qy = getQuarterAndYearByDate(now);
        }
        if (qy) {
            const searchStr = `${qy.quarter} ${qy.year}`;
            const found = trans.findIndex(t => t === searchStr);
            if (found >= 0) currentIndex = found;
        }
        return currentIndex;
    }

    // Clear existing slider DOM content before recreating
    ['creationRangeSlider', 'updateRangeSlider', 'expectedRangeSlider'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.innerHTML = '';
    });

    // Creation Date Slider
    if (document.getElementById('creationRangeSlider')) {
        filterComponents.creationSlider = new RangeSlider('creationRangeSlider', {
            min: 0,
            max: translatorLength - 1,
            value: [0, translatorLength - 1],
            step: 1,
            range: true,
            showLabels: true,
            showTooltip: true,
            showFill: true,
            colorClass: 'range-primary',
            formatValue: formatQuarter,
            text: { from: 'เริ่ม', to: 'ถึง' }
        });
    }

    // Update Date Slider
    if (document.getElementById('updateRangeSlider')) {
        filterComponents.updateSlider = new RangeSlider('updateRangeSlider', {
            min: 0,
            max: translatorLength - 1,
            value: [0, translatorLength - 1],
            step: 1,
            range: true,
            showLabels: true,
            showTooltip: true,
            showFill: true,
            colorClass: 'range-warning',
            formatValue: formatQuarter,
            text: { from: 'เริ่ม', to: 'ถึง' }
        });
    }

    // Expected Date Slider
    if (document.getElementById('expectedRangeSlider')) {
        const currentIndex = getCurrentQuarterIndex();
        filterComponents.expectedSlider = new RangeSlider('expectedRangeSlider', {
            min: 0,
            max: translatorLength - 1,
            value: [currentIndex, currentIndex],
            step: 1,
            range: true,
            showLabels: true,
            showTooltip: true,
            showFill: true,
            colorClass: 'range-accent',
            formatValue: formatQuarter,
            text: { from: 'เริ่ม', to: 'ถึง' }
        });
    }
}

/**
 * Get date range from quarter index (for API query)
 * Uses active Translator array based on quarterMode
 */
function getDateRangeFromQuarterIndex(quarterIndex) {
    // If standard mode, use standard date range calculation
    if (quarterMode === 'standard') {
        return getStandardDateRangeFromQuarterIndex(quarterIndex);
    }

    // Use Translator array from biomed-global.js (fiscal mode)
    if (typeof Translator !== 'undefined' && Translator.length > 0) {
        if (quarterIndex < 0 || quarterIndex >= Translator.length) {
            console.warn('Invalid quarter index:', quarterIndex, 'Translator length:', Translator.length);
            return null;
        }
        
        const quarterStr = Translator[quarterIndex]; // e.g. "Q1 2023"
        const match = quarterStr.match(/Q(\d)\s+(\d{4})/);
        
        if (match) {
            const quarter = parseInt(match[1]); // 1-4
            const year = parseInt(match[2]) - 2000; // Convert 2023 to 23 for getQuarterDateRange
            
            if (typeof getQuarterDateRange === 'function') {
                try {
                    return getQuarterDateRange(quarter, year);
                } catch (e) {
                    console.warn('getQuarterDateRange error:', e);
                }
            }
        }
    }

    // Fallback calculation if Translator or getQuarterDateRange not available
    const quarters = [
        { Quarter: "Q1", Year: 2023 },
        { Quarter: "Q2", Year: 2023 },
        { Quarter: "Q3", Year: 2023 },
        { Quarter: "Q4", Year: 2023 },
        { Quarter: "Q1", Year: 2024 },
        { Quarter: "Q2", Year: 2024 },
        { Quarter: "Q3", Year: 2024 },
        { Quarter: "Q4", Year: 2024 },
        { Quarter: "Q1", Year: 2025 },
        { Quarter: "Q2", Year: 2025 },
        { Quarter: "Q3", Year: 2025 },
        { Quarter: "Q4", Year: 2025 },
        { Quarter: "Q1", Year: 2026 },
        { Quarter: "Q2", Year: 2026 },
        { Quarter: "Q3", Year: 2026 },
        { Quarter: "Q4", Year: 2026 },
        { Quarter: "Q1", Year: 2027 },
        { Quarter: "Q2", Year: 2027 },
        { Quarter: "Q3", Year: 2027 },
        { Quarter: "Q4", Year: 2027 }
    ];

    if (quarterIndex < 0 || quarterIndex >= quarters.length) return null;

    const { Quarter, Year } = quarters[quarterIndex];
    const q = parseInt(Quarter.replace('Q', ''));
    
    // Thai fiscal year quarters
    // Q1: May-Jul, Q2: Aug-Oct, Q3: Nov-Jan, Q4: Feb-Apr
    let startMonth, endMonth, startYear, endYear;
    
    switch (q) {
        case 1: // May-Jul
            startMonth = 4; endMonth = 6; // May=4, Jul=6 (0-indexed)
            startYear = Year; endYear = Year;
            break;
        case 2: // Aug-Oct
            startMonth = 7; endMonth = 9;
            startYear = Year; endYear = Year;
            break;
        case 3: // Nov-Jan (crosses year)
            startMonth = 10; endMonth = 0;
            startYear = Year; endYear = Year + 1;
            break;
        case 4: // Feb-Apr
            startMonth = 1; endMonth = 3;
            startYear = Year + 1; endYear = Year + 1;
            break;
    }

    const startDate = new Date(startYear, startMonth, 1);
    const endDate = new Date(endYear, endMonth + 1, 0);
    endDate.setHours(23, 59, 59);

    return {
        startDate: startDate,
        endDate: endDate
    };
}

// ============================================
// Filter Functions
// ============================================

/**
 * Update URL with query parameters for QuickNav integration
 */
function updateCRMQueryURL() {
    const urlParams = new URLSearchParams();
    const trans = getActiveTranslator();
    
    // Save quarter mode
    urlParams.set('QuarterMode', quarterMode);
    
    // Get search text
    const searchText = document.getElementById('crmQuery')?.value || '';
    if (searchText) urlParams.set('Query', searchText);
    
    // Get MultiSelect values
    if (filterComponents.userSelect) {
        const userIds = filterComponents.userSelect.getValues();
        if (userIds && userIds.length > 0) urlParams.set('UserIDs', userIds.join(','));
    }
    if (filterComponents.productSelect) {
        const productIds = filterComponents.productSelect.getValues();
        if (productIds && productIds.length > 0) urlParams.set('ProductIDs', productIds.join(','));
    }
    if (filterComponents.saleAreaSelect) {
        const saleAreaIds = filterComponents.saleAreaSelect.getValues();
        if (saleAreaIds && saleAreaIds.length > 0) urlParams.set('SaleAreaIDs', saleAreaIds.join(','));
    }
    
    // Get slider values - store as index positions (or manual dates)
    if (quarterMode === 'manual') {
        const manualCreationStart = document.getElementById('manualCreationStart')?.value;
        const manualCreationEnd = document.getElementById('manualCreationEnd')?.value;
        const manualUpdateStart = document.getElementById('manualUpdateStart')?.value;
        const manualUpdateEnd = document.getElementById('manualUpdateEnd')?.value;
        const manualExpectedStart = document.getElementById('manualExpectedStart')?.value;
        const manualExpectedEnd = document.getElementById('manualExpectedEnd')?.value;
        if (manualCreationStart) urlParams.set('ManualCreationStart', manualCreationStart);
        if (manualCreationEnd) urlParams.set('ManualCreationEnd', manualCreationEnd);
        if (manualUpdateStart) urlParams.set('ManualUpdateStart', manualUpdateStart);
        if (manualUpdateEnd) urlParams.set('ManualUpdateEnd', manualUpdateEnd);
        if (manualExpectedStart) urlParams.set('ManualExpectedStart', manualExpectedStart);
        if (manualExpectedEnd) urlParams.set('ManualExpectedEnd', manualExpectedEnd);
    } else {
        if (filterComponents.creationSlider) {
            const values = filterComponents.creationSlider.getValues();
            if (Array.isArray(values)) {
                urlParams.set('CreationRange', values.map(Math.round).join(','));
            }
        }
        if (filterComponents.updateSlider) {
            const values = filterComponents.updateSlider.getValues();
            if (Array.isArray(values)) {
                urlParams.set('UpdateRange', values.map(Math.round).join(','));
            }
        }
        if (filterComponents.expectedSlider) {
            const values = filterComponents.expectedSlider.getValues();
            if (Array.isArray(values)) {
                urlParams.set('ExpectedRange', values.map(Math.round).join(','));
            }
        }
    }
    
    // Update URL without reload
    const newUrl = `${window.location.pathname}?${urlParams.toString()}`;
    window.history.replaceState(null, '', newUrl);
}

/**
 * Parse URL query parameters and apply to filters
 */
function parseCRMQueryURL() {
    const urlParams = new URLSearchParams(window.location.search);
    
    // Apply quarter mode from URL (overrides localStorage)
    const qMode = urlParams.get('QuarterMode');
    if (qMode === 'fiscal' || qMode === 'standard' || qMode === 'manual') {
        quarterMode = qMode;
        localStorage.setItem('crmQuarterMode', qMode);
    }
    
    // Apply search text
    const queryText = urlParams.get('Query');
    if (queryText) {
        const crmQuery = document.getElementById('crmQuery');
        if (crmQuery) crmQuery.value = queryText;
    }
    
    // Apply MultiSelect values (will be applied after components init)
    const userIds = urlParams.get('UserIDs')?.split(',').filter(Boolean);
    const productIds = urlParams.get('ProductIDs')?.split(',').filter(Boolean);
    const saleAreaIds = urlParams.get('SaleAreaIDs')?.split(',').filter(Boolean);
    
    // Apply slider values
    const creationRange = urlParams.get('CreationRange')?.split(',').map(Number);
    const updateRange = urlParams.get('UpdateRange')?.split(',').map(Number);
    const expectedRange = urlParams.get('ExpectedRange')?.split(',').map(Number);
    
    // Manual date values from URL
    const manualCreationStart = urlParams.get('ManualCreationStart');
    const manualCreationEnd = urlParams.get('ManualCreationEnd');
    const manualUpdateStart = urlParams.get('ManualUpdateStart');
    const manualUpdateEnd = urlParams.get('ManualUpdateEnd');
    const manualExpectedStart = urlParams.get('ManualExpectedStart');
    const manualExpectedEnd = urlParams.get('ManualExpectedEnd');
    
    // Store parsed values for later application
    window.crmUrlParams = {
        userIds,
        productIds,
        saleAreaIds,
        creationRange,
        updateRange,
        expectedRange,
        manualCreationStart,
        manualCreationEnd,
        manualUpdateStart,
        manualUpdateEnd,
        manualExpectedStart,
        manualExpectedEnd
    };
    
    console.log('Parsed CRM URL params:', window.crmUrlParams);
}

/**
 * Apply parsed URL params to filter components (call after components are initialized)
 */
function applyCRMUrlParamsToFilters() {
    if (!window.crmUrlParams) return;
    
    const { userIds, productIds, saleAreaIds, creationRange, updateRange, expectedRange, manualCreationStart, manualCreationEnd, manualUpdateStart, manualUpdateEnd, manualExpectedStart, manualExpectedEnd } = window.crmUrlParams;
    
    // Apply MultiSelect values
    if (userIds && filterComponents.userSelect) {
        filterComponents.userSelect.setValues(userIds);
    }
    if (productIds && filterComponents.productSelect) {
        filterComponents.productSelect.setValues(productIds);
    }
    if (saleAreaIds && filterComponents.saleAreaSelect) {
        filterComponents.saleAreaSelect.setValues(saleAreaIds);
    }
    
    // Apply slider values (for fiscal/standard mode)
    if (creationRange && creationRange.length === 2 && filterComponents.creationSlider) {
        filterComponents.creationSlider.setValues(creationRange);
    }
    if (updateRange && updateRange.length === 2 && filterComponents.updateSlider) {
        filterComponents.updateSlider.setValues(updateRange);
    }
    if (expectedRange && expectedRange.length === 2 && filterComponents.expectedSlider) {
        filterComponents.expectedSlider.setValues(expectedRange);
    }
    
    // Apply manual date values (for manual mode)
    if (manualCreationStart) {
        const el = document.getElementById('manualCreationStart');
        if (el) el.value = manualCreationStart;
    }
    if (manualCreationEnd) {
        const el = document.getElementById('manualCreationEnd');
        if (el) el.value = manualCreationEnd;
    }
    if (manualUpdateStart) {
        const el = document.getElementById('manualUpdateStart');
        if (el) el.value = manualUpdateStart;
    }
    if (manualUpdateEnd) {
        const el = document.getElementById('manualUpdateEnd');
        if (el) el.value = manualUpdateEnd;
    }
    if (manualExpectedStart) {
        const el = document.getElementById('manualExpectedStart');
        if (el) el.value = manualExpectedStart;
    }
    if (manualExpectedEnd) {
        const el = document.getElementById('manualExpectedEnd');
        if (el) el.value = manualExpectedEnd;
    }
    
    console.log('Applied URL params to CRM filters');
    
    // Clear stored params
    delete window.crmUrlParams;
}

async function applyFilters() {
    // Get myUser for default SaleArea/Product values
    const myUser = await crmGetMyUser();
    console.log("applyFilters myUser:", myUser);
    console.log("applyFilters SaleAreaUsers:", myUser?.SaleAreaUsers);
    console.log("applyFilters ProductUsers:", myUser?.ProductUsers);
    
    const defaultSaleAreaIDs = myUser?.SaleAreaUsers?.map(sa => sa.SaleAreaId) || [];
    const defaultProductIDs = myUser?.ProductUsers?.map(pu => pu.ProductId) || [];
    console.log("applyFilters defaults - SaleAreaIDs:", defaultSaleAreaIDs, "ProductIDs:", defaultProductIDs);

    // Get filter values from dropdown search
    const searchText = document.getElementById('crmQuery')?.value || 
                       document.getElementById('searchInput')?.value || '';

    // Build query
    const query = {};

    // Title search
    if (searchText) {
        query.Title = searchText;
    }

    // Get MultiSelect values - use myUser's values if not selected
    if (filterComponents.userSelect) {
        const userIds = filterComponents.userSelect.getValues();
        query.UserIDs = (userIds && userIds.length > 0) ? userIds.map(Number) : null;
    }

    if (filterComponents.productSelect) {
        const productIds = filterComponents.productSelect.getValues();
        console.log("=== Product Filter Debug ===");
        console.log("MultiSelect productIds:", productIds);
        console.log("productIds.length:", productIds?.length);
        console.log("defaultProductIDs:", defaultProductIDs);
        query.ProductIDs = (productIds && productIds.length > 0) ? productIds.map(Number) : defaultProductIDs;
        console.log("Final query.ProductIDs:", query.ProductIDs);
    } else {
        query.ProductIDs = defaultProductIDs;
        console.log("No productSelect component, using default:", defaultProductIDs);
    }

    if (filterComponents.saleAreaSelect) {
        const saleAreaIds = filterComponents.saleAreaSelect.getValues();
        console.log("=== SaleArea Filter Debug ===");
        console.log("MultiSelect saleAreaIds:", saleAreaIds);
        console.log("saleAreaIds.length:", saleAreaIds?.length);
        console.log("defaultSaleAreaIDs:", defaultSaleAreaIDs);
        query.SaleAreaIDs = (saleAreaIds && saleAreaIds.length > 0) ? saleAreaIds.map(Number) : defaultSaleAreaIDs;
        console.log("Final query.SaleAreaIDs:", query.SaleAreaIDs);
    } else {
        query.SaleAreaIDs = defaultSaleAreaIDs;
        console.log("No saleAreaSelect component, using default:", defaultSaleAreaIDs);
    }

    // Get date range values from sliders or manual inputs
    if (quarterMode === 'manual') {
        // Manual mode: read date inputs directly
        const creationStart = document.getElementById('manualCreationStart')?.value;
        const creationEnd = document.getElementById('manualCreationEnd')?.value;
        const updateStart = document.getElementById('manualUpdateStart')?.value;
        const updateEnd = document.getElementById('manualUpdateEnd')?.value;
        const expectedStart = document.getElementById('manualExpectedStart')?.value;
        const expectedEnd = document.getElementById('manualExpectedEnd')?.value;
        
        if (creationStart) {
            // Build start of day in local time, then format
            const sd = new Date(creationStart + 'T00:00:00');
            query.StartDate = timeFormaterLocal(sd);
        }
        if (creationEnd) {
            // Build end of day in local time, then format
            const ed = new Date(creationEnd + 'T23:59:59');
            query.EndDate = timeFormaterLocal(ed);
        }
        if (updateStart) {
            const us = new Date(updateStart + 'T00:00:00');
            query.UpdateStart = timeFormaterLocal(us);
        }
        if (updateEnd) {
            const ue = new Date(updateEnd + 'T23:59:59');
            query.UpdateEnd = timeFormaterLocal(ue);
        }
        if (expectedStart) {
            const es = new Date(expectedStart + 'T00:00:00');
            query.ExpectedStart = timeFormaterLocal(es);
        }
        if (expectedEnd) {
            const ee = new Date(expectedEnd + 'T23:59:59');
            query.ExpectedEnd = timeFormaterLocal(ee);
        }
    } else {
        // Quarter slider mode (fiscal / standard)
        if (filterComponents.creationSlider) {
            const values = filterComponents.creationSlider.getValues();
            const [startIdx, endIdx] = Array.isArray(values) ? values : [values, values];
            const startRange = getDateRangeFromQuarterIndex(Math.round(startIdx));
            const endRange = getDateRangeFromQuarterIndex(Math.round(endIdx));
            if (startRange && endRange) {
                query.StartDate = timeFormaterLocal(startRange.startDate);
                query.EndDate = timeFormaterLocal(endRange.endDate);
            }
        }

        if (filterComponents.expectedSlider) {
            const values = filterComponents.expectedSlider.getValues();
            const [startIdx, endIdx] = Array.isArray(values) ? values : [values, values];
            const startRange = getDateRangeFromQuarterIndex(Math.round(startIdx));
            const endRange = getDateRangeFromQuarterIndex(Math.round(endIdx));
            if (startRange && endRange) {
                query.ExpectedStart = timeFormaterLocal(startRange.startDate);
                query.ExpectedEnd = timeFormaterLocal(endRange.endDate);
            }
        }
    }

    console.log('Applying filters with query:', query);

    // Update URL for QuickNav integration
    updateCRMQueryURL();

    // Reload leads with new query
    await displayLeads(query);
    
    // Update table view if it's currently visible
    const tableView = document.getElementById('tableContainer');
    if (tableView && !tableView.classList.contains('hidden')) {
        displayTableView();
    }
    
    // Update visualization view if it's currently visible
    const vizView = document.getElementById('vizContainer');
    if (vizView && !vizView.classList.contains('hidden')) {
        renderVisualization();
    }
    
    // Reload targets with same filter (SaleAreaIDs, ProductIDs, ExpectedStart, ExpectedEnd)
    targetDisplay(query.SaleAreaIDs, query.ProductIDs, query.ExpectedStart, query.ExpectedEnd);
}

function clearFilters() {
    // Clear text inputs
    const searchInput = document.getElementById('searchInput');
    const crmQuery = document.getElementById('crmQuery');
    if (searchInput) searchInput.value = '';
    if (crmQuery) crmQuery.value = '';

    // Clear MultiSelects
    if (filterComponents.userSelect) filterComponents.userSelect.clearAll();
    if (filterComponents.productSelect) filterComponents.productSelect.clearAll();
    if (filterComponents.saleAreaSelect) filterComponents.saleAreaSelect.clearAll();

    // Reset sliders to full range
    const translatorLength = getActiveTranslator().length;
    if (filterComponents.creationSlider) filterComponents.creationSlider.setValues([0, translatorLength - 1]);
    if (filterComponents.updateSlider) filterComponents.updateSlider.setValues([0, translatorLength - 1]);
    if (filterComponents.expectedSlider) filterComponents.expectedSlider.setValues([0, translatorLength - 1]);

    // Clear manual date inputs
    ['manualCreationStart', 'manualCreationEnd', 'manualUpdateStart', 'manualUpdateEnd', 'manualExpectedStart', 'manualExpectedEnd'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.value = '';
    });

    // Reload with empty query
    displayLeads({});
}

// ============================================
// Search (for dropdown)
// ============================================

function querysearch() {
    applyFilters();
}

// ============================================
// Initialization
// ============================================

async function initCRM() {
    console.log('Initializing CRM (daisyUI version)...');

    // Check authentication
    const token = readToken();
    if (!token) {
        console.error('No token found, redirecting to login');
        window.location.href = 'login.html';
        return;
    }

    // Parse URL params first (before loading data)
    parseCRMQueryURL();

    // Load cache data first (needed for MultiSelect options)
    console.log('Loading cache data...');
    await Promise.all([
        crmGetUsers(),
        crmGetProducts(),
        crmGetSaleAreas()
    ]);
    console.log('Cache loaded - users:', usersCache.length, 'products:', productsCache.length, 'saleAreas:', saleAreasCache.length);

    // Initialize filter components after data is loaded
    await initializeFilterComponents();

    // Restore quarter mode toggle UI
    setQuarterMode(quarterMode);
    
    // Apply URL params to filters (after components are ready)
    applyCRMUrlParamsToFilters();

    // Load initial data using current filter values
    await applyFilters();

    // Setup dropdown search input
    const crmQuery = document.getElementById('crmQuery');
    if (crmQuery) {
        crmQuery.addEventListener('keyup', (e) => {
            if (e.key === 'Enter') {
                applyFilters();
            }
        });
    }

    console.log('CRM initialized successfully');
}

// Start on DOM ready
document.addEventListener('DOMContentLoaded', initCRM);
