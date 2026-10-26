// ============================================================
// biomed-manage.js
// Management page JavaScript for daisyUI version
// Handles Users, Groups, Products, Sale Areas CRUD operations
// ============================================================

// Alert helper for daisyUI - using alert-bar div
const showAlert = (message, type = 'info', duration = 5000) => {
    const container = document.getElementById('alert-bar');
    if (!container) {
        // Fallback to xalert if available
        if (typeof xalert === 'function') {
            xalert(message, type === 'error' ? 1 : (type === 'warning' ? 2 : 0), duration);
        }
        return;
    }

    const alertTypes = {
        0: 'alert-success',
        1: 'alert-error', 
        2: 'alert-warning',
        'success': 'alert-success',
        'error': 'alert-error',
        'warning': 'alert-warning',
        'info': 'alert-info'
    };

    const alertClass = alertTypes[type] || 'alert-info';
    const icons = {
        'alert-success': '<svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>',
        'alert-error': '<svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>',
        'alert-warning': '<svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>',
        'alert-info': '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="stroke-current shrink-0 w-6 h-6"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>'
    };

    const alertDiv = document.createElement('div');
    alertDiv.className = `alert ${alertClass} shadow-lg mb-2`;
    alertDiv.innerHTML = `${icons[alertClass]}<span>${message}</span>`;
    
    container.appendChild(alertDiv);

    if (duration && duration > 0) {
        setTimeout(() => {
            alertDiv.classList.add('opacity-0', 'transition-opacity', 'duration-300');
            setTimeout(() => alertDiv.remove(), 300);
        }, duration);
    }
};

// Page initialization
window.onload = function() {
    loadUsers();
    loadGroups();
    loadProducts();
    loadSaleAreas();
};

// ============================================================
// USERS MANAGEMENT
// ============================================================

function loadUsers() {
    const usersListContent = document.getElementById('usersListContent');
    if (!usersListContent) return;

    usersListContent.innerHTML = `
        <div class="flex items-center justify-center py-8 text-base-content/50">
            <span class="loading loading-spinner loading-md mr-2"></span>
            กำลังโหลด...
        </div>
    `;

    // includeDisabled = true for management page to show all users
    getUsers(async function(err, users) {
        if (err) {
            showAlert(err, 'error');
            usersListContent.innerHTML = '<div class="text-center text-error py-4">Error loading users</div>';
            return;
        }

        usersListContent.innerHTML = '';
        
        // Update count
        const userCount = document.getElementById('userCount');
        if (userCount) userCount.textContent = users.length;
        
        for (const user of users) {
            try {
                const color = await getColor(user.Id);
                const card = document.createElement('div');
                
                // Check if user is disabled
                const isDisabled = user.Enabled === false;
                
                card.className = 'item-card flex items-center justify-between p-3 rounded-lg border border-base-200' + 
                    (isDisabled ? ' opacity-60' : '');
                
                // Generate initials for fallback avatar
                const initials = `${user.FirstName?.[0] || ''}${user.LastName?.[0] || 'U'}`.toUpperCase();
                const fallbackUrl = `/crm/assets/default-avatar.svg ? '6b7280' : '6366f1'}&color=fff&size=100`;
                
                const profilePic = user.ProfilePic && user.ProfilePic !== '00000000-0000-0000-0000-000000000000' 
                    ? `assets/profile/${user.ProfilePic}.jpg`
                    : fallbackUrl;

                // Status badge
                const statusBadge = isDisabled 
                    ? '<span class="badge badge-error badge-xs ml-1">Disabled</span>'
                    : '';

                card.innerHTML = `
                    <div class="flex items-center gap-3">
                        <div class="avatar ${isDisabled ? 'grayscale' : ''}">
                            <div class="mask mask-squircle w-12 h-12">
                                <img src="${profilePic}" alt="Profile" onerror="this.src='${fallbackUrl}'" />
                            </div>
                        </div>
                        <div>
                            <div class="font-semibold">${user.FirstName || ''} ${user.LastName || ''}${statusBadge}</div>
                            <div class="text-xs text-base-content/60">@${user.username || ''} • ID: ${user.Id}</div>
                            <span class="badge badge-xs mt-1" style="background-color: ${color.color.code}; color: ${color.textColor}">${color.color.name}</span>
                        </div>
                    </div>
                    <div class="flex gap-1">
                        <a href="./management-detail.html?id=${user.Id}" class="btn btn-primary btn-xs">Edit</a>
                        <a href="./d3.html?type=Users&id=${user.Id}" class="btn btn-ghost btn-xs"><i class="fas fa-project-diagram"></i></a>
                    </div>
                `;
                
                usersListContent.appendChild(card);
            } catch (e) {
                console.error('Error processing user:', user, e);
            }
        }
    }, false, true); // force=false, includeDisabled=true
}

