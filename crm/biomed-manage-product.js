/**
 * biomed-manage-product.js
 * Product Management with daisyUI Timeline
 * Replaces Google Charts Timeline with native daisyUI timeline component
 */

const urlParams = new URLSearchParams(window.location.search);
const id = urlParams.get('id');

// ============================================
// Quarter Mode: 'fiscal' (FYQ) or 'standard' (YQ)
// Shared localStorage key with CRM/Helpdesk
// ============================================
let targetQuarterMode = localStorage.getItem('crmQuarterMode') || 'fiscal';

/**
 * Get the year button label prefix based on current mode
 */
function getYearPrefix() {
    return targetQuarterMode === 'fiscal' ? 'FY' : 'Y';
}

/**
 * Switch quarter mode and update all existing target cards
 */
function setTargetQuarterMode(mode) {
    targetQuarterMode = mode;
    localStorage.setItem('crmQuarterMode', mode);

    // Update toggle button UI
    const btnFYQ = document.getElementById('targetBtnFYQ');
    const btnYQ = document.getElementById('targetBtnYQ');
    const desc = document.getElementById('targetQuarterModeDesc');
    if (mode === 'fiscal') {
        btnFYQ?.classList.add('btn-active');
        btnYQ?.classList.remove('btn-active');
        if (desc) desc.textContent = 'Fiscal Year';
    } else {
        btnFYQ?.classList.remove('btn-active');
        btnYQ?.classList.add('btn-active');
        if (desc) desc.textContent = 'Calendar Year';
    }

    // Update all existing year button labels
    const prefix = getYearPrefix();
    document.querySelectorAll('[id*="CreationFY"]').forEach(btn => {
        const yearVal = btn.getAttribute('internalValue');
        if (yearVal) btn.setAttribute('aria-label', prefix + yearVal);
    });
}

/**
 * Get quarter date range based on current quarter mode
 * In fiscal mode: uses global getQuarterDateRange (Q1=May-Jul)
 * In standard mode: Q1=Jan-Mar, Q2=Apr-Jun, Q3=Jul-Sep, Q4=Oct-Dec
 */
function getTargetQuarterDateRange(quarter, year) {
    if (targetQuarterMode === 'fiscal') {
        // Use the global fiscal getQuarterDateRange from biomed-global.js
        return getQuarterDateRange(quarter, year);
    }
    // Standard calendar year quarters
    const fullYear = 2000 + parseInt(year);
    const startMonth = (quarter - 1) * 3;
    const endMonth = startMonth + 2;
    const startDate = new Date(fullYear, startMonth, 1);
    const endDate = new Date(fullYear, endMonth + 1, 0);
    endDate.setHours(23, 59, 59);
    return { startDate, endDate };
}

window.onload = function() {
    if (!id) {
        xalert("No id please check your url", 1, null);
        return;
    }
    
    // Restore quarter mode toggle UI
    setTargetQuarterMode(targetQuarterMode);
    
    // Update product ID badge
    document.getElementById('productIdBadge').textContent = 'ID: ' + id;
    
    // Make a request to biomedapi/products/{id}
    getProductById(id, function(error, product) {
        if (error) {
            console.error('Failed to retrieve product:', error);
            xalert("Failed to retrieve product", 1, null);
            return;
        }
        
        document.getElementById('productName').value = product.Name;
        document.getElementById('productDescription').value = product.Description;
        document.getElementById('breadcrumbProductName').textContent = product.Name;
        
        // Get Sale Areas
        getSaleAreas(function(error, saleAreas) {
            if(error) {
                console.error('Failed to retrieve sale areas:', error);
                xalert("Failed to retrieve sale areas", 1, null);
                return;
            }
            
            const saleAreasBox = document.getElementById('SaleAreaList');
            saleAreasBox.innerHTML = ''; // Clear loading state
            
            saleAreas.forEach(function(saleArea) {
                console.log(saleArea);
                
                const saleAreaBox = document.createElement('div');
                saleAreaBox.classList.add('flex', 'rounded-lg', 'border', 'border-base-300', 'bg-base-50', 'min-h-[280px]', 'overflow-hidden');
                saleAreaBox.innerHTML = `
                    <div class="w-12 flex-shrink-0 bg-base-200 flex items-center justify-center border-r border-base-300">
                        <span class="area-label font-semibold text-base-content/80 text-sm whitespace-nowrap">${saleArea.Name}</span>
                    </div>
                    <div class="flex-1 p-3 overflow-x-auto flex gap-3 targets-scroll" id="areaBox${saleArea.Id}">
                        <!-- Target cards will be inserted here -->
                    </div>
                    <div class="w-12 flex-shrink-0 bg-base-200 flex items-center justify-center border-l border-base-300 cursor-pointer hover:bg-primary hover:text-primary-content transition-colors"
                         onclick="createNewTarget(${saleArea.Id},'${saleArea.Name}')">
                        <i class="fas fa-plus text-xl"></i>
                    </div>
                `;
                saleAreasBox.appendChild(saleAreaBox);
                
                // Query targets for this sale area
                var query = {
                    ProductIDs: [id],
                    SaleAreaIDs: [saleArea.Id]
                };
                
                getTargets(function(error, targets) {
                    if(error) {
                        console.error('Failed to retrieve targets:', error);
                        xalert("Failed to retrieve targets", 1, null);
                        return;
                    }
                    console.log(targets);
                    targets.forEach(function(target) {
                        createNewTarget(saleArea.Id, saleArea.Name, target.Id, target);
                    });
                }, query);
            });

        }, true);
    });
    
    // Draw the timeline
    drawTimeline();
}

