/**
 * biomed-manage-detail.js
 * User Management Detail Page with daisyUI styling
 * Uses MultiSelect component for products, sale areas, and permissions
 */

const urlParams = new URLSearchParams(window.location.search);
const id = urlParams.get('id');

// MultiSelect instances
let productsMultiSelect = null;
let saleAreasMultiSelect = null;
let permissionsMultiSelect = null;

// Store for individual permissions
let individualPermissions = [];

// Current user data
let currentUser = null;

// Enabled state tracking for confirmation modal
let enabledPendingState = null;

window.onload = function() {
    if (!id) {
        xalert("No id please check your url", 1, null);
        return;
    }

    // Update user ID badge
    document.getElementById('userIdBadge').textContent = 'ID: ' + id;

    // Load user data
    loadUserData();
};

/**
 * Load user data from API
 */
function loadUserData() {
    const xhr = new XMLHttpRequest();
    xhr.open('GET', url + `/biomedapi/users/${id}`);
    xhr.setRequestHeader('Authorization', `Bearer ${readToken()}`);
    xhr.onload = function() {
        if (xhr.status === 200) {
            currentUser = JSON.parse(xhr.responseText);
            console.log('User loaded:', currentUser);
            populateUserForm(currentUser);
            initializeDropdowns(currentUser);
            initializeMultiSelects(currentUser);
            initializeIndividualPermissions(currentUser);
        } else {
            xalert("Failed to load user data", 1, null);
        }
    };
    xhr.onerror = function() {
        xalert("Failed to connect to server", 1, null);
    };
    xhr.send();
}

/**
 * Populate basic form fields
 */
function populateUserForm(user) {
    // Update breadcrumb
    const displayName = `${user.FirstName || ''} ${user.LastName || ''}`.trim() || user.username;
    document.getElementById('breadcrumbUserName').textContent = displayName;

    // Profile picture - generate fallback URL with initials
    const initials = `${user.FirstName?.[0] || ''}${user.LastName?.[0] || 'U'}`;
    const fallbackUrl = `/crm/assets/default-avatar.svg`;
    
    const profileImg = document.getElementById('profilePicPreview');
    profileImg.onerror = function() {
        this.onerror = null; // Prevent infinite loop
        this.src = fallbackUrl;
    };
    
    if (user.ProfilePic) {
        profileImg.src = url + '/crm/storage/' + user.ProfilePic;
    } else {
        profileImg.src = fallbackUrl;
    }

    // Basic fields
    document.getElementById('username').value = user.username || '';
    document.getElementById('first-name').value = user.FirstName || '';
    document.getElementById('last-name').value = user.LastName || '';
    document.getElementById('middle-name').value = user.MiddleName || '';
    document.getElementById('position').value = user.Position || '';
    document.getElementById('email').value = user.Email || '';
    document.getElementById('sale-code').value = user.SaleCode || '';
    document.getElementById('phone-number').value = user.PhoneNumber || '';
    document.getElementById('sub-email').value = user.SubEmail || '';
    document.getElementById('sub-phone-number').value = user.SubPhoneNumber || '';
    document.getElementById('address').value = user.Address || '';
    document.getElementById('line-id').value = user.LineID || '';

    // Employed date
    if (user.EmployedDate) {
        const formattedDate = user.EmployedDate.split('T')[0];
        document.getElementById('employed-date').value = formattedDate;
    }

    // Enabled status (default to true if null/undefined)
    const isEnabled = user.Enabled !== false;
    updateEnabledUI(isEnabled);
}

/**
 * Update Enabled checkbox UI
 */
