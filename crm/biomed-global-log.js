var logLeadId = (typeof leadid !== 'undefined' && !isNaN(leadid)) ? parseInt(leadid) : null;
var logHelpdeskTicketId = (typeof hdid !== 'undefined' && !isNaN(hdid)) ? parseInt(hdid) : null;
var logActivityId = (typeof activityid !== 'undefined' && !isNaN(activityid)) ? parseInt(activityid) : null;
//ahhhhhhhhhhhhhhhhhhhhhhhhhhhh
//ah
//ah logEventId is too dynamic so it is not defined here
var logEventId = function (){
   
    return (typeof currentID !== 'undefined' && currentID !== null && !isNaN(currentID)) ? parseInt(currentID) : null;
};
function toggleVisible(){
    document.getElementById('addLogBtn').classList.toggle('hidden');
    document.getElementById('saveLogBtn').classList.toggle('hidden');
};
function addText(){
    toggleVisible();
    
    document.getElementById('logTextarea').classList.remove('hidden');
    console.log(document.getElementById('logTextarea'));
};
function sendText(){
    toggleVisible();
    document.getElementById('logTextarea').classList.add('hidden');
    const logValue = document.getElementById('logTextareaValue').value;
    if(logValue === null || logValue === ''){
        console.error('Log value is empty');
        return;
    }
    document.getElementById('logTextareaValue').value = '';
    myUserRequest(function(err,user){
        if(err){
            console.error(err);
            return;
        }
        // SystemLog cannot be null, use logValue as fallback
        createLog(logValue, logValue, logLeadId, logEventId(), user.Id, logHelpdeskTicketId, logActivityId, 0);
    });
}


