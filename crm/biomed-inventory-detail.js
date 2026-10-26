// Biomed Inventory Detail Management JavaScript
// Author: Biomed Development Team
// Description: Handles detailed inventory product management and stock operations
// Updated for daisyUI - uses native dialog element

// Global variables
let currentProduct = null;
let currentStocks = [];
let allBrands = [];

// API Configuration
const API_BASE_URL = url+'/biomedapi/v2/product';

// Initialize page when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeDetailPage();
});

// Initialize the inventory detail page
function initializeDetailPage() {
    try {
        // Get product ID from URL
        const urlParams = new URLSearchParams(window.location.search);
        const productId = urlParams.get('id');
        
        if (!productId) {
            showError('No product ID specified');
            goBack();
            return;
        }
        
        // Load product data
        loadProductDetails(productId);
        loadBrands();
        
        console.log('Inventory detail page initialized successfully');
    } catch (error) {
        console.error('Error initializing inventory detail page:', error);
        showError('Failed to initialize inventory detail page');
    }
}

// Load product details from API
async function loadProductDetails(productId) {
    try {
        showLoading();
        
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
        currentProduct = result.data || result;
        
        // Display product information
        displayProductInfo(currentProduct);
        
        // Display stock information
        currentStocks = currentProduct.Stocks || [];
        await displayStockInfo(currentStocks);
        
        hideLoading();
        
    } catch (error) {
        console.error('Error loading product details:', error);
        showError(`Failed to load product details: ${error.message}`);
        hideLoading();
    }
}

// Load all brands for dropdowns
async function loadBrands() {
    try {
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
        allBrands = result.data || result;
        
        // Populate brand dropdown in edit modal
        populateBrandDropdown();
        
    } catch (error) {
        console.error('Error loading brands:', error);
    }
}

// Display product information
function displayProductInfo(product) {
    console.log('Displaying product info:', product);
    document.getElementById('productTitle').innerHTML = `<i class="fa-solid fa-box text-primary mr-2"></i>${product.Name || 'Product Details'}`;
    document.getElementById('productName').textContent = product.Name || 'N/A';
    document.getElementById('productCatNo').textContent = product.CategoryNumber || 'N/A';
    document.getElementById('productType').textContent = product.Type || 'N/A';
    document.getElementById('productUnit').textContent = product.Unit || 'N/A';
    document.getElementById('productBrand').textContent = product.Brand?.Name || 'N/A';
    document.getElementById('brandType').textContent = product.Brand?.InventoryBrandType || 'N/A';
    document.getElementById('brandDistributor').textContent = product.Brand?.InventoryBrandDistriutor || 'N/A';
    document.getElementById('productDescription').textContent = product.Description || 'No description available';
    document.getElementById('totalStockCount').textContent = product.StockCount || 0;
}

