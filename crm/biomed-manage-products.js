function createProductRequest() {
    return new Promise((resolve, reject) => {

        const productName = document.getElementById('productName').value;
        const productDescription = document.getElementById('productDescription').value;
        const product = {
            Name: productName,
            Description: productDescription
        };
        const xhr = new XMLHttpRequest();
        const token = readToken(); // Assuming readToken() returns the token value
        xhr.open('POST', url+'/biomedapi/products/create');
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.setRequestHeader('Authorization', `Bearer ${token}`); // Add the token to the request headers
        xhr.onload = function() {
            if (xhr.status === 200) {
                clearCache();
                location.reload();
                resolve(xhr.responseText);
            } else {
                xalert('Failed to add product', 1, null);
                reject(new Error('Failed to add product'));
            }
        };
        xhr.onerror = function() {
            xalert('Failed to add product', 1, null);
            reject(new Error('Failed to add product'));

        };
        xhr.send(JSON.stringify(product));
    });
}

function createSaleAreaRequest() {
    return new Promise((resolve, reject) => {

        const saleAreaName = document.getElementById('saleAreaName').value;
        const saleAreaDescription = document.getElementById('saleAreaDescription').value;
        const saleArea = {
            Name: saleAreaName,
            Description: saleAreaDescription
        };
        const xhr = new XMLHttpRequest();
        const token = readToken(); // Assuming readToken() returns the token value
        xhr.open('POST', url+'/biomedapi/saleareas/create');
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.setRequestHeader('Authorization', `Bearer ${token}`); // Add the token to the request headers
        xhr.onload = function() {
            if (xhr.status === 200) {
                clearCache();
                location.reload();
                resolve(xhr.responseText);
            } else {
                xalert('Failed to add sale area', 1, null);
                reject(new Error('Failed to add sale area'));
            }
        };
        xhr.onerror = function() {
            xalert('Failed to add sale area', 1, null);
            reject(new Error('Failed to add sale area'));

        };
        xhr.send(JSON.stringify(saleArea));
    });
}

function refreshProduct(){
    clearCache();
    location.reload();
}

function refreshSaleArea(){
    clearCache();
    location.reload();
}