function loadLogs(id, leadid, eventid, ticketid, activityid,userid){
    const xhr = new XMLHttpRequest();
    [id, leadid, eventid, ticketid, activityid, userid].forEach((param, index) => {
        if (param === undefined || param === null||param === NaN) {
            switch (index) {
                case 0: id = null; break;
                case 1: leadid = null; break;
                case 2: eventid = null; break;
                case 3: ticketid = null; break;
                case 4: activityid = null; break;
                case 5: userid = null; break;
            }
        }
    });
    xhr.open('POST', url+'/biomedapi/log/get', true);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.setRequestHeader("Authorization", "Bearer " + readToken());
    const logRequest = {
        id: id,
        LeadId: leadid,
        EventId: eventid,
        UserId: userid,
        HelpdeskTicketId: ticketid,
        ActivityId: activityid
    };

    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4) {
            if (xhr.status === 200) {
                const logs = JSON.parse(xhr.responseText);
                console.log('Logs loaded successfully:', logs);
                // Process logs as needed
                displayLogs(logs);
            } else {
                console.error('Error loading logs:', xhr.statusText);
            }
        }
    };
    console.log('Sending log request:', logRequest);
    xhr.send(JSON.stringify(logRequest));
    
}
function displayLogs(logs){
    console.log('Displaying logs:', logs);
    if (!document.getElementById('logList')) {
        console.error('logList element does not exist. Skipping log display.');
        return;
    }
    document.getElementById('logList').innerHTML = '';
    
    // Sort logs by date (newest first)
    logs.sort((a, b) => new Date(b.DateTime) - new Date(a.DateTime));
    
    // Escape HTML helper
    const escapeHtml = (str) => {
        if (!str) return "";
        return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
    };
    
    // Build all HTML first, then insert once
    let html = '';
    const userPromises = [];
    
    logs.forEach((log, index) => {
        userPromises.push(new Promise((resolve) => {
            getUserById(function(err, user){
                if(err){
                    console.error(err);
                    resolve({ index, html: '' });
                    return;
                }
                
                const userName = `${user.FirstName} ${user.LastName}`;
                const timeStr = timeFormater(log.DateTime);
                
                // Determine log type styling
                let typeLabel = 'บันทึก';
                let typeClass = 'text';
                let typeIcon = 'fa-comment';
                let itemClass = '';
                
                switch (log.Type) { 
                    case "Text": 
                        typeLabel = "บันทึก"; 
                        typeClass = "text"; 
                        typeIcon = "fa-comment"; 
                        break;
                    case "File": 
                        typeLabel = 'ไฟล์'; 
                        typeClass = "file"; 
                        typeIcon = "fa-paperclip"; 
                        itemClass = "file";
                        break;
                    case "Binder": 
                        typeLabel = 'Binder'; 
                        typeClass = "binder"; 
                        typeIcon = "fa-link"; 
                        itemClass = "binder";
                        break;
                    case "System": 
                        typeLabel = 'System'; 
                        typeClass = "change"; 
                        typeIcon = "fa-sync-alt"; 
                        itemClass = "system";
                        break;
                    default: 
                        typeLabel = 'บันทึก'; 
                        typeClass = "text"; 
                        typeIcon = "fa-comment"; 
                        break;
                }
                
                // Build content HTML
                let contentHtml = '';
                let fileHtml = '';
                
                if(log.Type == "File"){
                    const fileUrl = "./storage/" + log.SystemLog;
                    const fileName = log.SystemLog.toLowerCase();
                    const ext = fileName.split('.').pop();
                    
                    const imageExts = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp'];
                    const videoExts = ['mp4', 'avi', 'mov', 'wmv', 'flv', 'mkv', 'webm'];
                    
                    contentHtml = escapeHtml(log.LogValue || '');
                    
                    if (imageExts.includes(ext)) {
                        fileHtml = `<div class="mt-2"><a href="${fileUrl}" target="_blank"><img src="${fileUrl}" alt="${escapeHtml(log.LogValue)}" class="rounded-lg max-w-full max-h-48 object-contain border border-base-300" /></a><a href="${fileUrl}" target="_blank" class="flex items-center gap-2 mt-1 text-sm text-primary hover:underline"><i class="fas fa-download"></i> ดาวน์โหลดไฟล์</a></div>`;
                    } else if (videoExts.includes(ext)) {
                        fileHtml = `<div class="mt-2"><video controls class="rounded-lg max-w-full max-h-48 border border-base-300"><source src="${fileUrl}" type="video/${ext === 'mov' ? 'quicktime' : ext}">Your browser does not support the video tag.</video><a href="${fileUrl}" target="_blank" class="flex items-center gap-2 mt-1 text-sm text-primary hover:underline"><i class="fas fa-download"></i> ดาวน์โหลดไฟล์</a></div>`;
                    } else {
                        fileHtml = `<a href="${fileUrl}" target="_blank" class="flex items-center gap-2 mt-2 text-sm text-primary hover:underline"><i class="fas fa-download"></i> ดาวน์โหลดไฟล์</a>`;
                    }
                    
                } else if(log.Type == "Binder"){
                    try {
                        let binderData = JSON.parse(log.SystemLog);
                        let report = '';
                        if (binderData.logLeadId !== null) report += `<a href="./crm-detail.html?leadid=${binderData.logLeadId}" class="link link-primary">Lead (${binderData.logLeadId})</a> ⮜⬥⮞ `;
                        if (binderData.logEventId !== null) report += `<a href="./event.html?id=${binderData.logEventId}" class="link link-primary">Event (${binderData.logEventId})</a> ⮜⬥⮞ `;
                        if (binderData.logHelpdeskTicketId !== null) report += `<a href="./helpdesk-detail.html?hdid=${binderData.logHelpdeskTicketId}" class="link link-primary">Helpdesk (${binderData.logHelpdeskTicketId})</a> ⮜⬥⮞ `;
                        if (binderData.logActivityId !== null) report += `<a href="./project-activity.html?activityid=${binderData.logActivityId}" class="link link-primary">Activity (${binderData.logActivityId})</a> ⮜⬥⮞ `;
                        if (report.endsWith(' ⮜⬥⮞ ')) report = report.slice(0, -5);
                        contentHtml = `<span class="opacity-70">Binding:</span> ${report}`;
                    } catch(e) {
                        contentHtml = escapeHtml(log.LogValue || '');
                    }
                    
                } else if(log.Type == "System"){
                    const lines = (log.LogValue || '').split('\n');
                    const formattedLines = lines.map(line => {
                        const colonIndex = line.indexOf(':');
                        if (colonIndex > 0) {
                            const fieldName = escapeHtml(line.substring(0, colonIndex));
                            const fieldValue = escapeHtml(line.substring(colonIndex + 1));
                            return `<strong>${fieldName}:</strong>${fieldValue}`;
                        }
                        return escapeHtml(line);
                    });
                    contentHtml = `<div class="log-change-detail whitespace-pre-line">${formattedLines.join('<br>')}</div>`;
                    
                } else {
                    contentHtml = escapeHtml(log.LogValue || '');
                }
                
                const logHtml = `<div class="log-item ${itemClass}"><div class="log-item-header"><span class="log-item-user"><i class="fas fa-user-circle mr-1"></i>${userName}</span><span class="log-item-time">${timeStr}</span></div><div class="log-item-content"><span class="log-item-type ${typeClass}"><i class="fas ${typeIcon} mr-1"></i>${typeLabel}</span>${contentHtml}${fileHtml}</div></div>`;
                
                resolve({ index, html: logHtml });
            }, log.UserId);
        }));
    });
    
    // Wait for all user lookups to complete, then render in correct order
    Promise.all(userPromises).then(results => {
        // Sort by original index to maintain order
        results.sort((a, b) => a.index - b.index);
        const finalHtml = results.map(r => r.html).join('');
        document.getElementById('logList').innerHTML = finalHtml;
    });
}
function createLog(logValue, systemLog, leadId, eventId, userId, helpdeskTicketId, activityId, type, callback) {
    //Type 0 = Text 2 = File 3 = Binder 4 = System
    if (type === null || !Number.isInteger(type)) {
        console.error('Invalid type: must be a non-null integer');
        if (callback) callback(new Error('Invalid type: must be a non-null integer'));
        return;
    }
    const logData = {
        LogValue: logValue,
        SystemLog: systemLog,
        Visible: true,
        LeadId: leadId,
        EventId: eventId,
        UserId: userId,
        HelpdeskTicketId: helpdeskTicketId,
        ActivityId: activityId,
        Type: type
    };

    const xhr = new XMLHttpRequest();
    xhr.open('POST', url+'/biomedapi/log/create', true);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.setRequestHeader("Authorization", "Bearer " + readToken());
    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4) {
            if (xhr.status === 200) {
                console.log('Log created successfully:', JSON.parse(xhr.responseText));
                if (callback) callback(null, JSON.parse(xhr.responseText));
            } else {
                console.error('Error creating log:', xhr.statusText);
                if (callback) callback(new Error('Error creating log: ' + xhr.statusText));
            }
            autoload();
        }
    };

    xhr.send(JSON.stringify(logData));
}