// Display stock information
async function displayStockInfo(stocks) {
    const tbody = document.getElementById('stockTableBody');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    if (!stocks || stocks.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" class="text-center py-8 text-base-content/50">No stock records found</td></tr>';
        return;
    }
    
    // Process each stock record and fetch user information if UserId exists
    for (const stock of stocks) {
        let userInfo = 'N/A';
        
        // Fetch user information if UserId is provided
        if (stock.UserId) {
            try {
                const user = await promiseUserById(stock.UserId);
                userInfo = user ? `${user.FirstName} ${user.LastName}` : 'Unknown User';
            } catch (error) {
                console.error(`Error fetching user for UserId ${stock.UserId}:`, error);
                userInfo = 'Error loading user';
            }
        }
        
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><strong>${escapeHtml(stock.LotNumber || 'N/A')}</strong></td>
            <td><span class="badge ${getStockBadgeClass(stock.Quantity)}">${stock.Quantity || 0}</span></td>
            <td><span class="badge ${getStockTypeBadgeClass(stock.Type)}">${escapeHtml(stock.Type || 'N/A')}</span></td>
            <td>${formatDate(stock.ManufactureDate)}</td>
            <td>${formatDate(stock.ExpiryDate)}</td>
            <td>${formatDate(stock.IncomingDate)}</td>
            <td title="${escapeHtml(userInfo)}">${escapeHtml(truncateText(userInfo, 20))}</td>
            <td>${escapeHtml(truncateText(stock.Description || 'N/A', 30))}</td>
            <td class="text-center">
                <button class="btn btn-error btn-xs" onclick="openDeleteStockModal(${stock.Id}, '${escapeHtml(stock.LotNumber)}', ${stock.Quantity})" title="Delete Stock Record">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        `;
        tbody.appendChild(row);
    }
    
    // Update remove stock dropdown
    updateRemoveStockDropdown(stocks);
}

// Update remove stock dropdown with available lots
function updateRemoveStockDropdown(stocks) {
    const dropdown = document.getElementById('removeLotNumber');
    if (!dropdown) return;
    
    dropdown.innerHTML = '<option value="">Select lot number</option>';
    
    // Calculate net available quantity for each lot number
    const lotQuantities = {};
    
    console.log('Processing stocks for dropdown:', stocks);
    
    stocks.forEach(stock => {
        const lotNumber = stock.LotNumber;
        if (!lotQuantities[lotNumber]) {
            lotQuantities[lotNumber] = 0;
        }
        
        console.log(`Processing stock: Lot ${lotNumber}, Type: ${stock.Type}, Quantity: ${stock.Quantity}`);
        
        // Add incoming quantities and subtract outgoing quantities
        if (stock.Type === 'Incoming') {
            lotQuantities[lotNumber] += stock.Quantity || 0;
            console.log(`Added ${stock.Quantity} to lot ${lotNumber}, new total: ${lotQuantities[lotNumber]}`);
        } else if (stock.Type === 'Outgoing') {
            lotQuantities[lotNumber] += stock.Quantity || 0;
            console.log(`Subtracted ${stock.Quantity} from lot ${lotNumber}, new total: ${lotQuantities[lotNumber]}`);
        }
    });
    
    console.log('Final lot quantities:', lotQuantities);
    
    // Only show lots with positive available quantity
    Object.keys(lotQuantities).forEach(lotNumber => {
        const availableQty = lotQuantities[lotNumber];
        if (availableQty > 0) {
            const option = document.createElement('option');
            option.value = lotNumber;
            option.textContent = `${lotNumber} (Available: ${availableQty})`;
            option.setAttribute('data-quantity', availableQty);
            dropdown.appendChild(option);
        }
    });
    
    // Add event listener to update available quantity display
    dropdown.addEventListener('change', function() {
        const selectedOption = this.selectedOptions[0];
        const availableQty = selectedOption ? selectedOption.getAttribute('data-quantity') : 0;
        document.getElementById('availableQuantity').textContent = availableQty;
        
        // Reset quantity input
        const qtyInput = document.getElementById('removeQuantity');
        if (qtyInput) {
            qtyInput.max = availableQty;
            qtyInput.value = '';
        }
    });
}

// Populate brand dropdown for editing
function populateBrandDropdown() {
    const dropdown = document.getElementById('editProductBrand');
    if (!dropdown || !allBrands) return;
    
    dropdown.innerHTML = '<option value="">Select a brand</option>';
    
    allBrands.forEach(brand => {
        const option = document.createElement('option');
        option.value = brand.Id;
        option.textContent = brand.Name;
        dropdown.appendChild(option);
    });
}

// Open add stock modal
function openAddStockModal() {
    const modal = document.getElementById('addStockModal');
    
    // Reset form fields
    document.getElementById('stockQuantity').value = '';
    document.getElementById('stockLotNumber').value = '';
    document.getElementById('stockManufactureDate').value = '';
    document.getElementById('stockExpiryDate').value = '';
    document.getElementById('stockDescription').value = '';
    
    // Set minimum dates
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('stockManufactureDate').max = today;
    document.getElementById('stockExpiryDate').min = today;
    
    modal.showModal();
}

// Open remove stock modal
function openRemoveStockModal() {
    const modal = document.getElementById('removeStockModal');
    
    // Reset form fields
    document.getElementById('removeLotNumber').value = '';
    document.getElementById('removeQuantity').value = '';
    document.getElementById('removeDescription').value = '';
    document.getElementById('availableQuantity').textContent = '0';
    
    modal.showModal();
}

// Add stock
async function addStock() {
    try {
        const formData = {
            ProductId: currentProduct.Id,
            Quantity: parseInt(document.getElementById('stockQuantity').value),
            ExpiryDate: document.getElementById('stockExpiryDate').value + 'T00:00:00Z',
            ManufactureDate: document.getElementById('stockManufactureDate').value + 'T00:00:00Z',
            LotNumber: document.getElementById('stockLotNumber').value,
            Description: document.getElementById('stockDescription').value
        };
        
        // Validate required fields
        if (!formData.Quantity || !formData.LotNumber || !formData.Description || !formData.ExpiryDate || !formData.ManufactureDate) {
            showError('Please fill in all required fields');
            return;
        }
        
        // Validate dates
        const manufactureDate = new Date(formData.ManufactureDate);
        const expiryDate = new Date(formData.ExpiryDate);
        
        if (expiryDate <= manufactureDate) {
            showError('Expiry date must be after manufacture date');
            return;
        }
        
        const response = await fetch(`${API_BASE_URL}/stock/add`, {
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
        
        showSuccess('Stock added successfully');
        document.getElementById('addStockModal').close();
        
        // Reload product details to get updated stock
        await loadProductDetails(currentProduct.Id);
        
    } catch (error) {
        console.error('Error adding stock:', error);
        showError(`Failed to add stock: ${error.message}`);
    }
}

// Remove stock
async function removeStock() {
    try {
        const formData = {
            ProductId: currentProduct.Id,
            LotNumber: document.getElementById('removeLotNumber').value,
            Quantity: parseInt(document.getElementById('removeQuantity').value),
            Description: document.getElementById('removeDescription').value
        };
        
        // Validate required fields
        if (!formData.LotNumber || !formData.Quantity || !formData.Description) {
            showError('Please fill in all required fields');
            return;
        }
        
        // Validate quantity
        const availableQty = parseInt(document.getElementById('availableQuantity').textContent);
        if (formData.Quantity > availableQty) {
            showError(`Cannot remove ${formData.Quantity} items. Only ${availableQty} available.`);
            return;
        }
        
        const response = await fetch(`${API_BASE_URL}/stock/remove`, {
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
        
        showSuccess('Stock removed successfully');
        document.getElementById('removeStockModal').close();
        
        // Reload product details to get updated stock
        await loadProductDetails(currentProduct.Id);
        
    } catch (error) {
        console.error('Error removing stock:', error);
        showError(`Failed to remove stock: ${error.message}`);
    }
}

// Edit product
function editProduct() {
    if (!currentProduct) return;
    
    // Populate edit form
    document.getElementById('editProductName').value = currentProduct.Name || '';
    document.getElementById('editProductDescription').value = currentProduct.Description || '';
    document.getElementById('editProductBrand').value = currentProduct.BrandId || '';
    document.getElementById('editProductType').value = currentProduct.Type || '';
    document.getElementById('editProductCatNo').value = currentProduct.CategoryNumber || '';
    document.getElementById('editProductUnit').value = currentProduct.Unit || '';
    
    // Show modal
    document.getElementById('editProductModal').showModal();
}

// Update product
async function updateProduct() {
    try {
        const formData = {
            Id: currentProduct.Id,
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
        
        // Reload product details
        await loadProductDetails(currentProduct.Id);
        
    } catch (error) {
        console.error('Error updating product:', error);
        showError(`Failed to update product: ${error.message}`);
    }
}

// Delete product
function deleteProduct() {
    if (!currentProduct) return;
    
    document.getElementById('deleteProductName').textContent = currentProduct.Name;
    document.getElementById('deleteConfirmModal').showModal();
}

// Confirm delete product
async function confirmDeleteProduct() {
    try {
        const response = await fetch(`${API_BASE_URL}/inventory/delete`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${readToken()}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ Id: currentProduct.Id })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${await response.text()}`);
        }
        
        showSuccess('Product deleted successfully');
        document.getElementById('deleteConfirmModal').close();
        
        // Redirect back to inventory page
        setTimeout(() => {
            goBack();
        }, 1000);
        
    } catch (error) {
        console.error('Error deleting product:', error);
        showError(`Failed to delete product: ${error.message}`);
        document.getElementById('deleteConfirmModal').close();
    }
}