function addUser() {
    // Reset form
    const fields = ['username', 'password', 'firstName', 'lastName', 'middleName', 'position', 'email', 'saleCode', 'phoneNumber', 'areaCode'];
    fields.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.value = '';
    });
    
    document.getElementById('userModal').showModal();
}

function addUserRequest() {
    const username = document.getElementById('username')?.value || '';
    const password = document.getElementById('password')?.value || '';
    const firstName = document.getElementById('firstName')?.value || '';
    const lastName = document.getElementById('lastName')?.value || '';
    const middleName = document.getElementById('middleName')?.value || '';
    const position = document.getElementById('position')?.value || '';
    const email = document.getElementById('email')?.value || '';
    const saleCode = document.getElementById('saleCode')?.value || '';
    const phoneNumber = document.getElementById('phoneNumber')?.value || '';
    const areaCode = document.getElementById('areaCode')?.value || '';

    if (!username || !password) {
        showAlert('Username and password must not be empty', 'warning');
        return;
    }

    const user = {
        Username: username,
        Password: password,
        ProfilePic: '00000000-0000-0000-0000-000000000000',
        FirstName: firstName,
        LastName: lastName,
        MiddleName: middleName,
        Position: position,
        Email: email,
        SaleCode: saleCode,
        PhoneNumber: phoneNumber,
        SubEmail: '',
        SubPhoneNumber: '',
        Address: '',
        LineID: '',
        AreaCode: areaCode,
        ReportToID: null,
        CoachID: null,
        Products: '',
        EmployedDate: new Date(),
        Permissions: []
    };

    createUser(user, function(err) {
        document.getElementById('userModal').close();
        if (err) {
            showAlert(err, 'error');
            return;
        }
        showAlert('User created successfully', 'success');
        loadUsers();
    });
}

function createUser(user, callback) {
    const xhr = new XMLHttpRequest();
    const urlx = '/biomedapi/users/create';
    const token = readToken();

    xhr.open('POST', url + urlx, true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.setRequestHeader('Authorization', 'Bearer ' + token);

    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4) {
            if (xhr.status === 200) {
                callback(null);
            } else {
                callback('Error creating user');
            }
        }
    };

    xhr.send(JSON.stringify(user));
}

function refreshUser() {
    getUsers(function(err, users) {
        if (err) {
            showAlert(err, 'error');
        } else {
            loadUsers();
        }
    }, true);
}

// ============================================================
// GROUPS MANAGEMENT
// ============================================================

function loadGroups() {
    const groupListContent = document.getElementById('groupListContent');
    if (!groupListContent) return;

    groupListContent.innerHTML = `
        <div class="flex items-center justify-center py-8 text-base-content/50">
            <span class="loading loading-spinner loading-md mr-2"></span>
            กำลังโหลด...
        </div>
    `;

    getGroups(function(error, groups) {
        if (error) {
            showAlert(error, 'error');
            groupListContent.innerHTML = '<div class="text-center text-error py-4">Error loading groups</div>';
            return;
        }

        groupListContent.innerHTML = '';
        
        // Update count
        const groupCount = document.getElementById('groupCount');
        if (groupCount) groupCount.textContent = groups.length;
        
        groups.forEach(function(group) {
            const card = document.createElement('div');
            card.className = 'item-card flex items-center justify-between p-3 rounded-lg border border-base-200';
            
            card.innerHTML = `
                <div class="flex items-center gap-3">
                    <div class="avatar placeholder">
                        <div class="bg-secondary text-secondary-content rounded-full w-10 flex items-center justify-center">
                            <span class="text-lg">${(group.GroupName || 'G').charAt(0).toUpperCase()}</span>
                        </div>
                    </div>
                    <div>
                        <div class="font-semibold">${group.GroupName || 'Unnamed Group'}</div>
                        <div class="text-xs text-base-content/60">ID: ${group.Id}</div>
                    </div>
                </div>
                <a href="./management-group.html?id=${group.Id}" class="btn btn-secondary btn-xs">Edit</a>
            `;
            
            groupListContent.appendChild(card);
        });
    }, true);
}

