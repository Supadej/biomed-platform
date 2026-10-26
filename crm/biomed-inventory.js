// Biomed Inventory Management JavaScript
// Author: Biomed Development Team
// Description: Handles inventory product and brand management functionality

// Global variables
let currentProducts = [];
let currentBrands = [];
let allBrands = [];

// API Configuration
const API_BASE_URL = url+'/biomedapi/v2/product';

// Initialize page when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializePage();
});

// Initialize the inventory page
function initializePage() {
    try {
        // Load initial data
        loadBrands();
        loadProducts();
        
        // Setup event listeners
        setupEventListeners();
        
        // Initialize multi-select dropdowns
        setTimeout(() => {
            initializeMultiSelect();
        }, 500);
        
        console.log('Inventory page initialized successfully');
    } catch (error) {
        console.error('Error initializing inventory page:', error);
        showError('Failed to initialize inventory page');
    }
}

// Setup event listeners
function setupEventListeners() {
    // Search input with debounce
    const searchInput = document.getElementById('queryTitle');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(searchInventory, 300));
    }
    
    // Tab change listeners
    const productTab = document.getElementById('products-tab');
    const brandTab = document.getElementById('brands-tab');
    
    if (productTab) {
        productTab.addEventListener('click', () => {
            setTimeout(loadProducts, 100);
        });
    }
    
    if (brandTab) {
        brandTab.addEventListener('click', () => {
            setTimeout(loadBrands, 100);
        });
    }
}

// Initialize multi-select dropdowns (no longer needed for brand dropdown)
function initializeMultiSelect() {
    // Brand dropdown is now a single select, so no multi-select initialization needed
    console.log('Multi-select initialization complete');
}

// Load all brands from API
async function loadBrands() {
    try {
        showLoading();
        
        const response = await fetch(`${API_BASE_URL}/brands`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${readToken()}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${await response.text()}`);
        }
        
        const result = await response.json();
        const brands = result.data || result;
        
        allBrands = brands;
        currentBrands = brands;
        
        // Populate brand dropdown for filtering
        populateBrandDropdown(brands);
        
        // Populate brand table
        populateBrandsTable(brands);
        
        // Populate brand dropdown in add/edit product modals
        populateProductBrandDropdowns(brands);
        
        hideLoading();
        
    } catch (error) {
        console.error('Error loading brands:', error);
        showError(`Failed to load brands: ${error.message}`);
        hideLoading();
    }
}

// Load all products from API
async function loadProducts() {
    try {
        showLoading();
        
        const response = await fetch(`${API_BASE_URL}/inventory`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${readToken()}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${await response.text()}`);
        }
        
        const result = await response.json();
        const products = result.data || result;
        
        currentProducts = products;
        populateProductsTable(products);
        
        hideLoading();
        
    } catch (error) {
        console.error('Error loading products:', error);
        showError(`Failed to load products: ${error.message}`);
        hideLoading();
    }
}