function promiseCreateLog(logValue, systemLog, leadId, eventId, userId, helpdeskTicketId, activityId, type) {
    return new Promise((resolve, reject) => {
        createLog(logValue, systemLog, leadId, eventId, userId, helpdeskTicketId, activityId, type, (err, result) => {
            if (err) {
                reject(err);
            } else {
                resolve(result);
            }
        });
    });
}

/**
 * Promise-based function to get logs
 * @param {number|null} eventId - Event ID to filter logs
 * @param {number|null} leadId - Lead ID to filter logs
 * @param {number|null} ticketId - Helpdesk Ticket ID to filter logs
 * @param {number|null} activityId - Activity ID to filter logs
 * @returns {Promise<Array>} - Array of log objects
 */
function promiseLogs(eventId = null, leadId = null, ticketId = null, activityId = null) {
    return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        
        const logRequest = {
            id: null,
            LeadId: leadId,
            EventId: eventId,
            UserId: null,
            HelpdeskTicketId: ticketId,
            ActivityId: activityId
        };
        
        xhr.open('POST', url + '/biomedapi/log/get', true);
        xhr.setRequestHeader("Content-Type", "application/json");
        xhr.setRequestHeader("Authorization", "Bearer " + readToken());
        
        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4) {
                if (xhr.status === 200) {
                    try {
                        const logs = JSON.parse(xhr.responseText);
                        resolve(logs);
                    } catch (e) {
                        reject(new Error('Failed to parse logs response'));
                    }
                } else {
                    reject(new Error('Error loading logs: ' + xhr.statusText));
                }
            }
        };
        
        xhr.send(JSON.stringify(logRequest));
    });
}