function addGroup() {
    const groupNameEl = document.getElementById('groupName');
    if (groupNameEl) groupNameEl.value = '';
    document.getElementById('groupModal').showModal();
}

function createGroupRequest() {
    const groupName = document.getElementById('groupName')?.value || '';

    if (!groupName) {
        showAlert('Group name is required', 'warning');
        return;
    }

    const createGroupData = {
        GroupName: groupName,
        UserIds: []
    };

    createGroup(createGroupData, function(err) {
        document.getElementById('groupModal').close();
        if (err) {
            showAlert(err, 'error');
            return;
        }
        showAlert('Group created successfully', 'success');
        loadGroups();
    });
}

function createGroup(group, callback) {
    const xhr = new XMLHttpRequest();
    const urlx = '/biomedapi/groups/create';
    const token = readToken();

    xhr.open('POST', url + urlx, true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.setRequestHeader('Authorization', 'Bearer ' + token);

    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4) {
            if (xhr.status === 200) {
                callback(null);
            } else {
                callback('Error creating group');
            }
        }
    };

    xhr.send(JSON.stringify(group));
}

function refreshGroup() {
    getGroups(function(err, groups) {
        if (err) {
            showAlert(err, 'error');
        } else {
            loadGroups();
        }
    }, true);
}

// ============================================================
// PRODUCTS MANAGEMENT
// ============================================================

function loadProducts() {
    const productsListContent = document.getElementById('productsListContent');
    if (!productsListContent) return;

    productsListContent.innerHTML = `
        <div class="flex items-center justify-center py-8 text-base-content/50">
            <span class="loading loading-spinner loading-md mr-2"></span>
            กำลังโหลด...
        </div>
    `;

    getProducts(function(error, products) {
        if (error) {
            showAlert(error, 'error');
            productsListContent.innerHTML = '<div class="text-center text-error py-4">Error loading products</div>';
            return;
        }

        productsListContent.innerHTML = '';
        
        // Update count
        const productCount = document.getElementById('productCount');
        if (productCount) productCount.textContent = products.length;
        
        products.forEach(function(product) {
            const card = document.createElement('div');
            card.className = 'item-card flex items-center justify-between p-3 rounded-lg border border-base-200';
            
            card.innerHTML = `
                <div class="flex items-center gap-3">
                    <div class="avatar placeholder">
                        <div class="bg-accent text-accent-content rounded-lg w-10 flex items-center justify-center">
                            <i class="fas fa-box"></i>
                        </div>
                    </div>
                    <div>
                        <div class="font-semibold">${product.Name || 'Unnamed Product'}</div>
                        <div class="text-xs text-base-content/60">ID: ${product.Id}${product.Code ? ' • Code: ' + product.Code : ''}</div>
                    </div>
                </div>
                <a href="./management-product.html?id=${product.Id}" class="btn btn-accent btn-xs">Edit</a>
            `;
            
            productsListContent.appendChild(card);
        });
    });
}

function addProduct() {
    const fields = ['productName', 'productDescription'];
    fields.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.value = '';
    });
    document.getElementById('productModal').showModal();
}

function createProductRequest() {
    const productName = document.getElementById('productName')?.value || '';
    const productDescription = document.getElementById('productDescription')?.value || '';

    if (!productName) {
        showAlert('Product name is required', 'warning');
        return;
    }

    const productData = {
        Name: productName,
        Description: productDescription
    };

    createProduct(productData, function(err) {
        document.getElementById('productModal').close();
        if (err) {
            showAlert(err, 'error');
            return;
        }
        showAlert('Product created successfully', 'success');
        loadProducts();
    });
}