// Search inventory with filters
async function searchInventory() {
    try {
        showLoading();
        
        const searchCriteria = {
            Title: document.getElementById('queryTitle')?.value || undefined,
            BrandID: parseInt(document.getElementById('brandQuery')?.value) || undefined,
            ProductType: document.getElementById('productTypeQuery')?.value || undefined,
            BrandType: document.getElementById('brandTypeQuery')?.value || undefined,
            Distributor: document.getElementById('distributorQuery')?.value || undefined,
            Min: parseInt(document.getElementById('minStockQuery')?.value) || undefined,
            Max: parseInt(document.getElementById('maxStockQuery')?.value) || undefined,
            DeepDetails: false
        };
        
        // Remove undefined values
        Object.keys(searchCriteria).forEach(key => {
            if (searchCriteria[key] === undefined || searchCriteria[key] === '') {
                delete searchCriteria[key];
            }
        });
        
        const response = await fetch(`${API_BASE_URL}/inventory/get`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${readToken()}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(searchCriteria)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${await response.text()}`);
        }
        
        const result = await response.json();
        const products = result.data || result;
        
        currentProducts = products;
        populateProductsTable(products);
        
        hideLoading();
        
    } catch (error) {
        console.error('Error searching inventory:', error);
        showError(`Search failed: ${error.message}`);
        hideLoading();
    }
}

// Populate brand dropdown for filtering
function populateBrandDropdown(brands) {
    const dropdown = document.getElementById('brandQuery');
    if (!dropdown) return;
    
    // Keep the "All Brands" option and add brand options
    const currentValue = dropdown.value;
    dropdown.innerHTML = '<option value="">All Brands</option>';
    
    brands.forEach(brand => {
        const option = document.createElement('option');
        option.value = brand.Id;
        option.textContent = brand.Name;
        dropdown.appendChild(option);
    });
    
    // Restore previous selection if it still exists
    if (currentValue) {
        dropdown.value = currentValue;
    }
}

// Populate brand dropdowns in product modals
function populateProductBrandDropdowns(brands) {
    const addDropdown = document.getElementById('productBrand');
    const editDropdown = document.getElementById('editProductBrand');
    
    [addDropdown, editDropdown].forEach(dropdown => {
        if (dropdown) {
            const currentValue = dropdown.value;
            dropdown.innerHTML = '<option value="">Select a brand</option>';
            
            brands.forEach(brand => {
                const option = document.createElement('option');
                option.value = brand.Id;
                option.textContent = brand.Name;
                dropdown.appendChild(option);
            });
            
            if (currentValue) {
                dropdown.value = currentValue;
            }
        }
    });
}

// Populate products table
function populateProductsTable(products) {
    const tbody = document.getElementById('productsTableBody');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    if (!products || products.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="text-center py-8 text-base-content/50">No products found</td></tr>';
        return;
    }
    
    products.forEach(product => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>
                <a href="inventoryDetail.html?id=${product.Id}" class="link link-hover link-primary">
                    <strong>${escapeHtml(product.Name || 'N/A')}</strong>
                </a>
            </td>
            <td>${escapeHtml(product.CategoryNumber || 'N/A')}</td>
            <td>${escapeHtml(product.Brand?.Name || 'N/A')}</td>
            <td><span class="badge badge-primary">${escapeHtml(product.Type || 'N/A')}</span></td>
            <td><span class="badge badge-outline">${escapeHtml(product.Unit || 'N/A')}</span></td>
            <td><span class="badge ${getStockBadgeClass(product.StockCount)}">${product.StockCount || 0}</span></td>
            <td>${escapeHtml(truncateText(product.Description || 'N/A', 50))}</td>
            <td>
                <div class="join">
                    <button class="btn btn-primary btn-xs join-item" onclick="viewProduct(${product.Id})" title="View Details">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button class="btn btn-secondary btn-xs join-item" onclick="openEditProductModal(${product.Id})" title="Edit">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-error btn-xs join-item" onclick="confirmDeleteProduct(${product.Id}, '${escapeHtml(product.Name)}')" title="Delete">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </td>
        `;
        tbody.appendChild(row);
    });
}

// Populate brands table
function populateBrandsTable(brands) {
    const tbody = document.getElementById('brandsTableBody');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    if (!brands || brands.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center py-8 text-base-content/50">No brands found</td></tr>';
        return;
    }
    
    brands.forEach(brand => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><strong>${escapeHtml(brand.Name || 'N/A')}</strong></td>
            <td><span class="badge badge-secondary">${escapeHtml(brand.InventoryBrandType || 'N/A')}</span></td>
            <td><span class="badge badge-secondary">${escapeHtml(brand.InventoryBrandDistriutor || 'N/A')}</span></td>
            <td>${escapeHtml(truncateText(brand.Description || 'N/A', 50))}</td>
            <td>
                <div class="join">
                    <button class="btn btn-secondary btn-xs join-item" onclick="openEditBrandModal(${brand.Id})" title="Edit">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-error btn-xs join-item" onclick="confirmDeleteBrand(${brand.Id}, '${escapeHtml(brand.Name)}')" title="Delete">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </td>
        `;
        tbody.appendChild(row);
    });
}

// View product details
function viewProduct(productId) {
    window.location.href = `inventoryDetail.html?id=${productId}`;
}

// Open add product modal
function openAddProductModal() {
    const modal = document.getElementById('addProductModal');
    // Reset form fields
    document.getElementById('productName').value = '';
    document.getElementById('productDescription').value = '';
    document.getElementById('productBrand').value = '';
    document.getElementById('productType').value = '';
    document.getElementById('productCatNo').value = '';
    document.getElementById('productUnit').value = '';
    modal.showModal();
}

// Open add brand modal
function openAddBrandModal() {
    const modal = document.getElementById('addBrandModal');
    // Reset form fields
    document.getElementById('brandName').value = '';
    document.getElementById('brandDescription').value = '';
    document.getElementById('brandType').value = '';
    document.getElementById('brandDistributor').value = '';
    modal.showModal();
}

// Add new product
async function addProduct() {
    try {
        const formData = {
            Name: document.getElementById('productName').value,
            Description: document.getElementById('productDescription').value,
            BrandId: parseInt(document.getElementById('productBrand').value),
            Type: document.getElementById('productType').value,
            CatNo: document.getElementById('productCatNo').value,
            Unit: document.getElementById('productUnit').value
        };
        
        // Validate required fields
        if (!formData.Name || !formData.BrandId || !formData.Type) {
            showError('Please fill in all required fields');
            return;
        }
        
        const response = await fetch(`${API_BASE_URL}/inventory/create`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${readToken()}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${await response.text()}`);
        }
        
        const result = await response.json();
        
        showSuccess('Product added successfully');
        document.getElementById('addProductModal').close();
        loadProducts();
        
    } catch (error) {
        console.error('Error adding product:', error);
        showError(`Failed to add product: ${error.message}`);
    }
}