function saveGroup() {
    const data = {
        Name: document.getElementById('productName').value,
        id: id,
        Description: document.getElementById('productDescription').value
    };

    updateProduct(data, function(error, response) {
        if (error) {
            console.error('Failed to update product:', error);
            xalert("Failed to update product", 1, null);
            return;
        }
        console.log('product updated successfully:', response);
        xalert("Product updated successfully", 0, null);
        document.getElementById('breadcrumbProductName').textContent = data.Name;
    });
}

function updateProduct(data, callback) {
    const xhr = new XMLHttpRequest();
    xhr.open('POST', url + '/biomedapi/products/update');
    xhr.setRequestHeader('Authorization', `Bearer ${readToken()}`);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.onload = function() {
        if (xhr.status === 200) {
            callback(null, xhr.responseText);
        } else {
            callback('Failed to update product', null);
        }
    };
    xhr.onerror = function() {
        callback('Failed to send request', null);
    };
    xhr.send(JSON.stringify(data));
}

function deleteProduct() {
    // Show daisyUI style confirmation modal
    if (!confirm("Are you sure you want to delete this product?")) return;
    
    const xhr = new XMLHttpRequest();
    xhr.open('POST', url + '/biomedapi/products/delete');
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.setRequestHeader('Authorization', `Bearer ${readToken()}`);
    xhr.onload = function() {
        if (xhr.status === 200) {
            xalert("Product deleted successfully", 0, null);
            setTimeout(() => {
                window.location.href = 'management.html';
            }, 1500);
        } else {
            xalert("Failed to delete product", 1, null);
        }
    };
    xhr.onerror = function() {
        xalert("Failed to send request", 1, null);
    };
    xhr.send(JSON.stringify({id: id}));
}

let internalCounter = 0;