function updateEnabledUI(isEnabled) {
    const checkbox = document.getElementById('user-enabled');
    const statusText = document.getElementById('enabledStatusText');
    const badge = document.getElementById('enabledBadge');
    const label = document.getElementById('enabledLabel');

    checkbox.checked = isEnabled;

    if (isEnabled) {
        statusText.textContent = 'Enabled';
        badge.textContent = 'Active';
        badge.className = 'badge badge-success ml-auto';
        label.classList.remove('border-error', 'bg-error/10');
    } else {
        statusText.textContent = 'Disabled';
        badge.textContent = 'Inactive';
        badge.className = 'badge badge-error ml-auto';
        label.classList.add('border-error', 'bg-error/10');
    }
}

/**
 * Handle Enabled checkbox change - show confirmation modal
 */
function confirmEnabledChange(event) {
    const checkbox = document.getElementById('user-enabled');
    // checkbox.checked is already the NEW state after user clicked
    const newState = checkbox.checked;
    
    // Immediately revert to original state - we'll apply change only after confirmation
    checkbox.checked = !newState;
    
    // Store the pending state (the state user wants to change to)
    enabledPendingState = newState;
    
    // Update modal content based on action
    const modalTitle = document.getElementById('enabledModalTitle');
    const modalMessage = document.getElementById('enabledModalMessage');
    const confirmBtn = document.getElementById('enabledConfirmBtn');
    
    if (newState) {
        // Enabling user
        modalTitle.innerHTML = '<i class="fas fa-check-circle text-success"></i> Enable User Account';
        modalMessage.innerHTML = `
            <div class="alert alert-success">
                <i class="fas fa-info-circle"></i>
                <span>คุณต้องการ <strong>เปิดใช้งาน</strong> บัญชีผู้ใช้นี้หรือไม่?</span>
            </div>
            <p class="mt-2 text-sm">ผู้ใช้จะสามารถเข้าสู่ระบบได้อีกครั้ง</p>
        `;
        confirmBtn.className = 'btn btn-success';
        confirmBtn.innerHTML = '<i class="fas fa-check"></i> Enable';
    } else {
        // Disabling user
        modalTitle.innerHTML = '<i class="fas fa-exclamation-triangle text-error"></i> Disable User Account';
        modalMessage.innerHTML = `
            <div class="alert alert-error">
                <i class="fas fa-exclamation-triangle"></i>
                <span>คุณต้องการ <strong>ปิดใช้งาน</strong> บัญชีผู้ใช้นี้หรือไม่?</span>
            </div>
            <p class="mt-2 text-sm">ผู้ใช้จะไม่สามารถเข้าสู่ระบบได้จนกว่าจะเปิดใช้งานอีกครั้ง</p>
        `;
        confirmBtn.className = 'btn btn-error';
        confirmBtn.innerHTML = '<i class="fas fa-ban"></i> Disable';
    }
    
    // Show modal
    document.getElementById('enabledConfirmModal').showModal();
}

/**
 * Cancel Enabled change - revert checkbox
 */
function cancelEnabledChange() {
    enabledPendingState = null;
    document.getElementById('enabledConfirmModal').close();
    // Checkbox state remains unchanged (we prevented the change)
}

/**
 * Apply Enabled change after confirmation
 */
function applyEnabledChange() {
    if (enabledPendingState !== null) {
        updateEnabledUI(enabledPendingState);
    }
    enabledPendingState = null;
    document.getElementById('enabledConfirmModal').close();
}

/**
 * Initialize Report To and Coach dropdowns
 */
function initializeDropdowns(user) {
    getUsers(function(err, users) {
        if (err) {
            console.error(err);
            xalert("Error while fetching users", 1, null);
            return;
        }

        const reportToSelect = document.getElementById('report-to');
        const coachSelect = document.getElementById('coach');
        const individualPermUserSelect = document.getElementById('individualPermUser');

        users.forEach(u => {
            const displayText = `${u.FirstName || ''} ${u.LastName || ''}`.trim() || u.username;

            // Report To
            const reportOption = document.createElement('option');
            reportOption.value = u.Id;
            reportOption.textContent = displayText;
            reportToSelect.appendChild(reportOption);

            // Coach
            const coachOption = document.createElement('option');
            coachOption.value = u.Id;
            coachOption.textContent = displayText;
            coachSelect.appendChild(coachOption);

            // Individual Permission User
            const permUserOption = document.createElement('option');
            permUserOption.value = u.Id;
            permUserOption.textContent = displayText;
            individualPermUserSelect.appendChild(permUserOption);
        });

        // Set current values
        if (user.ReportToID) {
            reportToSelect.value = user.ReportToID;
        }
        if (user.CoachID) {
            coachSelect.value = user.CoachID;
        }

        // Initialize individual permission types dropdown
        initializeIndividualPermTypes();
    });
}