// Add new brand
async function addBrand() {
    try {
        const formData = {
            Name: document.getElementById('brandName').value,
            Description: document.getElementById('brandDescription').value,
            Type: document.getElementById('brandType').value,
            Distributor: document.getElementById('brandDistributor').value
        };
        
        // Validate required fields
        if (!formData.Name) {
            showError('Please enter a brand name');
            return;
        }
        
        const response = await fetch(`${API_BASE_URL}/brands/create`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${readToken()}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${await response.text()}`);
        }
        
        const result = await response.json();
        
        showSuccess('Brand added successfully');
        document.getElementById('addBrandModal').close();
        loadBrands();
        
    } catch (error) {
        console.error('Error adding brand:', error);
        showError(`Failed to add brand: ${error.message}`);
    }
}

// Open edit product modal
async function openEditProductModal(productId) {
    try {
        // Get product details
        const response = await fetch(`${API_BASE_URL}/inventory/${productId}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${readToken()}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${await response.text()}`);
        }
        
        const result = await response.json();
        const product = result.data || result;
        
        // Populate form
        document.getElementById('editProductId').value = product.Id;
        document.getElementById('editProductName').value = product.Name || '';
        document.getElementById('editProductDescription').value = product.Description || '';
        document.getElementById('editProductBrand').value = product.BrandId || '';
        document.getElementById('editProductType').value = product.Type || '';
        document.getElementById('editProductCatNo').value = product.CategoryNumber || '';
        document.getElementById('editProductUnit').value = product.Unit || '';
        
        // Show modal
        document.getElementById('editProductModal').showModal();
        
    } catch (error) {
        console.error('Error loading product for edit:', error);
        showError(`Failed to load product: ${error.message}`);
    }
}

// Open edit brand modal
async function openEditBrandModal(brandId) {
    try {
        // Get brand details
        const response = await fetch(`${API_BASE_URL}/brands/${brandId}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${readToken()}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${await response.text()}`);
        }
        
        const result = await response.json();
        const brand = result.data || result;
        
        // Populate form
        document.getElementById('editBrandId').value = brand.Id;
        document.getElementById('editBrandName').value = brand.Name || '';
        document.getElementById('editBrandDescription').value = brand.Description || '';
        document.getElementById('editBrandType').value = brand.InventoryBrandType || '';
        document.getElementById('editBrandDistributor').value = brand.InventoryBrandDistriutor || '';
        
        // Show modal
        document.getElementById('editBrandModal').showModal();
        
    } catch (error) {
        console.error('Error loading brand for edit:', error);
        showError(`Failed to load brand: ${error.message}`);
    }
}

// Update product
async function updateProduct() {
    try {
        const formData = {
            Id: parseInt(document.getElementById('editProductId').value),
            Name: document.getElementById('editProductName').value,
            Description: document.getElementById('editProductDescription').value,
            BrandId: parseInt(document.getElementById('editProductBrand').value),
            Type: document.getElementById('editProductType').value,
            CatNo: document.getElementById('editProductCatNo').value,
            Unit: document.getElementById('editProductUnit').value
        };
        
        // Validate required fields
        if (!formData.Name || !formData.BrandId || !formData.Type) {
            showError('Please fill in all required fields');
            return;
        }
        
        const response = await fetch(`${API_BASE_URL}/inventory/update`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${readToken()}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${await response.text()}`);
        }
        
        showSuccess('Product updated successfully');
        document.getElementById('editProductModal').close();
        loadProducts();
        
    } catch (error) {
        console.error('Error updating product:', error);
        showError(`Failed to update product: ${error.message}`);
    }
}

