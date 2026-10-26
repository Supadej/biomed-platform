// biomed-project-activity.js - DaisyUI version of Project Activity
const urlParams = new URLSearchParams(window.location.search);
const activityid = urlParams.get("activityid");

// D3 Button click handler
document.getElementById("d3Button").addEventListener("click", function () {
    window.location.href = `./d3.html?type=${"Activities"}&id=${activityid}`;
});

// Function to get selected pipeline ID (used by biomed-global.js for change tracking)
function getSelectedPipelineId() {
    return window.selectedPipelineId || null;
}

// DOM Elements
const modalUsersList = document.getElementById("modalUsersList");
const select = document.getElementById("usersSelecter");
const groupSelect = document.getElementById("groupSelecter");
const contactSelect = document.getElementById("contactsSelecter");
const mainContactSelect = document.getElementById("mainContactsSelecter");
const modalContactsList = document.getElementById("modalContactsList");

// Sync contacts list
function syncContactsList() {
    const mainContactsList = document.getElementById('mainContactsList');
    if (mainContactsList && modalContactsList) {
        mainContactsList.innerHTML = modalContactsList.innerHTML;
    }
}

// MutationObserver for contacts list
if (modalContactsList) {
    const observer = new MutationObserver(syncContactsList);
    observer.observe(modalContactsList, { childList: true });
}

var mainuserid;
var projectId;