/**
 * Initialize Individual Permission Types dropdown
 */
function initializeIndividualPermTypes() {
    const permTypeSelect = document.getElementById('individualPermType');
    
    // permissionsTypeIndividual is defined in biomed-global.js
    if (typeof permissionsTypeIndividual !== 'undefined') {
        permissionsTypeIndividual.forEach(perm => {
            const option = document.createElement('option');
            option.value = perm.value;
            option.textContent = perm.name;
            if (perm.description) {
                option.setAttribute('data-description', perm.description);
            }
            permTypeSelect.appendChild(option);
        });
    }
}

/**
 * Initialize MultiSelect components
 */
function initializeMultiSelects(user) {
    // Products MultiSelect
    getProducts(function(err, products) {
        if (err) {
            console.error('Error fetching products:', err);
            return;
        }

        const productOptions = products.map(p => ({
            value: p.Id,
            label: p.Name,
            badge: p.Description || null
        }));

        productsMultiSelect = new MultiSelect('productsMultiSelect', {
            options: productOptions,
            placeholder: 'เลือก Products...',
            badgeClass: 'badge-info',
            checkboxClass: 'checkbox-info',
            searchable: true,
            showSelectAll: true,
            text: {
                search: 'ค้นหา Product...',
                selectAll: 'เลือกทั้งหมด',
                clearAll: 'ล้างทั้งหมด',
                noResults: 'ไม่พบ Product'
            },
            onChange: (values) => {
                console.log('Products selected:', values);
            }
        });

        // Set current user's products
        if (user.ProductUsers && user.ProductUsers.length > 0) {
            const productIds = user.ProductUsers.map(pu => pu.ProductId);
            productsMultiSelect.setValues(productIds);
        }
    });

    // Sale Areas MultiSelect
    getSaleAreas(function(err, saleAreas) {
        if (err) {
            console.error('Error fetching sale areas:', err);
            return;
        }

        const saleAreaOptions = saleAreas.map(sa => ({
            value: sa.Id,
            label: sa.Name,
            badge: sa.Description || null
        }));

        saleAreasMultiSelect = new MultiSelect('saleAreasMultiSelect', {
            options: saleAreaOptions,
            placeholder: 'เลือก Sale Areas...',
            badgeClass: 'badge-warning',
            checkboxClass: 'checkbox-warning',
            searchable: true,
            showSelectAll: true,
            text: {
                search: 'ค้นหา Sale Area...',
                selectAll: 'เลือกทั้งหมด',
                clearAll: 'ล้างทั้งหมด',
                noResults: 'ไม่พบ Sale Area'
            },
            onChange: (values) => {
                console.log('Sale Areas selected:', values);
            }
        });

        // Set current user's sale areas
        if (user.SaleAreaUsers && user.SaleAreaUsers.length > 0) {
            const saleAreaIds = user.SaleAreaUsers.map(sau => sau.SaleAreaId);
            saleAreasMultiSelect.setValues(saleAreaIds);
        }
    });

    // Permissions MultiSelect
    // permissionsType is defined in biomed-global.js
    if (typeof permissionsType !== 'undefined') {
        const permOptions = permissionsType.map(p => ({
            value: p.value,
            label: p.name,
            badge: p.description || null
        }));

        permissionsMultiSelect = new MultiSelect('permissionsMultiSelect', {
            options: permOptions,
            placeholder: 'เลือก Permissions...',
            badgeClass: 'badge-error',
            checkboxClass: 'checkbox-error',
            searchable: true,
            showSelectAll: true,
            text: {
                search: 'ค้นหา Permission...',
                selectAll: 'เลือกทั้งหมด',
                clearAll: 'ล้างทั้งหมด',
                noResults: 'ไม่พบ Permission'
            },
            onChange: (values) => {
                console.log('Permissions selected:', values);
            }
        });

        // Set current user's permissions (system permissions only, not individual)
        if (user.Permissions && user.Permissions.length > 0) {
            const systemPermissions = user.Permissions
                .filter(p => {
                    // System permissions are those in permissionsType
                    return permissionsType.some(pt => pt.name === p.Type) && 
                           (p.Value === 'Allow' || p.Value === 3);
                })
                .map(p => {
                    const pt = permissionsType.find(pt => pt.name === p.Type);
                    return pt ? pt.value : null;
                })
                .filter(v => v !== null);
            
            permissionsMultiSelect.setValues(systemPermissions);
        }
    }
}

