// biomed-project-overview.js - DaisyUI version of Project Overview
var pipelineCache = [];
var pipelineIdCache = null;
var projectCache = null;
var deletePipelineId = null;
var allActivitiesCache = []; // Cache all activities for table/viz views

const urlParams = new URLSearchParams(window.location.search);
const projectId = urlParams.get('projectId');

// Tab switching function
function switchTab(tab) {
    // Update tab buttons
    document.getElementById('tabKanban').classList.remove('tab-active');
    document.getElementById('tabTable').classList.remove('tab-active');
    document.getElementById('tabViz').classList.remove('tab-active');
    document.getElementById('tab' + tab.charAt(0).toUpperCase() + tab.slice(1)).classList.add('tab-active');
    
    // Show/hide views
    document.getElementById('viewKanban').classList.add('hidden');
    document.getElementById('viewTable').classList.add('hidden');
    document.getElementById('viewViz').classList.add('hidden');
    
    if (tab === 'kanban') {
        document.getElementById('viewKanban').classList.remove('hidden');
    } else if (tab === 'table') {
        document.getElementById('viewTable').classList.remove('hidden');
        renderTableView();
    } else if (tab === 'viz') {
        document.getElementById('viewViz').classList.remove('hidden');
        renderVizView();
    }
}

// Render Table View
async function renderTableView() {
    const tableBody = document.getElementById('tableBody');
    
    if (allActivitiesCache.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center py-8 text-base-content/50">
                    <i class="fas fa-inbox text-3xl mb-2"></i>
                    <p>ไม่มี Activity</p>
                </td>
            </tr>
        `;
        return;
    }
    
    tableBody.innerHTML = '';
    
    let index = 1;
    for (const activity of allActivitiesCache) {
        const pipeline = pipelineCache.find(p => p.Id === activity.PipelineId || 
            (p.Activities && p.Activities.some(a => a.Id === activity.Id)));
        const pipelineName = pipeline ? (pipeline.PipelineName || pipeline.Name) : '-';
        
        // Get user
        let userName = 'Unknown';
        try {
            const user = await promiseUserById(activity.MainUserId);
            if (user) {
                userName = `${user.FirstName} ${user.LastName}`;
            }
        } catch (e) {}
        
        // Calculate status
        const status = getActivityStatus(activity);
        
        // Format date
        const updateDate = activity.Update || activity.Creation;
        let formattedDate = '-';
        if (updateDate) {
            const d = new Date(updateDate);
            const thaiMonths = ['ม.ค.', 'ก.พ.', 'มี.ค.', 'เม.ย.', 'พ.ค.', 'มิ.ย.', 'ก.ค.', 'ส.ค.', 'ก.ย.', 'ต.ค.', 'พ.ย.', 'ธ.ค.'];
            formattedDate = `${d.getDate()} ${thaiMonths[d.getMonth()]} ${d.getFullYear() + 543}`;
        }
        
        const row = document.createElement('tr');
        row.className = 'hover cursor-pointer';
        row.innerHTML = `
            <td class="font-mono text-xs">${index}</td>
            <td class="font-semibold">${escapeHtml(activity.Name)}</td>
            <td><span class="badge badge-primary badge-sm">${escapeHtml(pipelineName)}</span></td>
            <td>${escapeHtml(userName)}</td>
            <td>${status.badge}</td>
            <td class="text-sm">${formattedDate}</td>
            <td>
                <a href="./project-activity.html?activityid=${activity.Id}" class="btn btn-ghost btn-xs">
                    <i class="fas fa-eye"></i>
                </a>
            </td>
        `;
        row.addEventListener('click', (e) => {
            if (!e.target.closest('a')) {
                window.location.href = `./project-activity.html?activityid=${activity.Id}`;
            }
        });
        tableBody.appendChild(row);
        index++;
    }
}

// Get activity status
function getActivityStatus(activity) {
    const thirtyDaysAgo = new Date();
    thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
    
    const threeMonthsAgo = new Date();
    threeMonthsAgo.setDate(threeMonthsAgo.getDate() - 90);
    
    const lastUpdate = new Date(activity.Update || activity.Creation);
    
    if (lastUpdate < threeMonthsAgo) {
        return { 
            status: 'inactive', 
            badge: '<span class="badge badge-error badge-sm gap-1"><i class="fi fi-rr-ban text-xs"></i> Inactive</span>' 
        };
    } else if (lastUpdate < thirtyDaysAgo) {
        return { 
            status: 'warning', 
            badge: '<span class="badge badge-warning badge-sm gap-1"><i class="fi fi-rr-triangle-warning text-xs"></i> Warning</span>' 
        };
    } else {
        return { 
            status: 'active', 
            badge: '<span class="badge badge-success badge-sm gap-1"><i class="fi fi-rr-check text-xs"></i> Active</span>' 
        };
    }
}

// Render Visualization View
function renderVizView() {
    if (allActivitiesCache.length === 0) {
        document.getElementById('chartPipeline').innerHTML = '<p class="text-base-content/50">ไม่มีข้อมูล</p>';
        document.getElementById('chartStatus').innerHTML = '<p class="text-base-content/50">ไม่มีข้อมูล</p>';
        document.getElementById('chartUser').innerHTML = '<p class="text-base-content/50">ไม่มีข้อมูล</p>';
        return;
    }
    
    // Calculate statistics
    let activeCount = 0, warnCount = 0, inactiveCount = 0;
    const pipelineStats = {};
    const userStats = {};
    
    for (const activity of allActivitiesCache) {
        const status = getActivityStatus(activity);
        if (status.status === 'active') activeCount++;
        else if (status.status === 'warning') warnCount++;
        else inactiveCount++;
        
        // Pipeline stats
        const pipeline = pipelineCache.find(p => p.Id === activity.PipelineId || 
            (p.Activities && p.Activities.some(a => a.Id === activity.Id)));
        const pipelineName = pipeline ? (pipeline.PipelineName || pipeline.Name) : 'Unknown';
        pipelineStats[pipelineName] = (pipelineStats[pipelineName] || 0) + 1;
        
        // User stats
        userStats[activity.MainUserId] = (userStats[activity.MainUserId] || 0) + 1;
    }
    
    const total = allActivitiesCache.length;
    
    // Update summary stats
    document.getElementById('statTotal').textContent = total;
    document.getElementById('statActive').textContent = activeCount;
    document.getElementById('statActivePercent').textContent = total > 0 ? Math.round(activeCount/total*100) + '%' : '0%';
    document.getElementById('statWarn').textContent = warnCount;
    document.getElementById('statWarnPercent').textContent = total > 0 ? Math.round(warnCount/total*100) + '%' : '0%';
    document.getElementById('statInactive').textContent = inactiveCount;
    document.getElementById('statInactivePercent').textContent = total > 0 ? Math.round(inactiveCount/total*100) + '%' : '0%';
    
    // Render Pipeline Chart (simple bar visualization)
    renderBarChart('chartPipeline', pipelineStats, 'primary');
    
    // Render Status Chart (donut-like)
    renderStatusChart('chartStatus', { 'Active': activeCount, 'Warning': warnCount, 'Inactive': inactiveCount });
    
    // Render User Chart
    renderUserChart('chartUser', userStats);
}

// Simple bar chart renderer with inline colors
function renderBarChart(containerId, data, color) {
    const container = document.getElementById(containerId);
    const maxValue = Math.max(...Object.values(data));
    
    // Color map for consistent colors
    const colorMap = {
        'primary': '#6366f1',
        'secondary': '#ec4899',
        'accent': '#14b8a6',
        'success': '#22c55e',
        'warning': '#f59e0b',
        'error': '#ef4444',
        'info': '#3b82f6'
    };
    const barColor = colorMap[color] || color || '#6366f1';
    
    let html = '<div class="space-y-2 w-full">';
    for (const [label, value] of Object.entries(data)) {
        const percent = maxValue > 0 ? (value / maxValue * 100) : 0;
        html += `
            <div class="flex items-center gap-2">
                <span class="text-xs w-24 truncate" title="${escapeHtml(label)}">${escapeHtml(label)}</span>
                <div class="flex-1 bg-base-200 rounded-full h-4 overflow-hidden">
                    <div class="h-full rounded-full transition-all duration-500" style="width: ${percent}%; background-color: ${barColor}"></div>
                </div>
                <span class="text-xs font-bold w-8 text-right">${value}</span>
            </div>
        `;
    }
    html += '</div>';
    container.innerHTML = html;
}

// Status chart (with color-coded bars)
function renderStatusChart(containerId, data) {
    const container = document.getElementById(containerId);
    const total = Object.values(data).reduce((a, b) => a + b, 0);
    
    // Use inline colors for proper rendering
    const colorStyles = { 
        'Active': { bg: '#22c55e', text: 'white' }, 
        'Warning': { bg: '#f59e0b', text: 'white' }, 
        'Inactive': { bg: '#ef4444', text: 'white' } 
    };
    
    let html = '<div class="space-y-3 w-full">';
    for (const [label, value] of Object.entries(data)) {
        const percent = total > 0 ? (value / total * 100) : 0;
        const colorStyle = colorStyles[label];
        html += `
            <div class="flex items-center gap-2">
                <span class="badge badge-sm w-20 text-white" style="background-color: ${colorStyle.bg}">${label}</span>
                <div class="flex-1 bg-base-200 rounded-full h-5 overflow-hidden">
                    <div class="h-full rounded-full transition-all duration-500 flex items-center justify-end pr-2" style="width: ${Math.max(percent, 10)}%; background-color: ${colorStyle.bg}">
                        <span class="text-xs text-white font-bold">${value}</span>
                    </div>
                </div>
                <span class="text-xs w-12 text-right">${percent.toFixed(1)}%</span>
            </div>
        `;
    }
    html += '</div>';
    
    // Add donut summary
    const activePercent = total > 0 ? Math.round(data['Active']/total*100) : 0;
    html += `
        <div class="flex justify-center mt-4">
            <div class="radial-progress text-primary" style="--value:${activePercent}; --size:6rem; --thickness:8px;" role="progressbar">
                <span class="text-lg font-bold">${total}</span>
            </div>
        </div>
        <p class="text-center text-xs text-base-content/60 mt-2">Total Activities</p>
    `;
    
    container.innerHTML = html;
}

// User chart renderer
async function renderUserChart(containerId, data) {
    const container = document.getElementById(containerId);
    const maxValue = Math.max(...Object.values(data));
    
    let html = '<div class="space-y-2 w-full">';
    
    for (const [userId, value] of Object.entries(data)) {
        let userName = 'Unknown';
        try {
            const user = await promiseUserById(parseInt(userId));
            if (user) {
                userName = `${user.FirstName} ${user.LastName}`;
            }
        } catch (e) {}
        
        const percent = maxValue > 0 ? (value / maxValue * 100) : 0;
        html += `
            <div class="flex items-center gap-2">
                <span class="text-xs w-28 truncate" title="${escapeHtml(userName)}">${escapeHtml(userName)}</span>
                <div class="flex-1 bg-base-200 rounded-full h-4 overflow-hidden">
                    <div class="h-full rounded-full transition-all duration-500" style="width: ${percent}%; background-color: #14b8a6"></div>
                </div>
                <span class="text-xs font-bold w-8 text-right">${value}</span>
            </div>
        `;
    }
    html += '</div>';
    container.innerHTML = html;
}

function editpipeline(pipelineId) {
    createModalPopup(pipelineId);
}

function deletepipeline(pipelineId) {
    deletePipelineId = pipelineId;
    const modal = document.getElementById('deletePipelineModal');
    const confirmBtn = document.getElementById('deletePipelineBtn');
    
    // Show pipeline name in the confirmation dialog
    const pipeline = pipelineCache.find(p => p.Id === pipelineId);
    const titleDisplay = document.getElementById('deletePipelineTitleDisplay');
    if (titleDisplay) titleDisplay.value = pipeline ? (pipeline.PipelineName || pipeline.Name) : '';
    
    confirmBtn.onclick = function() {
        deletePipelineRequest(deletePipelineId);
        modal.close();
    };
    
    modal.showModal();
}

function getUniqueLeads(leads) {
    if (!leads) return [];
    const uniqueLeads = leads.reduce((acc, lead) => {
        if (!acc.some(existingLead => existingLead.Id === lead.Id)) {
            acc.push(lead);
        }
        return acc;
    }, []);
    return uniqueLeads;
}

function createModalPopup(pipelineId = null) {
    pipelineIdCache = pipelineId;
    const modal = document.getElementById('pipelineModal');
    const titleInput = document.getElementById('pipelineTitle');
    const orderInput = document.getElementById('pipelineOrder');
    const modalTitle = document.getElementById('pipelineModalTitle');
    const actionText = document.getElementById('pipelineActionText');
    
    // Reset form
    titleInput.value = '';
    orderInput.value = '0';
    
    if (pipelineId) {
        // Edit mode
        const pipeline = pipelineCache.find(p => p.Id === pipelineId);
        if (pipeline) {
            titleInput.value = pipeline.PipelineName || pipeline.Name || '';
            orderInput.value = pipeline.Order || 0;
        }
        modalTitle.textContent = 'Edit Pipeline';
        actionText.textContent = 'Update';
    } else {
        // Create mode
        modalTitle.textContent = 'Add Pipeline';
        actionText.textContent = 'Create';
    }
    
    modal.showModal();
}

function createCRMPipeline() {
    createPipelineRequest(pipelineIdCache);
    document.getElementById('pipelineModal').close();
}

function deletePipelineRequest(pipelineId) {
    const token = readToken();
    const xhr = new XMLHttpRequest();
    xhr.open('POST', url + '/biomedapi/v2/project/pipelines/delete', true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.setRequestHeader('Authorization', `Bearer ${token}`);
    xhr.onreadystatechange = function() {
        if (xhr.readyState === XMLHttpRequest.DONE) {
            if (xhr.status === 200) {
                xalert('Pipeline deleted successfully', 0, -1);
                // Clear project cache before reload
                sessionStorage.removeItem('project:' + projectId);
                sessionStorage.removeItem('projects');
                setTimeout(function() {
                    location.reload();
                }, 1000);
            } else {
                xalert('Error ' + xhr.status + " " + xhr.responseText, 1, -1);
            }
        }
    };
    const data = JSON.stringify({Id: pipelineId});
    xhr.send(data);
}

function createPipelineRequest(pipelineId = null) {
    const token = readToken();
    const name = document.getElementById('pipelineTitle').value;
    const order = parseInt(document.getElementById('pipelineOrder').value) || 0;
    
    if (!name.trim()) {
        xalert('Please enter a pipeline name', 2, 3000);
        return;
    }

    const xhr = new XMLHttpRequest();
    if (pipelineId) {
        xhr.open('POST', url + '/biomedapi/v2/project/pipelines/update', true);
    } else {
        xhr.open('POST', url + '/biomedapi/v2/project/pipelines/create', true);
    }
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.setRequestHeader('Authorization', `Bearer ${token}`);
    xhr.onreadystatechange = function() {
        if (xhr.readyState === XMLHttpRequest.DONE) {
            if (xhr.status === 200) {
                xalert('Pipeline ' + (pipelineId ? 'updated' : 'created') + ' successfully', 0, -1);
                // Clear project cache before reload
                sessionStorage.removeItem('project:' + projectId);
                sessionStorage.removeItem('projects');
                setTimeout(function() {
                    location.reload();
                }, 1000);
            } else {
                xalert('Error ' + xhr.status + " " + xhr.responseText, 1, -1);
            }
        }
    };
    
    let rawdata = {
        ProjectId: parseInt(projectId),
        Name: name,
        Description: "Just a Placeholder",
        Order: order
    };
    if (pipelineId) {
        rawdata.Id = pipelineId;
    }
    
    const data = JSON.stringify(rawdata);
    xhr.send(data);
}

// Activity Modal Functions
function createLeadPopup() {
    const modal = document.getElementById('leadModal');
    const dropdown = document.getElementById('pipelineDropdown');
    
    // Clear and populate dropdown
    dropdown.innerHTML = '';
    pipelineCache.forEach(pipeline => {
        const option = document.createElement('option');
        option.value = pipeline.Id;
        option.textContent = pipeline.PipelineName || pipeline.Name;
        dropdown.appendChild(option);
    });
    
    // Reset form
    document.getElementById('leadName').value = '';
    
    modal.showModal();
}

function createLead() {
    createLeadRequest();
    document.getElementById('leadModal').close();
}

function createLeadRequest() {
    const token = readToken();
    const leadName = document.getElementById('leadName').value;
    const pipelineId = document.getElementById('pipelineDropdown').value;
    
    if (!leadName.trim()) {
        xalert('Please enter an activity name', 2, 3000);
        return;
    }

    const xhr = new XMLHttpRequest();
    xhr.open('POST', url + '/biomedapi/v2/project/activities/create', true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.setRequestHeader('Authorization', `Bearer ${token}`);
    xhr.onreadystatechange = function() {
        if (xhr.readyState === XMLHttpRequest.DONE) {
            if (xhr.status === 200) {
                xalert('Activity created successfully', 0, -1);
                // Clear project cache
                sessionStorage.removeItem('project:' + projectId);
                sessionStorage.removeItem('projects');
                setTimeout(() => {
                    const leadId = xhr.responseText;
                    window.location.href = `./project-activity.html?activityid=${leadId}`;
                }, 2000);
            } else {
                xalert('Error ' + xhr.status + " " + xhr.responseText, 1, -1);
            }
        }
    };
    
    let rawdata = {
        Name: leadName,
        Description: "Just a Placeholder",
        PipelineId: pipelineId
    };
    
    const data = JSON.stringify(rawdata);
    xhr.send(data);
}

// Create lead for specific pipeline (from + button)
function createLeadPopupForPipeline(pipelineId) {
    const modal = document.getElementById('leadModal');
    const dropdown = document.getElementById('pipelineDropdown');
    
    // Clear and populate dropdown
    dropdown.innerHTML = '';
    pipelineCache.forEach(pipeline => {
        const option = document.createElement('option');
        option.value = pipeline.Id;
        option.textContent = pipeline.PipelineName || pipeline.Name;
        if (pipeline.Id === pipelineId) {
            option.selected = true;
        }
        dropdown.appendChild(option);
    });
    
    // Reset form
    document.getElementById('leadName').value = '';
    
    modal.showModal();
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function renderPipelineColumn(pipeline) {
    const column = document.createElement('div');
    column.className = 'kanban-column';
    column.id = `pipeline-${pipeline.Id}`;
    
    // Calculate activity count
    const activityCount = (pipeline.Activities || []).length;
    
    column.innerHTML = `
        <div class="bg-base-100 rounded-xl shadow-md h-full flex flex-col overflow-hidden border border-base-200">
            <!-- Pipeline Header - Purple Background -->
            <div class="bg-primary text-primary-content px-4 py-3">
                <div class="flex items-center justify-between">
                    <div class="flex-1 min-w-0">
                        <h3 class="font-bold text-sm truncate">${escapeHtml(pipeline.PipelineName || pipeline.Name)}</h3>
                        <p class="text-xs opacity-80 mt-0.5"><span id="count${pipeline.Id}">${activityCount}</span> รายการ</p>
                    </div>
                    <div class="dropdown dropdown-end">
                        <div tabindex="0" role="button" class="btn btn-ghost btn-xs btn-circle text-primary-content hover:bg-white/20">
                            <i class="fa-solid fa-ellipsis-vertical"></i>
                        </div>
                        <ul tabindex="0" class="dropdown-content z-[10] menu p-2 shadow-lg bg-base-100 text-base-content rounded-box w-40">
                            <li><a onclick="editpipeline(${pipeline.Id})"><i class="fa-solid fa-pen mr-2"></i>Edit</a></li>
                            <li><a onclick="deletepipeline(${pipeline.Id})" class="text-error"><i class="fa-solid fa-trash mr-2"></i>Delete</a></li>
                        </ul>
                    </div>
                </div>
                
                <!-- Status Badges -->
                <div class="flex flex-wrap gap-1.5 mt-2">
                    <span class="badge badge-sm gap-1 bg-error/90 border-0 text-white">
                        <i class="fi fi-rr-ban text-[10px]"></i>
                        <span id="abandon${pipeline.Id}">0</span>
                    </span>
                    <span class="badge badge-sm gap-1 bg-warning/90 border-0 text-white">
                        <i class="fi fi-rr-triangle-warning text-[10px]"></i>
                        <span id="warn${pipeline.Id}">0</span>
                    </span>
                    <span class="badge badge-sm gap-1 bg-success/90 border-0 text-white">
                        <i class="fi fi-rr-signal-bars-good text-[10px]"></i>
                        <span id="ok${pipeline.Id}">0</span>
                    </span>
                </div>
            </div>
            
            <!-- Activities Container -->
            <div class="flex-1 overflow-y-auto p-3 bg-base-200/50 min-h-0">
                <div class="space-y-3" id="activities-${pipeline.Id}">
                    <!-- Activity cards will be inserted here -->
                </div>
            </div>
            
            <!-- Add Activity Button - Centered -->
            <div class="p-3 border-t border-base-200 bg-base-100">
                <button class="btn btn-ghost btn-sm w-full justify-center text-base-content/60 hover:text-primary" onclick="createLeadPopupForPipeline(${pipeline.Id})">
                    <i class="fa-solid fa-plus mr-2"></i>
                    เพิ่มรายการ
                </button>
            </div>
        </div>
    `;
    
    return column;
}

function renderActivityCard(activity, color, user) {
    const card = document.createElement('div');
    const userColor = color?.color?.code || '#f97316'; // Default orange
    
    card.className = 'bg-white rounded-lg shadow-sm cursor-pointer hover:shadow-md transition-all duration-200 overflow-hidden';
    card.style.borderLeft = `4px solid ${userColor}`;
    
    const activityLink = `./project-activity.html?activityid=${activity.Id}`;
    
    // Determine status badge
    const thirtyDaysAgo = new Date();
    thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
    
    const threeMonthsAgo = new Date();
    threeMonthsAgo.setDate(threeMonthsAgo.getDate() - 90);
    
    let statusBadge = '';
    let statusColor = 'bg-success';
    
    const lastUpdate = new Date(activity.Update || activity.Creation);
    if (lastUpdate < threeMonthsAgo) {
        statusBadge = '<span class="badge badge-error badge-sm text-white"><i class="fi fi-rr-ban"></i></span>';
        statusColor = 'error';
    } else if (lastUpdate < thirtyDaysAgo) {
        statusBadge = '<span class="badge badge-warning badge-sm text-white"><i class="fi fi-rr-triangle-warning"></i></span>';
        statusColor = 'warning';
    } else {
        statusBadge = '<span class="badge badge-success badge-sm text-white"><i class="fi fi-rr-check"></i></span>';
        statusColor = 'success';
    }
    
    const userName = user ? `${user.FirstName} ${user.LastName}` : 'Unknown';
    
    // Format date in Thai style
    const updateDate = activity.Update || activity.Creation;
    let formattedDate = '';
    if (updateDate) {
        const d = new Date(updateDate);
        const day = d.getDate();
        const thaiMonths = ['ม.ค.', 'ก.พ.', 'มี.ค.', 'เม.ย.', 'พ.ค.', 'มิ.ย.', 'ก.ค.', 'ส.ค.', 'ก.ย.', 'ต.ค.', 'พ.ย.', 'ธ.ค.'];
        const thaiYear = d.getFullYear() + 543;
        formattedDate = `Due: ${day} ${thaiMonths[d.getMonth()]} ${thaiYear}`;
    }
    
    card.innerHTML = `
        <div class="p-3">
            <!-- Header Row with Status Badge -->
            <div class="flex items-start justify-between gap-2 mb-2">
                <div class="flex items-center gap-2 flex-1 min-w-0">
                    ${statusBadge}
                    <h4 class="font-bold text-sm text-base-content">${escapeHtml(activity.Name)}</h4>
                </div>
                <div class="dropdown dropdown-end">
                    <div tabindex="0" role="button" class="btn btn-ghost btn-xs btn-circle">
                        <i class="fa-solid fa-ellipsis-vertical text-base-content/40"></i>
                    </div>
                    <ul tabindex="0" class="dropdown-content z-[10] menu p-2 shadow-lg bg-base-100 rounded-box w-36">
                        <li><a href="${activityLink}"><i class="fa-solid fa-pen mr-2"></i>Edit</a></li>
                    </ul>
                </div>
            </div>
            
            <!-- Description -->
            <p class="text-xs text-base-content/70 mb-2">${escapeHtml(activity.Description || 'Just a Placeholder')}</p>
            
            <!-- Date Row -->
            <p class="text-xs text-base-content/60 mb-2">${formattedDate}</p>
            
            <!-- User Badge Row -->
            <div class="mt-2">
                <span class="badge badge-outline badge-sm" style="border-color: ${userColor}; color: ${userColor}">${escapeHtml(userName)}</span>
            </div>
        </div>
    `;
    
    // Make card clickable
    card.addEventListener('click', (e) => {
        if (!e.target.closest('.dropdown')) {
            window.location.href = activityLink;
        }
    });
    
    return card;
}

async function displayLeads() {
    if (!projectId) {
        xalert('Error: Missing Project ID. Please check URL', 1, -1);
        return;
    }
    
    const pipelineContainer = document.getElementById('pipelineContainer');
    pipelineContainer.innerHTML = '<div class="flex items-center justify-center p-8"><span class="loading loading-spinner loading-lg text-primary"></span></div>';
    
    getProjectById(projectId, async function(error, project) {
        if (error) {
            xalert('Error loading project: ' + error, 1, -1);
            return;
        }
        
        document.getElementById('projectName').textContent = project.Name;
        projectCache = project;
        
        const pipelines = project.Pipelines || [];
        pipelines.sort((a, b) => (a.Order || 0) - (b.Order || 0));
        
        // Store pipeline cache with proper naming
        pipelineCache = pipelines.map(p => ({
            ...p,
            PipelineName: p.Name
        }));
        
        // Cache all activities for table/viz views
        allActivitiesCache = [];
        pipelines.forEach(p => {
            const activities = getUniqueLeads(p.Activities);
            activities.forEach(a => {
                a.PipelineId = p.Id; // Store pipeline ID in activity
                allActivitiesCache.push(a);
            });
        });
        
        pipelineContainer.innerHTML = '';
        
        if (pipelines.length === 0) {
            pipelineContainer.innerHTML = `
                <div class="flex flex-col items-center justify-center py-16 w-full">
                    <div class="w-16 h-16 bg-base-200 rounded-full flex items-center justify-center mb-4">
                        <i class="fi fi-rr-columns text-3xl text-base-content/40"></i>
                    </div>
                    <h3 class="text-lg font-semibold mb-2">No Pipelines Yet</h3>
                    <p class="text-sm text-base-content/60 mb-4">Create your first pipeline to organize activities</p>
                    <button class="btn btn-primary btn-sm" onclick="createModalPopup()">
                        <i class="fa-solid fa-plus mr-2"></i>
                        Add Pipeline
                    </button>
                </div>
            `;
            return;
        }
        
        // Render each pipeline
        for (const pipeline of pipelines) {
            const column = renderPipelineColumn(pipeline);
            pipelineContainer.appendChild(column);
            
            const activities = getUniqueLeads(pipeline.Activities);
            const activitiesContainer = column.querySelector(`#activities-${pipeline.Id}`);
            
            let activeCount = 0;
            let warnCount = 0;
            let abandonCount = 0;
            
            // Show empty state if no activities
            if (activities.length === 0) {
                activitiesContainer.innerHTML = `
                    <div class="flex flex-col items-center justify-center py-8 text-center">
                        <div class="w-12 h-12 bg-base-200 rounded-full flex items-center justify-center mb-3">
                            <i class="fi fi-rr-inbox-out text-2xl text-base-content/30"></i>
                        </div>
                        <p class="text-sm text-base-content/40">ไม่มีรายการ</p>
                    </div>
                `;
            }
            
            for (const activity of activities) {
                try {
                    // Get user and color
                    const user = await promiseUserById(activity.MainUserId);
                    const color = await getColor(activity.MainUserId);
                    
                    // Calculate status
                    const thirtyDaysAgo = new Date();
                    thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
                    
                    const threeMonthsAgo = new Date();
                    threeMonthsAgo.setDate(threeMonthsAgo.getDate() - 90);
                    
                    const lastUpdate = new Date(activity.Update || activity.Creation);
                    if (lastUpdate < threeMonthsAgo) {
                        abandonCount++;
                    } else if (lastUpdate < thirtyDaysAgo) {
                        warnCount++;
                    } else {
                        activeCount++;
                    }
                    
                    const card = renderActivityCard(activity, color, user);
                    activitiesContainer.appendChild(card);
                } catch (err) {
                    console.error('Error rendering activity:', err);
                    // Render card without user info
                    const card = renderActivityCard(activity, null, null);
                    activitiesContainer.appendChild(card);
                }
            }
            
            // Update status counts
            document.getElementById(`ok${pipeline.Id}`).textContent = activeCount;
            document.getElementById(`warn${pipeline.Id}`).textContent = warnCount;
            document.getElementById(`abandon${pipeline.Id}`).textContent = abandonCount;
        }
        
    }, true);
}

window.onload = function() {
    if (urlParams.has('projectId')) {
        displayLeads();
    } else {
        xalert('Error: Missing Project ID. Please check URL', 1, -1);
    }
};