function createNewTarget(boxId, saleAreaName, targetId = "New", target = null) {
    internalCounter++;
    const currentCounter = internalCounter;
    const areaBox = document.getElementById('areaBox' + boxId);
    
    const newTarget = document.createElement('div');
    newTarget.id = "miniBox" + currentCounter;
    newTarget.classList.add('target-card', 'card', 'card-bordered', 'bg-base-100', 'shadow-sm', 'flex-shrink-0', 'w-[420px]');
    newTarget.targetId = targetId;
    
    newTarget.innerHTML = `
        <div class="card-body p-4">
            <div class="flex items-center justify-between mb-2">
                <h3 class="card-title text-sm">
                    <span class="badge badge-outline">${saleAreaName}</span>
                    <span class="text-base-content/60">#${targetId}</span>
                </h3>
                <div class="flex gap-1">
                    <button class="btn btn-success btn-xs btn-circle" onclick="createNewTargetRequest('${targetId}','${currentCounter}',${boxId},'${saleAreaName}')" title="Save">
                        <i class="fas fa-check"></i>
                    </button>
                    <button class="btn btn-error btn-xs btn-circle" onclick="deleteTargetRequest('${targetId}',${currentCounter})" title="Delete">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>
            
            <fieldset class="fieldset">
                <legend class="fieldset-legend text-xs">Target Note</legend>
                <input type="text" class="input input-bordered input-sm w-full" id="note${currentCounter}" placeholder="Enter note">
            </fieldset>
            
            <div class="grid grid-cols-2 gap-2 mt-2">
                <fieldset class="fieldset">
                    <legend class="fieldset-legend text-xs">Start Date</legend>
                    <input type="datetime-local" id="targetStartDate${currentCounter}" class="input input-bordered input-sm w-full">
                </fieldset>
                <fieldset class="fieldset">
                    <legend class="fieldset-legend text-xs">End Date</legend>
                    <input type="datetime-local" id="targetEndDate${currentCounter}" class="input input-bordered input-sm w-full">
                </fieldset>
            </div>
            
            <div class="mt-2">
                <fieldset class="fieldset">
                    <legend class="fieldset-legend text-xs">Quick Date Selection</legend>
                    <div class="flex flex-wrap gap-1" id="QuarterYear${currentCounter}">
                        <!-- Quarter buttons -->
                        <div class="join">
                            <input class="join-item btn btn-xs" type="radio" name="CreationQuarter${currentCounter}" aria-label="Q1" internalValue="Q1" id="${currentCounter}CreationQuarter1" onclick="ChangeQ(1,${currentCounter})">
                            <input class="join-item btn btn-xs" type="radio" name="CreationQuarter${currentCounter}" aria-label="Q2" internalValue="Q2" id="${currentCounter}CreationQuarter2" onclick="ChangeQ(2,${currentCounter})">
                            <input class="join-item btn btn-xs" type="radio" name="CreationQuarter${currentCounter}" aria-label="Q3" internalValue="Q3" id="${currentCounter}CreationQuarter3" onclick="ChangeQ(3,${currentCounter})">
                            <input class="join-item btn btn-xs" type="radio" name="CreationQuarter${currentCounter}" aria-label="Q4" internalValue="Q4" id="${currentCounter}CreationQuarter4" onclick="ChangeQ(4,${currentCounter})">
                        </div>
                        
                        <button class="btn btn-xs btn-ghost" onclick="clearRadioSelection(this,${currentCounter})" title="Clear">
                            <i class="fas fa-eraser"></i>
                        </button>
                        
                        <!-- Year buttons (auto-derived: prev/curr/next 2-digit short) -->
                        <div class="join">
                            ${(function () {
                                var c = new Date().getFullYear() - 2000;
                                return [c - 1, c, c + 1].map(function (n) {
                                    var y = String(n).padStart(2, '0');
                                    return `<input class="join-item btn btn-xs" type="radio" name="CreationFY${currentCounter}" aria-label="${getYearPrefix()}${y}" internalValue="${y}" id="${currentCounter}CreationFY${y}" onclick="ChangeY('${y}',${currentCounter})">`;
                                }).join('');
                            })()}
                        </div>
                    </div>
                </fieldset>
            </div>
            
            <fieldset class="fieldset mt-2">
                <legend class="fieldset-legend text-xs">Target Value (THB)</legend>
                <input type="number" class="input input-bordered input-sm w-full" id="targetValue${currentCounter}" placeholder="0">
            </fieldset>
        </div>
    `;

    areaBox.insertBefore(newTarget, areaBox.firstChild);
    
    // Set values
    const note = document.getElementById('note' + currentCounter);
    const startDate = document.getElementById('targetStartDate' + currentCounter);
    const endDate = document.getElementById('targetEndDate' + currentCounter);
    const targetValue = document.getElementById('targetValue' + currentCounter);
    
    if(target == null) {
        note.value = "";
        startDate.value = timeFuck(new Date().toISOString().split("T")[0] + "T00:00");
        endDate.value = timeFuck(new Date().toISOString().split("T")[0] + "T23:59");
        targetValue.value = 0;
    } else {
        note.value = target.Name;
        startDate.value = timeFuck(target.StartDate);
        endDate.value = timeFuck(target.EndDate);
        targetValue.value = target.TargetValue;
    }
}

function ChangeQ(q, internalCounter) {
    const startDate = document.getElementById('targetStartDate' + internalCounter);
    const endDate = document.getElementById('targetEndDate' + internalCounter);

    const quarterYearElement = document.getElementById('QuarterYear' + internalCounter);
    const selectedQuarter = quarterYearElement.querySelector('input[name="CreationQuarter' + internalCounter + '"]:checked');
    const selectedFY = quarterYearElement.querySelector('input[name="CreationFY' + internalCounter + '"]:checked');
    let quarterValue = selectedQuarter ? selectedQuarter.getAttribute('internalValue') : null;
    let fyValue = selectedFY ? selectedFY.getAttribute('internalValue') : null;

    if (!selectedQuarter) {
        const defaultQuarter = document.getElementById(internalCounter + 'CreationQuarter' + q);
        defaultQuarter.checked = true;
        quarterValue = 'Q' + q;
    }
    if (!selectedFY) {
        const defaultFY = document.getElementById(internalCounter + 'CreationFY25');
        defaultFY.checked = true;
        fyValue = '25';
    }

    const dateRange = getTargetQuarterDateRange(q, fyValue);
    startDate.value = timeFuck(dateRange.startDate);
    endDate.value = timeFuck(new Date(dateRange.endDate).getTime());
    console.log("StartDate", startDate.value);
    console.log("EndDate", endDate.value);
    console.log('Selected quarter:', q);
    console.log('Selected FY:', fyValue);
}