/**
 * Initialize Individual Permissions
 */
function initializeIndividualPermissions(user) {
    individualPermissions = [];

    if (user.Permissions && user.Permissions.length > 0) {
        // Individual permissions are those in permissionsTypeIndividual with a PermissionKey
        user.Permissions.forEach(p => {
            if (typeof permissionsTypeIndividual !== 'undefined') {
                const isIndividual = permissionsTypeIndividual.some(pt => pt.name === p.Type);
                if (isIndividual && (p.Value === 'Allow' || p.Value === 3) && p.PermissionKey) {
                    const pt = permissionsTypeIndividual.find(pt => pt.name === p.Type);
                    if (pt) {
                        individualPermissions.push({
                            userId: p.PermissionKey,
                            permissionType: pt.value
                        });
                    }
                }
            }
        });
    }

    renderIndividualPermissions();
}

/**
 * Add individual permission
 */
function addIndividualPermission() {
    const userSelect = document.getElementById('individualPermUser');
    const permSelect = document.getElementById('individualPermType');

    const userId = userSelect.value;
    const permType = permSelect.value;

    if (!userId || !permType) {
        xalert("Please select both user and permission type", 1, null);
        return;
    }

    // Check if already exists
    const exists = individualPermissions.some(
        ip => ip.userId === userId && ip.permissionType === parseInt(permType)
    );

    if (exists) {
        xalert("This permission already exists", 1, null);
        return;
    }

    individualPermissions.push({
        userId: userId,
        permissionType: parseInt(permType)
    });

    // Reset selects
    userSelect.value = '';
    permSelect.value = '';

    renderIndividualPermissions();
}

/**
 * Remove individual permission
 */
function removeIndividualPermission(userId, permType) {
    individualPermissions = individualPermissions.filter(
        ip => !(ip.userId === userId && ip.permissionType === parseInt(permType))
    );
    renderIndividualPermissions();
}

/**
 * Render individual permissions list
 */