// Open delete stock confirmation modal
function openDeleteStockModal(stockId, lotNumber, quantity) {
    document.getElementById('deleteStockLot').textContent = lotNumber;
    document.getElementById('deleteStockQuantity').textContent = quantity;
    
    // Store stock ID for deletion
    window.currentDeleteStockId = stockId;
    
    document.getElementById('deleteStockConfirmModal').showModal();
}

// Confirm delete stock record
async function confirmDeleteStockRecord() {
    try {
        const stockId = window.currentDeleteStockId;
        if (!stockId) return;
        
        const response = await fetch(`${API_BASE_URL}/stock/delete`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${readToken()}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ Id: stockId })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${await response.text()}`);
        }
        
        showSuccess('Stock record deleted successfully');
        document.getElementById('deleteStockConfirmModal').close();
        
        // Reload product details to get updated stock
        await loadProductDetails(currentProduct.Id);
        
    } catch (error) {
        console.error('Error deleting stock record:', error);
        showError(`Failed to delete stock record: ${error.message}`);
        document.getElementById('deleteStockConfirmModal').close();
    }
}

// Go back to inventory page
function goBack() {
    window.location.href = 'inventory.html';
}

// Utility Functions

// Get stock badge class based on quantity (daisyUI classes)
function getStockBadgeClass(stockCount) {
    if (stockCount === 0) return 'badge-error';
    if (stockCount < 10) return 'badge-warning';
    if (stockCount < 50) return 'badge-info';
    return 'badge-success';
}

// Get stock type badge class (daisyUI classes)
function getStockTypeBadgeClass(stockType) {
    switch (stockType) {
        case 'Incoming':
            return 'badge-success';
        case 'Outgoing':
            return 'badge-warning';
        default:
            return 'badge-ghost';
    }
}

// Format date for display
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    
    try {
        const date = new Date(dateString);
        return date.toLocaleDateString();
    } catch (error) {
        return 'Invalid Date';
    }
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    if (typeof text !== 'string') return text;
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Truncate text
function truncateText(text, maxLength) {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

// Show loading indicator
function showLoading() {
    console.log('Loading...');
}

// Hide loading indicator
function hideLoading() {
    console.log('Loading complete');
}

// Show error message
function showError(message) {
    console.error('Error:', message);
    alert('Error: ' + message);
}

// Show success message
function showSuccess(message) {
    console.log('Success:', message);
    alert('Success: ' + message);
}

// Export functions for global access
window.openAddStockModal = openAddStockModal;
window.openRemoveStockModal = openRemoveStockModal;
window.addStock = addStock;
window.removeStock = removeStock;
window.editProduct = editProduct;
window.updateProduct = updateProduct;
window.deleteProduct = deleteProduct;
window.confirmDeleteProduct = confirmDeleteProduct;
window.openDeleteStockModal = openDeleteStockModal;
window.confirmDeleteStockRecord = confirmDeleteStockRecord;
window.goBack = goBack;