function ChangeY(y, internalCounter) {
    const startDate = document.getElementById('targetStartDate' + internalCounter);
    const endDate = document.getElementById('targetEndDate' + internalCounter);

    const quarterYearElement = document.getElementById('QuarterYear' + internalCounter);
    const selectedQuarter = quarterYearElement.querySelector('input[name="CreationQuarter' + internalCounter + '"]:checked');
    const selectedFY = quarterYearElement.querySelector('input[name="CreationFY' + internalCounter + '"]:checked');
    let quarterValue = selectedQuarter ? selectedQuarter.getAttribute('internalValue') : null;
    let fyValue = selectedFY ? selectedFY.getAttribute('internalValue') : null;

    if (!selectedQuarter) {
        const defaultQuarter = document.getElementById(internalCounter + 'CreationQuarter1');
        defaultQuarter.checked = true;
        quarterValue = 'Q1';
    }
    if (!selectedFY) {
        const defaultFY = document.getElementById(internalCounter + 'CreationFY25');
        defaultFY.checked = true;
        fyValue = y;
    }

    const dateRange = getTargetQuarterDateRange(parseInt(quarterValue.replace('Q', '')), y);
    startDate.value = timeFuck(dateRange.startDate);
    endDate.value = timeFuck(new Date(dateRange.endDate).getTime());
    console.log("StartDate", startDate.value);
    console.log("EndDate", endDate.value);
    console.log('Selected quarter:', quarterValue);
    console.log('Selected FY:', y);
}

function clearRadioSelection(e, internalCounter) {
    const parentElement = e.closest('#QuarterYear' + internalCounter);
    const radioButtons = parentElement.querySelectorAll('input[type="radio"]');
    radioButtons.forEach(radioButton => {
        radioButton.checked = false;
    });
    const startDate = document.getElementById('targetStartDate' + internalCounter);
    const endDate = document.getElementById('targetEndDate' + internalCounter);
    const today = new Date();
    startDate.value = timeFuck(today);
    endDate.value = timeFuck(today);
}

function createNewTargetRequest(targetId, internalCounter, saleAreaId, saleAreaName) {
    const startDate = document.getElementById('targetStartDate' + internalCounter).value;
    const endDate = document.getElementById('targetEndDate' + internalCounter).value;
    const targetValue = document.getElementById('targetValue' + internalCounter).value;
    const note = document.getElementById('note' + internalCounter).value;
    const xhr = new XMLHttpRequest();
    
    if(targetId == "New" || targetId == null || targetId == "" || targetId == undefined) {
        // Create New
        var data = {
            Name: note,
            StartDate: timeFormater(startDate),
            EndDate: timeFormater(endDate),
            TargetValue: targetValue,
            ProductId: id,
            SaleAreaId: saleAreaId
        };
        xhr.open('POST', url + '/biomedapi/targets/create');
    } else {
        // Update
        var data = {
            Name: note,
            StartDate: timeFormater(startDate),
            EndDate: timeFormater(endDate),
            TargetValue: targetValue,
            Id: targetId
        };
        xhr.open('POST', url + '/biomedapi/targets/update');
    }
    
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.setRequestHeader('Authorization', `Bearer ${readToken()}`);
    xhr.onload = function() {
        if (xhr.status === 200) {
            console.log('target created successfully:', xhr.responseText);
            var miniBox = document.getElementById('miniBox' + internalCounter);
            miniBox.remove();
            var response = JSON.parse(xhr.responseText);
            createNewTarget(saleAreaId, saleAreaName, response.Id, response);
            xalert("Target saved successfully", 0, 1000);
            // Refresh timeline
            reloadTimeline();
        } else {
            console.error('Failed to create target:', xhr.responseText);
            xalert("Failed to save target", 1, null);
        }
    };
    xhr.onerror = function() {
        xalert('Failed to send request', 1, null);
    };
    xhr.send(JSON.stringify(data));
}