function addFile(){
    uploadFile(function(err, file){
        if(err){
            console.error(err);
            return;
        }
        const fileName = file.split('_').slice(2).join('_');
        createLog(fileName, file, logLeadId,logEventId(), null, logHelpdeskTicketId, logActivityId, 2);
    });


}

function determineFileType(fileName) {
    const extension = fileName.split('.').pop().toLowerCase();

    const fileTypes = {
        images: ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp', 'tiff'],
        pdf: ['pdf'],
        word: ['doc', 'docx'],
        excel: ['xls', 'xlsx', 'csv'],
        powerpoint: ['ppt', 'pptx'],
        text: ['txt', 'rtf', 'log'],
        audio: ['mp3', 'wav', 'aac', 'ogg', 'flac', 'wma'],
        video: ['mp4', 'avi', 'mov', 'wmv', 'flv', 'mkv', 'webm'],
        archive: ['zip', 'rar', '7z', 'tar', 'gz'],
        code: ['html', 'css', 'js', 'json', 'xml', 'py', 'java', 'cpp', 'c', 'cs', 'php', 'rb', 'go', 'swift', 'ts', 'sh', 'sql'],
        executable: ['exe', 'msi', 'bat', 'sh', 'apk', 'dmg'],
        diskImage: ['iso', 'img']
    };

    for (const [type, extensions] of Object.entries(fileTypes)) {
        if (extensions.includes(extension)) {
            return type.charAt(0).toUpperCase() + type.slice(1) + ' File';
        }
    }

    return 'Unknown File Type';
}
function autoload(){
    // Guard: Only run if log container exists (legacy pages or new pages)
    const logContainer = document.getElementById('logContainer') || document.getElementById('logList');
    if (!logContainer) {
        console.log('Log autoload skipped: logContainer/logList not found');
        return;
    }
    if ((logLeadId === null || isNaN(logLeadId)) && 
        (logEventId() === null || isNaN(logEventId())) && 
        (logHelpdeskTicketId === null || isNaN(logHelpdeskTicketId)) && 
        (logActivityId === null || isNaN(logActivityId))) {
        console.error('At least one of logLeadId, logEventId, logHelpdeskTicketId, or logActivityId must be non-null and not NaN');
        return;
    }
    console.log('Loading logs...');
    console.log(logLeadId,logEventId(),logHelpdeskTicketId,logActivityId);
    loadLogs(null,logLeadId,logEventId(),logHelpdeskTicketId,logActivityId,null);
}

function addBinder(){
    const binderTemporary = {
        logLeadId: (logLeadId !== null && Number.isInteger(logLeadId)) ? logLeadId : null,
        logEventId: (logEventId() !== null && Number.isInteger(logEventId())) ? logEventId() : null,
        logHelpdeskTicketId: (logHelpdeskTicketId !== null && Number.isInteger(logHelpdeskTicketId)) ? logHelpdeskTicketId : null,
        logActivityId: (logActivityId !== null && Number.isInteger(logActivityId)) ? logActivityId : null
    };
    localStorage.setItem('binderTemporary', JSON.stringify(binderTemporary));
    console.log('Binder data saved:', binderTemporary);
    loadBinder();
}