function renderIndividualPermissions() {
    const container = document.getElementById('individualPermissionsList');

    if (individualPermissions.length === 0) {
        container.innerHTML = '<span class="text-base-content/50 text-sm">No individual permissions</span>';
        return;
    }

    const userSelect = document.getElementById('individualPermUser');

    container.innerHTML = individualPermissions.map(ip => {
        // Get user name
        const userOption = Array.from(userSelect.options).find(o => o.value === ip.userId);
        const userName = userOption ? userOption.textContent : `User ${ip.userId}`;

        // Get permission name
        let permName = `Permission ${ip.permissionType}`;
        if (typeof permissionsTypeIndividual !== 'undefined') {
            const perm = permissionsTypeIndividual.find(p => p.value === ip.permissionType);
            if (perm) permName = perm.name;
        }

        return `
            <div class="badge badge-lg badge-outline gap-2" data-user="${ip.userId}" data-perm="${ip.permissionType}">
                <span class="font-medium">${userName}</span>
                <span class="text-primary">⚡</span>
                <span>${permName}</span>
                <button type="button" class="btn btn-ghost btn-xs btn-circle text-error" onclick="removeIndividualPermission('${ip.userId}', ${ip.permissionType})">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
    }).join('');
}

/**
 * Save user data
 */
function saveUserData() {
    if (!id) {
        xalert("No id please check your url", 1, null);
        return;
    }

    // Collect form data
    const data = {
        Id: id,
        Username: document.getElementById('username').value,
        Password: document.getElementById('password').value || null,
        ProfilePic: null,
        FirstName: document.getElementById('first-name').value,
        LastName: document.getElementById('last-name').value,
        MiddleName: document.getElementById('middle-name').value,
        Position: document.getElementById('position').value,
        Email: document.getElementById('email').value,
        SaleCode: "Obsoleted",
        PhoneNumber: document.getElementById('phone-number').value,
        SubEmail: document.getElementById('sub-email').value,
        SubPhoneNumber: document.getElementById('sub-phone-number').value,
        Address: document.getElementById('address').value,
        LineID: document.getElementById('line-id').value,
        AreaCode: "Obsoleted",
        ReportToID: document.getElementById('report-to').value || null,
        CoachID: document.getElementById('coach').value || null,
        Products: "Obsoleted",
        EmployedDate: timeFormater(document.getElementById('employed-date').value),
        Enabled: document.getElementById('user-enabled').checked
    };

    // Collect permissions
    const permissions = [];

    // System permissions from MultiSelect
    if (permissionsMultiSelect) {
        const selectedPerms = permissionsMultiSelect.getValues();
        selectedPerms.forEach(permValue => {
            permissions.push({
                Type: parseInt(permValue),
                Value: 3
            });
        });
    }

    // Individual permissions
    individualPermissions.forEach(ip => {
        permissions.push({
            Type: ip.permissionType,
            Value: 3,
            PermissionKey: ip.userId
        });
    });

    data.Permissions = permissions;

    // Products from MultiSelect
    if (productsMultiSelect) {
        data.ProductIDs = productsMultiSelect.getValues().map(v => parseInt(v));
    } else {
        data.ProductIDs = [];
    }

    // Sale Areas from MultiSelect
    if (saleAreasMultiSelect) {
        data.SaleAreaIDs = saleAreasMultiSelect.getValues().map(v => parseInt(v));
    } else {
        data.SaleAreaIDs = [];
    }

    console.log('Saving user data:', data);

    // Send to API
    const xhr = new XMLHttpRequest();
    xhr.open('POST', url + '/biomedapi/users/update');
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.setRequestHeader('Authorization', 'Bearer ' + readToken());
    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4) {
            if (xhr.status === 200) {
                console.log('User updated successfully');
                
                // Clear user caches to force refresh
                sessionStorage.removeItem("users");
                
                // If editing own profile, refresh myUser cache
                myUserRequest(function(err, myUser) {
                    if (!err && myUser && String(myUser.Id) === String(id)) {
                        // This is the logged-in user, refresh their cache
                        sessionStorage.removeItem("myUser");
                        myUserRequest(function() {}, true); // Force refresh
                    }
                });
                
                xalert("User updated successfully", 0, -1);
                
                // Update breadcrumb
                const displayName = `${data.FirstName || ''} ${data.LastName || ''}`.trim() || data.Username;
                document.getElementById('breadcrumbUserName').textContent = displayName;
            } else {
                console.error('Error while updating user:', xhr.status, xhr.responseText);
                xalert("Error while updating user: " + xhr.status + " - " + xhr.responseText, 1, null);
            }
        }
    };
    xhr.send(JSON.stringify(data));
}

/**
 * Delete user
 */
function deleteUser() {
    if (!confirm("Are you sure you want to delete this user?\n\nThis action cannot be undone.")) {
        return;
    }

    const xhr = new XMLHttpRequest();
    xhr.open('POST', url + '/biomedapi/users/delete');
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.setRequestHeader('Authorization', `Bearer ${readToken()}`);
    xhr.onload = function() {
        if (xhr.status === 200) {
            // Clear user cache
            sessionStorage.removeItem("users");
            
            xalert("User deleted successfully", 0, null);
            setTimeout(() => {
                window.location.href = 'management.html';
            }, 1500);
        } else {
            xalert("Failed to delete user: " + xhr.responseText, 1, null);
        }
    };
    xhr.onerror = function() {
        xalert("Failed to send request", 1, null);
    };
    xhr.send(JSON.stringify({ id: id }));
}

// ==================== Profile Picture Upload ====================

function resizeImage(image, maxWidth, maxHeight) {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');

    let width = image.width;
    let height = image.height;

    if (width < height) {
        if (width > maxWidth) {
            height *= maxWidth / width;
            width = maxWidth;
        }
    } else {
        if (height > maxHeight) {
            width *= maxHeight / height;
            height = maxHeight;
        }
    }

    canvas.width = width;
    canvas.height = height;

    ctx.fillStyle = 'white';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(image, 0, 0, width, height);

    return canvas.toDataURL('image/jpeg');
}

function cropImage(imageDataUrl, size) {
    return new Promise((resolve, reject) => {
        const image = new Image();
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');

        canvas.width = size;
        canvas.height = size;

        image.onload = function() {
            const width = image.width;
            const height = image.height;

            const x = (width - size) / 2;
            const y = (height - size) / 2;

            ctx.drawImage(image, x, y, size, size, 0, 0, size, size);
            resolve(canvas.toDataURL('image/jpeg'));
        };

        image.onerror = reject;
        image.src = imageDataUrl;
    });
}

function processImage(file) {
    const reader = new FileReader();
    reader.onload = function(event) {
        const image = new Image();
        image.onload = async function() {
            const resizedImageDataUrl = resizeImage(image, 300, 300);
            try {
                const croppedImageDataUrl = await cropImage(resizedImageDataUrl, 300);
                
                // Update preview immediately
                document.getElementById('profilePicPreview').src = croppedImageDataUrl;
                
                const formData = new FormData();
                formData.append('file', dataURItoBlob(croppedImageDataUrl));
                
                const xhr = new XMLHttpRequest();
                xhr.open('POST', url + '/biomedapi/upload/profile/' + id, true);
                xhr.setRequestHeader('Authorization', 'Bearer ' + readToken());
                xhr.onreadystatechange = function() {
                    if (xhr.readyState === 4) {
                        if (xhr.status === 200) {
                            xalert('Profile picture uploaded successfully', 0, 5000);
                            
                            // Refresh user cache
                            myUserRequest(function(err, response) {
                                if (err) {
                                    console.log(err);
                                }
                            }, true);
                        } else {
                            xalert(xhr.status + '-' + xhr.responseText, 1, -1);
                        }
                    }
                };
                xhr.send(formData);
            } catch (error) {
                console.error("Error cropping image:", error);
                xalert("Error processing image", 1, null);
            }
        };
        image.src = event.target.result;
    };
    reader.readAsDataURL(file);
}

function dataURItoBlob(dataURI) {
    const byteString = atob(dataURI.split(',')[1]);
    const mimeString = dataURI.split(',')[0].split(':')[1].split(';')[0];
    const ab = new ArrayBuffer(byteString.length);
    const ia = new Uint8Array(ab);
    for (let i = 0; i < byteString.length; i++) {
        ia[i] = byteString.charCodeAt(i);
    }
    return new Blob([ab], { type: mimeString });
}

function uploadProfilePic() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/*';
    input.onchange = function(event) {
        const file = event.target.files[0];
        if (file) {
            processImage(file);
        }
    };
    input.click();
}