// Update brand
async function updateBrand() {
    try {
        const formData = {
            Id: parseInt(document.getElementById('editBrandId').value),
            Name: document.getElementById('editBrandName').value,
            Description: document.getElementById('editBrandDescription').value,
            Type: document.getElementById('editBrandType').value,
            Distributor: document.getElementById('editBrandDistributor').value
        };
        
        // Validate required fields
        if (!formData.Name) {
            showError('Please enter a brand name');
            return;
        }
        
        const response = await fetch(`${API_BASE_URL}/brands/update`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${readToken()}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${await response.text()}`);
        }
        
        showSuccess('Brand updated successfully');
        document.getElementById('editBrandModal').close();
        loadBrands();
        
    } catch (error) {
        console.error('Error updating brand:', error);
        showError(`Failed to update brand: ${error.message}`);
    }
}

// Confirm delete product
function confirmDeleteProduct(productId, productName) {
    if (confirm(`Are you sure you want to delete "${productName}"? This action cannot be undone.`)) {
        deleteProduct(productId);
    }
}

// Confirm delete brand
function confirmDeleteBrand(brandId, brandName) {
    if (confirm(`Are you sure you want to delete "${brandName}"? This will also delete all associated products.`)) {
        deleteBrand(brandId);
    }
}

// Delete product
async function deleteProduct(productId) {
    try {
        const response = await fetch(`${API_BASE_URL}/inventory/delete`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${readToken()}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ Id: productId })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${await response.text()}`);
        }
        
        showSuccess('Product deleted successfully');
        loadProducts();
        
    } catch (error) {
        console.error('Error deleting product:', error);
        showError(`Failed to delete product: ${error.message}`);
    }
}

// Delete brand
async function deleteBrand(brandId) {
    try {
        const response = await fetch(`${API_BASE_URL}/brands/delete`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${readToken()}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ Id: brandId })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${await response.text()}`);
        }
        
        showSuccess('Brand deleted successfully');
        loadBrands();
        
    } catch (error) {
        console.error('Error deleting brand:', error);
        showError(`Failed to delete brand: ${error.message}`);
    }
}

// Utility Functions

// Get stock badge class based on quantity
function getStockBadgeClass(stockCount) {
    if (stockCount === 0) return 'badge-error';
    if (stockCount < 10) return 'badge-warning';
    if (stockCount < 50) return 'badge-info';
    return 'badge-success';
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Truncate text
function truncateText(text, maxLength) {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

// Debounce function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Show loading indicator
function showLoading() {
    // Implementation depends on your loading component
    console.log('Loading...');
}

// Hide loading indicator
function hideLoading() {
    // Implementation depends on your loading component
    console.log('Loading complete');
}

// Show error message
function showError(message) {
    console.error('Error:', message);
    alert('Error: ' + message); // Replace with your preferred notification system
}

// Show success message
function showSuccess(message) {
    console.log('Success:', message);
    alert('Success: ' + message); // Replace with your preferred notification system
}

// Export functions for global access
window.searchInventory = searchInventory;
window.openAddProductModal = openAddProductModal;
window.openAddBrandModal = openAddBrandModal;
window.addProduct = addProduct;
window.addBrand = addBrand;
window.updateProduct = updateProduct;
window.updateBrand = updateBrand;
window.openEditProductModal = openEditProductModal;
window.openEditBrandModal = openEditBrandModal;
window.confirmDeleteProduct = confirmDeleteProduct;
window.confirmDeleteBrand = confirmDeleteBrand;
window.viewProduct = viewProduct;