window.onload = function () {
    if (activityid === null) {
        xalert("Error: No activity id parameter found in the URL", 1, null);
        return;
    }

    const token = readToken();
    const xhr = new XMLHttpRequest();
    
    xhr.open("GET", url + `/biomedapi/v2/project/activities/${activityid}`, true);
    xhr.setRequestHeader("Authorization", `Bearer ${token}`);

    xhr.onload = function () {
        if (xhr.status === 200) {
            const response = JSON.parse(xhr.responseText);
            console.log(response);
            mainuserid = response.MainUserId;

            // Populate form fields
            if (response.Name) {
                document.getElementById("leadName").value = response.Name;
            }
            if (response.Creation) {
                document.getElementById("creation").value = timeFuck(response.Creation);
            }
            if (response.Update) {
                document.getElementById("update").value = timeFuck(response.Update);
            }
            if (response.Objective) {
                document.getElementById("objective").value = response.Objective;
            }
            if (response.Description) {
                document.getElementById("description").value = response.Description;
            }
            if (response.Budget != null) {
                document.getElementById("budget").value = response.Budget;
            }
            if (response.Outcome != null) {
                document.getElementById("outcome").value = response.Outcome;
            }
            if (response.ActivityReturn) {
                document.getElementById("activityReturn").value = response.ActivityReturn;
            }
            if (response.InvolvedProducts) {
                document.getElementById("involvedProducts").value = response.InvolvedProducts;
            }
            if (response.Insight) {
                document.getElementById("insight").value = response.Insight;
            }
            if (response.NextStep) {
                document.getElementById("nextStep").value = response.NextStep;
            }
            if (response.Done) {
                document.getElementById("done").value = response.Done;
            }
            if (response.KeyPoints) {
                document.getElementById("keyPoints").value = response.KeyPoints;
            }
            if (response.Notes) {
                document.getElementById("notes").value = response.Notes;
            }
            if (response.Brochures) {
                document.getElementById("brochures").value = response.Brochures;
            }
            if (response.Publications) {
                document.getElementById("publications").value = response.Publications;
            }
            if (response.Gimmicks) {
                document.getElementById("gimmicks").value = response.Gimmicks;
            }
            if (response.Products) {
                document.getElementById("products").value = response.Products;
            }
            if (response.Materials) {
                document.getElementById("materials").value = response.Materials;
            }
            if (response.MaterialBudget != null) {
                document.getElementById("materialBudget").value = response.MaterialBudget;
            }
            if (response.Responsibles) {
                document.getElementById("responsibles").value = response.Responsibles;
            }
            if (response.Responsibilities) {
                document.getElementById("responsibilities").value = response.Responsibilities;
            }
            if (response.Expense != null) {
                document.getElementById("expense").value = response.Expense;
            }

            projectId = response.ProjectID;
            const currentPipelineId = response.ProjectPipelineId;

            // Load project and pipelines
            getProjectById(response.ProjectID, (err, project) => {
                if (err) {
                    console.error("Failed to fetch project:", err);
                    return;
                }
                
                document.getElementById("activityLocation").innerHTML = `
                    <span class="text-base-content/60">Project:</span> 
                    <a href="./project-overview.html?projectId=${project.Id}" class="link link-primary">${escapeHtml(project.Name)}</a>
                `;

                const sortedPipelines = (project.Pipelines || []).sort((a, b) => a.Order - b.Order);
                const pipelineSelection = document.getElementById("pipelineSelection");
                pipelineSelection.innerHTML = '';

                // Find index of current pipeline
                const currentIndex = sortedPipelines.findIndex(p => p.Id === currentPipelineId);
                
                // Store pipelines for later use
                window.pipelinesCache = sortedPipelines;

                sortedPipelines.forEach((pipeline, index) => {
                    const step = document.createElement("li");
                    step.className = "step cursor-pointer";
                    step.setAttribute("data-content", index + 1);
                    step.setAttribute("data-pipeline-id", pipeline.Id);
                    step.textContent = pipeline.Name;
                    
                    // Add step-primary class for completed and active steps
                    if (index <= currentIndex) {
                        step.classList.add("step-primary");
                    }
                    
                    // Click handler to select pipeline
                    step.addEventListener("click", () => {
                        selectPipelineStep(pipeline.Id);
                    });
                    
                    pipelineSelection.appendChild(step);
                });
                
                // Store selected pipeline
                window.selectedPipelineId = currentPipelineId;
                
                // Cache object after pipeline is set
                cachingObject();
            }, false);

            // Load main responsible user
            getUsers((error, users) => {
                if (error) {
                    console.error("Failed to fetch users:", error);
                    return;
                }

                const Muser = users.find((u) => u.Id === response.MainUserId);
                if (Muser) {
                    const primaryBadge = document.createElement("span");
                    primaryBadge.className = "badge badge-info gap-1";
                    primaryBadge.innerHTML = `
                        <i class="fi fi-rr-chess-king text-xs"></i>
                        ${escapeHtml(Muser.FirstName)} ${escapeHtml(Muser.LastName)} 
                        <span class="text-xs opacity-70">(${escapeHtml(Muser.Position || '')})</span>
                    `;
                    document.getElementById("responsible").appendChild(primaryBadge);
                }
            });
            
            // Load logs for this activity
            loadLogs(null, null, null, null, parseInt(activityid), null);
        } else {
            xalert("Error loading activity: " + xhr.status, 1, null);
        }
    };

    xhr.send();
};

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Select pipeline step and update UI
// Select pipeline step and update UI (daisyUI steps)
function selectPipelineStep(pipelineId) {
    window.selectedPipelineId = pipelineId;
    
    const pipelines = window.pipelinesCache || [];
    const steps = document.querySelectorAll('#pipelineSelection .step');
    const selectedIndex = pipelines.findIndex(p => p.Id === pipelineId);
    
    steps.forEach((step, index) => {
        step.classList.remove('step-primary');
        
        // Add step-primary for completed and active steps
        if (index <= selectedIndex) {
            step.classList.add('step-primary');
        }
    });
}

function contactsModal() {
    const modal = document.getElementById("multiContactModal");
    modal.showModal();
}

function usersModal() {
    const modal = document.getElementById("multiSelectModal");
    modal.showModal();
}

async function updateLead() {
    let changedComponent = await compareChange();
    let readableChanges = changedComponent.map(change => {
        let oldValue = Array.isArray(change.oldValue) ? change.oldValue.join(", ") : (typeof(change.oldValue) === 'boolean' ? change.oldValue : change.oldValue || "N/A");
        let newValue = Array.isArray(change.newValue) ? change.newValue.join(", ") : (typeof(change.newValue) === 'boolean' ? change.newValue : change.newValue || "N/A");
        return `${change.field}: ${oldValue} -> ${newValue}`;
    }).join("\n");

    console.log(readableChanges);
    createLog(readableChanges, JSON.stringify(changedComponent), null, null, null, null, parseInt(activityid), 4, function(err, log) {
        if (err) {
            console.error(err);
            updateLeadRequest();
            return;
        }
        console.log('Log created successfully:', log);
        updateLeadRequest();
    });
}