function createProduct(product, callback) {
    const xhr = new XMLHttpRequest();
    const urlx = '/biomedapi/products/create';
    const token = readToken();

    xhr.open('POST', url + urlx, true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.setRequestHeader('Authorization', 'Bearer ' + token);

    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4) {
            if (xhr.status === 200) {
                callback(null);
            } else {
                callback('Error creating product');
            }
        }
    };

    xhr.send(JSON.stringify(product));
}

function refreshProduct() {
    getProducts(function(err, products) {
        if (err) {
            showAlert(err, 'error');
        } else {
            loadProducts();
        }
    }, true);
}

// ============================================================
// SALE AREAS MANAGEMENT
// ============================================================

function loadSaleAreas() {
    const saleAreaListContent = document.getElementById('saleAreaListContent');
    if (!saleAreaListContent) return;

    saleAreaListContent.innerHTML = `
        <div class="flex items-center justify-center py-8 text-base-content/50">
            <span class="loading loading-spinner loading-md mr-2"></span>
            กำลังโหลด...
        </div>
    `;

    getSaleAreas(function(error, saleAreas) {
        if (error) {
            showAlert(error, 'error');
            saleAreaListContent.innerHTML = '<div class="text-center text-error py-4">Error loading sale areas</div>';
            return;
        }

        saleAreaListContent.innerHTML = '';
        
        // Update count
        const saleAreaCount = document.getElementById('saleAreaCount');
        if (saleAreaCount) saleAreaCount.textContent = saleAreas.length;
        
        saleAreas.forEach(function(saleArea) {
            const card = document.createElement('div');
            card.className = 'item-card flex items-center justify-between p-3 rounded-lg border border-base-200';
            
            card.innerHTML = `
                <div class="flex items-center gap-3">
                    <div class="avatar placeholder">
                        <div class="bg-info text-info-content rounded-lg w-10 flex items-center justify-center">
                            <i class="fas fa-map-marker-alt"></i>
                        </div>
                    </div>
                    <div>
                        <div class="font-semibold">${saleArea.Name || 'Unnamed Area'}</div>
                        <div class="text-xs text-base-content/60">ID: ${saleArea.Id}${saleArea.Code ? ' • Code: ' + saleArea.Code : ''}</div>
                    </div>
                </div>
                <a href="./management-salearea.html?id=${saleArea.Id}" class="btn btn-info btn-xs">Edit</a>
            `;
            
            saleAreaListContent.appendChild(card);
        });
    });
}

function addSaleArea() {
    const fields = ['saleAreaName', 'saleAreaDescription'];
    fields.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.value = '';
    });
    document.getElementById('saleAreaModal').showModal();
}

function createSaleAreaRequest() {
    const saleAreaName = document.getElementById('saleAreaName')?.value || '';
    const saleAreaDescription = document.getElementById('saleAreaDescription')?.value || '';

    if (!saleAreaName) {
        showAlert('Sale area name is required', 'warning');
        return;
    }

    const saleAreaData = {
        Name: saleAreaName,
        Description: saleAreaDescription
    };

    createSaleArea(saleAreaData, function(err) {
        document.getElementById('saleAreaModal').close();
        if (err) {
            showAlert(err, 'error');
            return;
        }
        showAlert('Sale area created successfully', 'success');
        loadSaleAreas();
    });
}

function createSaleArea(saleArea, callback) {
    const xhr = new XMLHttpRequest();
    const urlx = '/biomedapi/saleareas/create';
    const token = readToken();

    xhr.open('POST', url + urlx, true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.setRequestHeader('Authorization', 'Bearer ' + token);

    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4) {
            if (xhr.status === 200) {
                callback(null);
            } else {
                callback('Error creating sale area');
            }
        }
    };

    xhr.send(JSON.stringify(saleArea));
}

function refreshSaleArea() {
    getSaleAreas(function(err, saleAreas) {
        if (err) {
            showAlert(err, 'error');
        } else {
            loadSaleAreas();
        }
    }, true);
}
