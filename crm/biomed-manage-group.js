/**
 * biomed-manage-group.js
 * Group Management with daisyUI styling
 */

const urlParams = new URLSearchParams(window.location.search);
const id = urlParams.get('id');

let allUsers = [];
let selectedUserIds = [];
let mainUserId = null;

window.onload = function() {
    if (!id) {
        xalert("No id please check your url", 1, null);
        return;
    }
    
    // Update group ID badge
    document.getElementById('groupIdBadge').textContent = 'ID: ' + id;
    
    // Load group data
    getGroupMembers(id, function(error, response) {
        if (error) {
            console.error('Failed to fetch group:', error);
            xalert("Failed to fetch group", 1, null);
            return;
        }
        
        // Set group name
        document.getElementById('groupName').value = response.GroupName;
        document.getElementById('breadcrumbGroupName').textContent = response.GroupName;
        
        // Store main user ID
        mainUserId = response.MainUserId;
        
        // Get selected user IDs from group
        selectedUserIds = response.GroupUsers.map(user => user.UserId);
        
        // Load all users
        loadUsers(response);
    });
}

function loadUsers(groupResponse) {
    getUsers((error, users) => {
        if (error) {
            console.error('Failed to fetch users:', error);
            xalert("Failed to fetch users", 1, null);
            return;
        }
        
        allUsers = users;
        
        // Update main users list display
        updateMainUsersList(groupResponse);
        
        // Populate modal
        populateMembersModal();
        
    }, false);
}

function updateMainUsersList(groupResponse) {
    const mainUsersList = document.getElementById('mainUsersList');
    mainUsersList.innerHTML = '';
    
    // Add selected member badges
    selectedUserIds.forEach(userId => {
        const user = allUsers.find(u => u.Id === userId);
        if (user) {
            const badge = document.createElement('span');
            badge.className = 'badge badge-secondary gap-1 member-badge';
            badge.innerHTML = `${user.FirstName} ${user.LastName}`;
            mainUsersList.appendChild(badge);
        }
    });
    
    if (mainUsersList.children.length === 0) {
        mainUsersList.innerHTML = '<span class="text-base-content/50 text-sm">No members</span>';
    }
}

function populateMembersModal() {
    const checkboxList = document.getElementById('usersCheckboxList');
    
    // Create checkboxes for all users
    checkboxList.innerHTML = '';
    allUsers.forEach(user => {
        const isChecked = selectedUserIds.includes(user.Id);
        
        const label = document.createElement('label');
        label.className = 'flex items-center gap-2 p-2 rounded hover:bg-base-200 cursor-pointer';
        label.innerHTML = `
            <input type="checkbox" class="checkbox checkbox-sm checkbox-primary" 
                   value="${user.Id}" 
                   ${isChecked ? 'checked' : ''}
                   onchange="updateModalPreview()">
            <span class="flex-1">${user.FirstName} ${user.LastName}</span>
            <span class="badge badge-ghost badge-xs">${user.Position || ''}</span>
        `;
        checkboxList.appendChild(label);
    });
    
    // Update preview
    updateModalPreview();
}

function updateModalPreview() {
    const modalUsersList = document.getElementById('modalUsersList');
    const checkboxes = document.querySelectorAll('#usersCheckboxList input[type="checkbox"]:checked');
    
    modalUsersList.innerHTML = '';
    
    // Add selected members
    checkboxes.forEach(cb => {
        const userId = parseInt(cb.value);
        const user = allUsers.find(u => u.Id === userId);
        if (user) {
            const badge = document.createElement('span');
            badge.className = 'badge badge-secondary';
            badge.textContent = `${user.FirstName} ${user.LastName}`;
            modalUsersList.appendChild(badge);
        }
    });
    
    if (modalUsersList.children.length === 0) {
        modalUsersList.innerHTML = '<span class="text-base-content/50 text-sm">No members selected</span>';
    }
}

function openMembersModal() {
    populateMembersModal();
    document.getElementById('membersModal').showModal();
}

function confirmMemberSelection() {
    const checkboxes = document.querySelectorAll('#usersCheckboxList input[type="checkbox"]:checked');
    selectedUserIds = Array.from(checkboxes).map(cb => parseInt(cb.value));
    
    // Update main display
    updateMainUsersList({});
    
    // Close modal
    document.getElementById('membersModal').close();
}

function saveGroup() {
    const groupName = document.getElementById('groupName').value;
    
    if (!groupName.trim()) {
        xalert("Group name is required", 1, null);
        return;
    }
    
    const data = {
        groupName: groupName,
        id: id,
        userIDs: selectedUserIds
    };

    updateGroup(data, function(error, response) {
        if (error) {
            console.error('Failed to update group:', error);
            xalert("Failed to update group", 1, null);
            return;
        }
        console.log('Group updated successfully:', response);
        xalert("Group updated successfully", 0, null);
        document.getElementById('breadcrumbGroupName').textContent = groupName;
    });
}

function updateGroup(data, callback) {
    const xhr = new XMLHttpRequest();
    xhr.open('POST', url + '/biomedapi/groups/update');
    xhr.setRequestHeader('Authorization', `Bearer ${readToken()}`);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.onload = function() {
        if (xhr.status === 200) {
            callback(null, xhr.responseText);
        } else {
            callback('Failed to update group', null);
        }
    };
    xhr.onerror = function() {
        callback('Failed to send request', null);
    };
    xhr.send(JSON.stringify(data));
}