function deleteTargetRequest(requestId, internalCounter) {
    if(requestId == "New" || requestId == null || requestId == "" || requestId == undefined) {
        var miniBox = document.getElementById('miniBox' + internalCounter);
        miniBox.remove();
    } else {
        if (confirm("Are you sure you want to delete the target with id: " + requestId + "?")) {
            const xhr = new XMLHttpRequest();
            xhr.open('POST', url + '/biomedapi/targets/delete');
            xhr.setRequestHeader('Content-Type', 'application/json');
            xhr.setRequestHeader('Authorization', `Bearer ${readToken()}`);
            xhr.onload = function() {
                if (xhr.status === 200) {
                    console.log('Target deleted successfully:', xhr.responseText);
                    var miniBox = document.getElementById('miniBox' + internalCounter);
                    miniBox.remove();
                    xalert("Target deleted successfully", 0, 1000);
                    // Refresh timeline
                    reloadTimeline();
                } else {
                    console.error('Failed to delete target:', xhr.responseText);
                    xalert("Failed to delete target", 1, null);
                }
            };
            xhr.onerror = function() {
                xalert('Failed to send request', 1, null);
            };
            xhr.send(JSON.stringify({ Id: requestId }));
        }
    }
}

// ===============================
// Gantt-style Timeline Functions
// ===============================

// Color palette for sale areas
const saleAreaColors = [
    '#3b82f6', // blue
    '#10b981', // green
    '#f59e0b', // amber
    '#ef4444', // red
    '#8b5cf6', // violet
    '#ec4899', // pink
    '#06b6d4', // cyan
    '#f97316', // orange
    '#84cc16', // lime
    '#6366f1', // indigo
];

function drawTimeline() {
    const timelineContainer = document.getElementById('timelineContainer');
    
    // Query all targets for this product
    var queryProduct = { ProductIDs: [id] };
    
    getTargets((err, targets) => {
        if (err) {
            console.log(err);
            xalert('Error: Failed to get targets', 1, -1);
            renderEmptyTimeline(timelineContainer);
            return;
        }
        
        if (!targets || targets.length === 0) {
            renderEmptyTimeline(timelineContainer);
            return;
        }
        
        // Get sale area names for all targets
        Promise.all(targets.map(target => {
            return getSaleAreaById(target.SaleAreaID)
                .then(saleArea => ({
                    ...target,
                    saleAreaName: saleArea.Name,
                    saleAreaId: target.SaleAreaID
                }))
                .catch(() => ({
                    ...target,
                    saleAreaName: 'Unknown',
                    saleAreaId: target.SaleAreaID
                }));
        })).then(enrichedTargets => {
            renderGanttTimeline(timelineContainer, enrichedTargets);
        });
        
    }, queryProduct);
}

function renderEmptyTimeline(container) {
    container.innerHTML = `
        <div class="flex flex-col items-center justify-center py-12 text-base-content/50">
            <i class="fas fa-chart-gantt text-4xl mb-3 opacity-30"></i>
            <p class="text-sm">No targets found</p>
            <p class="text-xs">Add targets to see them on the timeline</p>
        </div>
    `;
}

