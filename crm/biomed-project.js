// biomed-project.js - DaisyUI version of Project management
var pipelineCache = [];
var pipelineIdCache = null;
var deleteProjectId = null;

function editpipeline(pipelineId) {
    createProjectModal(pipelineId);
}

function deletepipeline(pipelineId) {
    deleteProjectId = pipelineId;
    const project = pipelineCache.find(p => p.Id === pipelineId);
    
    // Show delete confirmation modal
    const modal = document.getElementById('deleteConfirmModal');
    const confirmBtn = document.getElementById('confirmDeleteBtn');
    
    // Set up confirm button handler
    confirmBtn.onclick = function() {
        deletePipelineRequest(deleteProjectId);
        modal.close();
    };
    
    modal.showModal();
}

function createProjectModal(pipelineId = null) {
    pipelineIdCache = pipelineId;
    const modal = document.getElementById('projectModal');
    const titleInput = document.getElementById('pipelineTitle');
    const descInput = document.getElementById('pipelineOrder');
    const modalTitle = document.getElementById('modalTitle');
    const actionText = document.getElementById('modalActionText');
    const actionBtn = document.getElementById('modalActionBtn');
    
    // Reset form
    titleInput.value = '';
    descInput.value = '';
    
    if (pipelineId) {
        // Edit mode
        const pipeline = pipelineCache.find(p => p.Id === pipelineId);
        if (pipeline) {
            titleInput.value = pipeline.Name || '';
            descInput.value = pipeline.Description || '';
        }
        modalTitle.textContent = 'Edit Project';
        actionText.textContent = 'Update';
        actionBtn.className = 'btn btn-primary';
    } else {
        // Create mode
        modalTitle.textContent = 'Add Project';
        actionText.textContent = 'Create';
        actionBtn.className = 'btn btn-primary';
    }
    
    modal.showModal();
}

function createCRMPipeline() {
    createPipelineRequest(pipelineIdCache);
    document.getElementById('projectModal').close();
}

function deletePipelineRequest(pipelineId) {
    const token = readToken();
    const xhr = new XMLHttpRequest();
    xhr.open('POST', url + '/biomedapi/v2/project/delete', true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.setRequestHeader('Authorization', `Bearer ${token}`);
    xhr.onreadystatechange = function() {
        if (xhr.readyState === XMLHttpRequest.DONE) {
            if (xhr.status === 200) {
                xalert('Project deleted successfully', 0, -1);
                setTimeout(function() {
                    location.reload();
                }, 2000);
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
    const description = document.getElementById('pipelineOrder').value;
    
    if (!name.trim()) {
        xalert('Please enter a project name', 2, 3000);
        return;
    }

    const xhr = new XMLHttpRequest();
    if (pipelineId) {
        xhr.open('POST', url + '/biomedapi/v2/project/update', true);
    } else {
        xhr.open('POST', url + '/biomedapi/v2/project/create', true);
    }
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.setRequestHeader('Authorization', `Bearer ${token}`);
    xhr.onreadystatechange = function() {
        if (xhr.readyState === XMLHttpRequest.DONE) {
            if (xhr.status === 200) {
                xalert('Project ' + (pipelineId ? 'updated' : 'created') + ' successfully', 0, -1);
                setTimeout(function() {
                    location.reload();
                }, 2000);
            } else {
                xalert('Error ' + xhr.status + " " + xhr.responseText, 1, -1);
            }
        }
    };
    
    let rawdata = {
        Name: name,
        Description: description
    };
    if (pipelineId) {
        rawdata.Id = pipelineId;
    }
    
    const data = JSON.stringify(rawdata);
    xhr.send(data);
}

function renderProjectCard(project) {
    const card = document.createElement('div');
    card.className = 'card bg-base-100 shadow-sm project-card';
    
    card.innerHTML = `
        <div class="card-body">
            <div class="flex items-start justify-between mb-2">
                <div class="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center flex-shrink-0">
                    <i class="fi fi-rr-folder text-xl text-primary"></i>
                </div>
                <div class="dropdown dropdown-end">
                    <div tabindex="0" role="button" class="btn btn-ghost btn-sm btn-circle">
                        <i class="fa-solid fa-ellipsis-vertical"></i>
                    </div>
                    <ul tabindex="0" class="dropdown-content z-[1] menu p-2 shadow-lg bg-base-100 rounded-box w-40">
                        <li><a onclick="editpipeline(${project.Id})"><i class="fa-solid fa-pen mr-2"></i>Edit</a></li>
                        <li><a onclick="deletepipeline(${project.Id})" class="text-error"><i class="fa-solid fa-trash mr-2"></i>Delete</a></li>
                    </ul>
                </div>
            </div>
            
            <h2 class="card-title text-lg">${escapeHtml(project.Name || 'Untitled Project')}</h2>
            <p class="text-sm text-base-content/60 line-clamp-2 min-h-[2.5rem]">${escapeHtml(project.Description || 'No description')}</p>
            
            <div class="card-actions justify-end mt-4 pt-4 border-t border-base-200">
                <a href="./project-overview.html?projectId=${project.Id}" class="btn btn-primary btn-sm">
                    <i class="fa-solid fa-arrow-right mr-1"></i>
                    View Project
                </a>
            </div>
        </div>
    `;
    
    return card;
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

window.onload = function() {
    const container = document.getElementById('projectContainer');
    const emptyState = document.getElementById('emptyState');
    
    // Show loading state
    container.innerHTML = `
        <div class="col-span-full flex justify-center py-12">
            <span class="loading loading-spinner loading-lg text-primary"></span>
        </div>
    `;
    
    getProjects((err, projects) => {
        if (err) {
            console.error('Error loading projects:', err);
            xalert('Error loading projects: ' + (err.message || err), 1, -1);
            container.innerHTML = `
                <div class="col-span-full text-center py-12">
                    <div class="w-16 h-16 bg-error/10 rounded-full flex items-center justify-center mx-auto mb-4">
                        <i class="fa-solid fa-triangle-exclamation text-3xl text-error"></i>
                    </div>
                    <h3 class="text-lg font-semibold text-error">Failed to load projects</h3>
                    <p class="text-sm text-base-content/60 mt-2">${escapeHtml(err.message || 'Unknown error')}</p>
                    <button class="btn btn-primary btn-sm mt-4" onclick="location.reload()">
                        <i class="fa-solid fa-rotate-right mr-2"></i>Retry
                    </button>
                </div>
            `;
            return;
        }
        
        pipelineCache = projects || [];
        
        if (!projects || projects.length === 0) {
            container.classList.add('hidden');
            emptyState.classList.remove('hidden');
            return;
        }
        
        emptyState.classList.add('hidden');
        container.classList.remove('hidden');
        container.innerHTML = '';
        
        projects.forEach(project => {
            const card = renderProjectCard(project);
            container.appendChild(card);
        });
        
    }, true);
};