function updateLeadRequest() {
    var xhr = new XMLHttpRequest();
    
    // Use new pipeline selection
    if (!window.selectedPipelineId) {
        xalert("Error: No pipeline selected", 2, 5000);
        return;
    }

    xhr.open("POST", url + "/biomedapi/v2/project/activities/update", true);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.setRequestHeader("Authorization", "Bearer " + readToken());

    var data = {
        Id: activityid,
        Name: document.getElementById("leadName").value,
        MainUserId: parseInt(mainuserid),
        Update: timeFormater(Date.now()),
        ActivityReturn: document.getElementById("activityReturn").value,
        Objective: document.getElementById("objective").value,
        Description: document.getElementById("description").value,
        Budget: parseFloat(document.getElementById("budget").value) || 0,
        Outcome: parseFloat(document.getElementById("outcome").value) || 0,
        InvolvedProducts: document.getElementById("involvedProducts").value,
        Insight: document.getElementById("insight").value,
        NextStep: document.getElementById("nextStep").value,
        Done: document.getElementById("done").value,
        KeyPoints: document.getElementById("keyPoints").value,
        Notes: document.getElementById("notes").value,
        Brochures: document.getElementById("brochures").value,
        Publications: document.getElementById("publications").value,
        Gimmicks: document.getElementById("gimmicks").value,
        Products: document.getElementById("products").value,
        Materials: document.getElementById("materials").value,
        MaterialBudget: parseFloat(document.getElementById("materialBudget").value) || 0,
        Responsibles: document.getElementById("responsibles").value,
        Responsibilities: document.getElementById("responsibilities").value,
        Expense: parseFloat(document.getElementById("expense").value) || 0,
        PipelineId: window.selectedPipelineId,
    };

    xhr.onload = function () {
        if (xhr.status === 200) {
            xalert("Activity updated successfully", 0, null);
            console.log("Activity updated successfully");
            // Clear project cache so overview reloads fresh data
            sessionStorage.removeItem('project:' + projectId);
            sessionStorage.removeItem('projects');
            setTimeout(() => {
                window.location.href = "./project-overview.html?projectId=" + projectId;
            }, 1000);
        } else {
            xalert("Error:" + xhr.status + " " + xhr.responseText, 1, null);
            console.error("Error:", xhr.status);
        }
    };

    xhr.send(JSON.stringify(data));
}

function modalContactsUpdate() {
    if (!mainContactSelect || !contactSelect || !modalContactsList) return;
    
    const mainselectedOptions = Array.from(mainContactSelect.selectedOptions);
    modalContactsList.innerHTML = "";
    
    mainselectedOptions.forEach((option) => {
        const badge = document.createElement("span");
        badge.className = "badge badge-info gap-1";
        badge.innerHTML = option.getAttribute("data-subtext")
            ? `${option.textContent} (${option.getAttribute("data-subtext")})`
            : option.textContent;
        modalContactsList.appendChild(badge);
    });
    
    const selectedOptions = Array.from(contactSelect.selectedOptions);
    
    selectedOptions.forEach((option) => {
        const badge = document.createElement("span");
        badge.className = "badge badge-accent gap-1";
        badge.innerHTML = option.getAttribute("data-subtext")
            ? `${option.textContent} (${option.getAttribute("data-subtext")})`
            : option.textContent;
        if (mainselectedOptions.length === 0 || mainselectedOptions[0].value !== option.value) {
            modalContactsList.appendChild(badge);
        }
    });
}

function deleteLead() {
    deleteLeadRequest();
}

function deleteLeadRequest() {
    var xhr = new XMLHttpRequest();

    xhr.open("POST", url + "/biomedapi/v2/project/activities/delete", true);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.setRequestHeader("Authorization", "Bearer " + readToken());

    xhr.onload = function () {
        if (xhr.status === 200) {
            xalert("Activity deleted successfully", 0, null);
            console.log("Activity deleted successfully");
            // Clear project cache so overview reloads fresh data
            sessionStorage.removeItem('project:' + projectId);
            sessionStorage.removeItem('projects');
            setTimeout(() => {
                window.location.href = "./project-overview.html?projectId=" + projectId;
            }, 1000);
        } else {
            xalert("Error:" + xhr.status + " " + xhr.responseText, 1, null);
            console.error("Error:", xhr.status);
        }
    };

    xhr.send(JSON.stringify({ Id: parseInt(activityid) }));
}