function renderGanttTimeline(container, targets) {
    // Group targets by Sale Area
    const groupedBySaleArea = {};
    const saleAreaOrder = [];
    
    targets.forEach(target => {
        const key = target.saleAreaId;
        if (!groupedBySaleArea[key]) {
            groupedBySaleArea[key] = {
                name: target.saleAreaName,
                targets: []
            };
            saleAreaOrder.push(key);
        }
        groupedBySaleArea[key].targets.push(target);
    });
    
    // Find date range for the entire timeline
    let minDate = new Date();
    let maxDate = new Date();
    
    targets.forEach(target => {
        const start = new Date(target.StartDate);
        const end = new Date(target.EndDate);
        if (start < minDate) minDate = start;
        if (end > maxDate) maxDate = end;
    });
    
    // Extend range to full months
    minDate = new Date(minDate.getFullYear(), minDate.getMonth(), 1);
    maxDate = new Date(maxDate.getFullYear(), maxDate.getMonth() + 1, 0);
    
    // Generate months array
    const months = [];
    let currentDate = new Date(minDate);
    while (currentDate <= maxDate) {
        months.push({
            date: new Date(currentDate),
            label: new Intl.DateTimeFormat('th-TH', { month: 'short', year: '2-digit' }).format(currentDate)
        });
        currentDate.setMonth(currentDate.getMonth() + 1);
    }
    
    // Calculate total timeline width in ms
    const totalMs = maxDate.getTime() - minDate.getTime();
    
    // Build HTML
    let html = `<div class="gantt-container">`;
    
    // Header with months
    html += `
        <div class="gantt-header rounded-t-lg">
            <div class="gantt-header-label">SALE AREA</div>
            <div class="gantt-header-months">
                ${months.map((m, i) => `<div class="gantt-month-cell${i % 2 === 0 ? ' bg-base-100/50' : ''}"><span class="gantt-month">${m.label}</span></div>`).join('')}
            </div>
        </div>
    `;
    
    // Rows for each Sale Area
    saleAreaOrder.forEach((saleAreaId, rowIndex) => {
        const saleArea = groupedBySaleArea[saleAreaId];
        const rowColor = saleAreaColors[rowIndex % saleAreaColors.length];
        
        html += `
            <div class="gantt-row">
                <div class="gantt-label" style="border-left: 4px solid ${rowColor};">
                    ${saleArea.name}
                </div>
                <div class="gantt-bars">
                    <div class="gantt-grid">
                        ${months.map((m, i) => `<div class="gantt-grid-line${i % 2 === 0 ? ' bg-base-200/30' : ''}"></div>`).join('')}
                    </div>
        `;
        
        // Add bars for each target
        saleArea.targets.forEach(target => {
            const startDate = new Date(target.StartDate);
            const endDate = new Date(target.EndDate);
            
            // Calculate position and width as percentage
            const leftPercent = ((startDate.getTime() - minDate.getTime()) / totalMs) * 100;
            const widthPercent = ((endDate.getTime() - startDate.getTime()) / totalMs) * 100;
            
            // Add small gap (0.3% on each side = 0.6% total gap)
            const gapPercent = 0.3;
            const adjustedLeft = leftPercent + gapPercent;
            const adjustedWidth = Math.max(widthPercent - (gapPercent * 2), 2);
            
            // Format value
            const formattedValue = new Intl.NumberFormat('th-TH', { 
                notation: 'compact',
                maximumFractionDigits: 1 
            }).format(target.TargetValue);
            
            // Format dates for tooltip
            const dateFormatter = new Intl.DateTimeFormat('th-TH', { 
                day: '2-digit', 
                month: 'short',
                year: '2-digit'
            });
            const formattedStart = dateFormatter.format(startDate);
            const formattedEnd = dateFormatter.format(endDate);
            const fullValue = new Intl.NumberFormat('th-TH').format(target.TargetValue);
            
            // Determine quarter label
            const quarter = getQuarterLabel(startDate, endDate);
            
            html += `
                <div class="gantt-bar tooltip tooltip-top" 
                     style="left: ${adjustedLeft}%; width: ${adjustedWidth}%; background: ${rowColor};"
                     data-tip="${saleArea.name}&#10;${target.Name || 'No note'}&#10;${formattedStart} - ${formattedEnd}&#10;${fullValue} THB">
                    <span class="truncate">${formattedValue}</span>
                </div>
            `;
        });
        
        html += `
                </div>
            </div>
        `;
    });
    
    html += `</div>`;
    
    container.innerHTML = html;
}

function getQuarterLabel(startDate, endDate) {
    // Try to determine if this is a quarter target
    const startMonth = startDate.getMonth();
    const endMonth = endDate.getMonth();
    const year = startDate.getFullYear();
    
    // Check for fiscal year quarters (Thai fiscal year: Oct-Sep)
    // Q1: Oct-Dec, Q2: Jan-Mar, Q3: Apr-Jun, Q4: Jul-Sep
    const quarterMap = {
        '9-11': 'Q1',   // Oct-Dec
        '0-2': 'Q2',    // Jan-Mar
        '3-5': 'Q3',    // Apr-Jun
        '6-8': 'Q4'     // Jul-Sep
    };
    
    const key = `${startMonth}-${endMonth}`;
    const quarter = quarterMap[key];
    
    if (quarter) {
        const fy = startMonth >= 9 ? (year + 1) % 100 : year % 100;
        return `${quarter} FY${fy}`;
    }
    
    return '';
}

function reloadTimeline() {
    const timelineContainer = document.getElementById('timelineContainer');
    timelineContainer.innerHTML = `
        <div class="flex items-center justify-center py-8">
            <span class="loading loading-dots loading-lg text-primary"></span>
        </div>
    `;
    drawTimeline();
}
