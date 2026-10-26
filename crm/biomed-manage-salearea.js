/**
 * biomed-manage-salearea.js
 * Sale Area Management with daisyUI styling
 */

const urlParams = new URLSearchParams(window.location.search);
const id = urlParams.get('id');

window.onload = function() {
    if (!id) {
        xalert("No id please check your url", 1, null);
        return;
    }
    
    // Update area ID badge
    document.getElementById('areaIdBadge').textContent = 'ID: ' + id;
    
    // Load sale area data
    getSaleAreaById(id)
        .then(function(saleArea) {
            document.getElementById('areaName').value = saleArea.Name || '';
            document.getElementById('areaDescription').value = saleArea.Description || '';
            document.getElementById('breadcrumbAreaName').textContent = saleArea.Name || 'Unnamed Area';
        })
        .catch(function(error) {
            console.error('Failed to retrieve sale area:', error);
            xalert("Failed to retrieve sale area", 1, null);
        });
}

function saveSaleArea() {
    const areaName = document.getElementById('areaName').value;
    const areaDescription = document.getElementById('areaDescription').value;
    
    if (!areaName.trim()) {
        xalert("Area name is required", 1, null);
        return;
    }
    
    const data = {
        Name: areaName,
        id: id,
        Description: areaDescription
    };

    updateSaleArea(data, function(error, response) {
        if (error) {
            console.error('Failed to update area:', error);
            xalert("Failed to update area", 1, null);
            return;
        }
        console.log('Area updated successfully:', response);
        
        // Clear sale area cache to force refresh
        sessionStorage.removeItem("saleArea");
        sessionStorage.removeItem("saleArea:" + id);
        
        xalert("Sale area updated successfully", 0, null);
        document.getElementById('breadcrumbAreaName').textContent = areaName;
    });
}

function updateSaleArea(data, callback) {
    const xhr = new XMLHttpRequest();
    xhr.open('POST', url + '/biomedapi/saleareas/update');
    xhr.setRequestHeader('Authorization', `Bearer ${readToken()}`);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.onload = function() {
        if (xhr.status === 200) {
            callback(null, xhr.responseText);
        } else {
            callback('Failed to update area', null);
        }
    };
    xhr.onerror = function() {
        callback('Failed to send request', null);
    };
    xhr.send(JSON.stringify(data));
}

function deleteSaleArea() {
    if (!confirm("Are you sure you want to delete this sale area?\n\nThis action cannot be undone.")) {
        return;
    }
    
    const xhr = new XMLHttpRequest();
    xhr.open('POST', url + '/biomedapi/saleareas/delete');
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.setRequestHeader('Authorization', `Bearer ${readToken()}`);
    xhr.onload = function() {
        if (xhr.status === 200) {
            xalert("Sale area deleted successfully", 0, null);
            setTimeout(() => {
                window.location.href = 'management.html';
            }, 1500);
        } else {
            xalert("Failed to delete sale area", 1, null);
        }
    };
    xhr.onerror = function() {
        xalert("Failed to send request", 1, null);
    };
    xhr.send(JSON.stringify({ id: id }));
}