function loadBinder(){
    // Guard: Check all required binder UI elements exist
    const bindingBtn = document.getElementById('bindingBtn');
    const dropBtn = document.getElementById('dropBtn');
    const cancelBtn = document.getElementById('cancelBtn');
    
    if (!bindingBtn || !dropBtn || !cancelBtn) {
        console.log('Binder elements not found. Skipping Binder Loading.');
        return;
    }
    const binderTemporary = localStorage.getItem('binderTemporary');
    if (binderTemporary) {
        const parsedBinder = JSON.parse(binderTemporary);
        console.log('Binder data loaded:', parsedBinder);
        bindingBtn.classList.add('hidden');
        dropBtn.classList.remove('hidden');
        cancelBtn.classList.remove('hidden');
        
        const isBinderValid = () => {
            const { logLeadId: binderLeadId, logEventId: binderEventId, logHelpdeskTicketId: binderHelpdeskId, logActivityId: binderActivityId } = parsedBinder;

            const localLeadId = logLeadId;
            const localEventId = logEventId();
            const localHelpdeskId = logHelpdeskTicketId;
            const localActivityId = logActivityId;

            const binderIds = [binderLeadId, binderEventId, binderHelpdeskId, binderActivityId];
            const localIds = [localLeadId, localEventId, localHelpdeskId, localActivityId];

            for (let i = 0; i < binderIds.length; i++) {
                if (binderIds[i] !== null && localIds[i] !== null) {
                    return false;
                }
            }
            return true;
        };

        if (!isBinderValid()) {
            console.log('Binder validation failed: conflicting IDs');
            dropBtn.setAttribute('disabled','');
            dropBtn.classList.add('btn-disabled');
            return;
        }else{
            console.log('Binder validation passed');
            dropBtn.removeAttribute('disabled');
            dropBtn.classList.remove('btn-disabled');
        }
        // Process the binder data as needed
    } else {
        bindingBtn.classList.remove('hidden');
        dropBtn.classList.add('hidden');
        cancelBtn.classList.add('hidden');
        console.log('No binder data found in localStorage');
    }
};

function cancelBinder(){
    localStorage.removeItem('binderTemporary');
    console.log('Binder data removed from localStorage');
    loadBinder();
};

function dropBinder(){
    const binderTemporary = JSON.parse(localStorage.getItem('binderTemporary'));
    if (!binderTemporary) {
        console.error('No binder data found in localStorage');
        return;
    }

    const { logLeadId: binderLeadId, logEventId: binderEventId, logHelpdeskTicketId: binderHelpdeskId, logActivityId: binderActivityId } = binderTemporary;

    const localLeadId = logLeadId;
    const localEventId = logEventId();
    const localHelpdeskId = logHelpdeskTicketId;
    const localActivityId = logActivityId;

    const binderIds = [binderLeadId, binderEventId, binderHelpdeskId, binderActivityId];
    const localIds = [localLeadId, localEventId, localHelpdeskId, localActivityId];

    for (let i = 0; i < binderIds.length; i++) {
        if (binderIds[i] !== null && localIds[i] !== null) {
            console.error('Binder validation failed: conflicting IDs');
            return;
        }
    }

    const newBinder = {
        logLeadId: binderLeadId !== null ? binderLeadId : localLeadId,
        logEventId: binderEventId !== null ? binderEventId : localEventId,
        logHelpdeskTicketId: binderHelpdeskId !== null ? binderHelpdeskId : localHelpdeskId,
        logActivityId: binderActivityId !== null ? binderActivityId : localActivityId
    };

    let report = '';
    if (newBinder.logLeadId !== null) report += `Lead (${newBinder.logLeadId}) <-> `;
    if (newBinder.logEventId !== null) report += `Event (${newBinder.logEventId}) <-> `;
    if (newBinder.logHelpdeskTicketId !== null) report += `Helpdesk (${newBinder.logHelpdeskTicketId}) <-> `;
    if (newBinder.logActivityId !== null) report += `Activity (${newBinder.logActivityId}) <-> `;

    // Remove the trailing ' <-> ' if it exists
    if (report.endsWith(' <-> ')) {
        report = report.slice(0, -5);
    }

    console.log(report);

    console.log('New binder data saved:', newBinder);
    createLog("Binding between "+report, JSON.stringify(newBinder), newBinder.logLeadId, newBinder.logEventId, null, newBinder.logHelpdeskTicketId, newBinder.logActivityId, 3);
    localStorage.removeItem('binderTemporary');
    loadBinder();
};


// Load binder state when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', loadBinder);
} else {
    loadBinder();
}