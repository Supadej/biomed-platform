/**
 * biomed-index.js
 * Dashboard page with modern daisyUI styling
 */

async function fetchUserSummary() {
    try {
        const xhr = new XMLHttpRequest();
        xhr.open('GET', `${url}/biomedapi/v2/user/Summary`, true);
        xhr.setRequestHeader("Content-Type", "application/json");
        xhr.setRequestHeader("Authorization", "Bearer " + readToken());

        const response = await new Promise((resolve, reject) => {
            xhr.onload = function () {
                if (xhr.status === 200) {
                    resolve(JSON.parse(xhr.responseText));
                } else {
                    reject(new Error(`Error: ${xhr.status} ${xhr.statusText}`));
                }
            };

            xhr.onerror = function () {
                reject(new Error('Request failed.'));
            };

            xhr.send();
        });

        return response;
    } catch (error) {
        console.error(error);
        throw error;
    }
}

// Main entry point
(async () => {
    showLoader();
    try {
        const response = await fetchUserSummary();
        console.log('Response:', response);
        
        var eventDisplayTask = displayEvent(response.myEvent, response.myCoopEvent);
        var targetDisplayTask = displayTarget(response.myTarget);
        var userDisplayTask = displayUser(response.user, response.userProduct, response.userSaleArea);
        
        await Promise.all([eventDisplayTask, targetDisplayTask, userDisplayTask]);
        
        // Update counts
        const eventCount = document.getElementById('eventCount');
        const targetCount = document.getElementById('targetCount');
        if (eventCount) eventCount.textContent = (response.myEvent?.length || 0) + (response.myCoopEvent?.length || 0);
        if (targetCount) targetCount.textContent = response.myTarget?.length || 0;
        
        hideLoader();
    } catch (error) {
        console.error(error);
        hideLoader();
        showAlert('เกิดข้อผิดพลาดในการโหลดข้อมูล', 'error');
    }
})();

async function displayUser(user, products, saleAreas) {
    return new Promise(async (resolve, reject) => {
        try {
            const codenameElements = document.querySelectorAll('.codename');
            const positionElements = document.querySelectorAll('.position');
            const profilePicElements = document.querySelectorAll('.ProfilePic');
            const emailElements = document.querySelectorAll('.email');
            const telElements = document.querySelectorAll('.tel');
            const saleAreasElements = document.querySelectorAll('.SaleAreas');
            const productsElements = document.querySelectorAll('.Products');
            const nameElements = document.querySelectorAll('.name');
            
            var Color = await getColor(user.Id);
            
            nameElements.forEach(el => el.textContent = user.FirstName + " " + user.LastName || 'N/A');
            
            codenameElements.forEach(el => {
                el.innerHTML = `${user.FirstName} <span class="badge badge-sm" style="background-color:${Color.color.code};color:${Color.textColor};">${Color.color.name}</span>`;
            });
            
            positionElements.forEach(el => el.textContent = user.Position || 'N/A');
            profilePicElements.forEach(el => el.src = "assets/profile/" + user.ProfilePic + ".jpg" || 'assets/profile-user.png');
            emailElements.forEach(el => el.textContent = user.Email || 'N/A');
            telElements.forEach(el => el.textContent = user.PhoneNumber || 'N/A');
            
            saleAreasElements.forEach(el => {
                el.innerHTML = saleAreas.map(area => 
                    `<span class="badge badge-info badge-sm gap-1"><i class="fas fa-map-pin text-[10px]"></i>${area}</span>`
                ).join('') || '<span class="badge badge-ghost badge-sm">N/A</span>';
            });
            
            productsElements.forEach(el => {
                el.innerHTML = products.map(product => 
                    `<span class="badge badge-success badge-sm gap-1"><i class="fas fa-cube text-[10px]"></i>${product}</span>`
                ).join('') || '<span class="badge badge-ghost badge-sm">N/A</span>';
            });

            console.log("User displayed successfully.");
            resolve("User displayed successfully.");
        } catch (error) {
            console.error("Failed to display user.", error);
            reject(new Error("Failed to display user."));
        }
    });
}

async function displayTarget(target) {
    return new Promise(async (resolve, reject) => {
        try {
            // Process target data
            target.forEach(t => {
                const now = new Date();
                const endDate = new Date(t.EndDate);
                t.RemainDays = Math.ceil((endDate - now) / (1000 * 60 * 60 * 24));
                t.Acheived = t.Leads.reduce((sum, lead) => sum + lead.AchivedRevenue, 0);
                t.Remaining = t.TargetValue - t.Acheived;
                t.AcheivedPercent = t.TargetValue > 0 ? Math.round((t.Acheived / t.TargetValue) * 100) : 0;
            });

            const targetContainer = document.getElementById("targetContainer");
            if (!targetContainer) {
                reject(new Error("Target container not found"));
                return;
            }

            targetContainer.innerHTML = '';

            for (const t of target) {
                const product = await promiseProductById(t.ProductID);
                const saleArea = await promiseSaleAreaById(t.SaleAreaID);
                
                // Status badge
                let statusBadge = '';
                if (t.RemainDays <= 0) {
                    statusBadge = `<div class="badge badge-error gap-1 text-white"><i class="fas fa-exclamation-circle"></i> หมดเวลา</div>`;
                } else if (t.RemainDays <= 7) {
                    statusBadge = `<div class="badge badge-warning gap-1"><i class="fas fa-clock"></i> ${t.RemainDays} วัน</div>`;
                } else {
                    statusBadge = `<div class="badge badge-info gap-1 text-white"><i class="fas fa-hourglass-half"></i> ${t.RemainDays} วัน</div>`;
                }
                
                // Progress color based on percentage
                let progressColor = '#8b5cf6'; // Default purple
                if (t.AcheivedPercent >= 100) {
                    progressColor = '#10b981'; // Green
                } else if (t.AcheivedPercent >= 75) {
                    progressColor = '#3b82f6'; // Blue
                } else if (t.AcheivedPercent >= 50) {
                    progressColor = '#f59e0b'; // Yellow
                } else {
                    progressColor = '#ef4444'; // Red
                }
                
                const targetElement = document.createElement('div');
                targetElement.className = "target-card card rounded-2xl shadow-lg flex-shrink-0 overflow-hidden";
                
                targetElement.innerHTML = `
                    <div class="card-body p-4">
                        <!-- Header -->
                        <div class="flex items-start justify-between gap-2 mb-3">
                            <h3 class="font-bold text-base line-clamp-2">${t.Name}</h3>
                            ${statusBadge}
                        </div>
                        
                        <!-- Chart Container -->
                        <div class="relative flex justify-center my-2">
                            <canvas id="target-${t.Id}" class="!w-[150px] !h-[150px]"></canvas>
                        </div>
                        
                        <!-- Info Grid -->
                        <div class="space-y-2 mt-3">
                            <div class="info-row">
                                <span class="text-xs text-base-content/60 flex items-center gap-1">
                                    <i class="fas fa-box text-primary text-[10px]"></i> Product
                                </span>
                                <span class="text-xs font-medium truncate max-w-[100px]">${product?.Name || 'N/A'}</span>
                            </div>
                            <div class="info-row">
                                <span class="text-xs text-base-content/60 flex items-center gap-1">
                                    <i class="fas fa-map-marker-alt text-secondary text-[10px]"></i> Sale Area
                                </span>
                                <span class="text-xs font-medium truncate max-w-[100px]">${saleArea?.Name || 'N/A'}</span>
                            </div>
                            <div class="info-row">
                                <span class="text-xs text-base-content/60 flex items-center gap-1">
                                    <i class="fas fa-bullseye text-info text-[10px]"></i> Target
                                </span>
                                <span class="text-xs font-bold text-primary">${AutoComma(t.TargetValue)} ฿</span>
                            </div>
                            <div class="info-row">
                                <span class="text-xs text-base-content/60 flex items-center gap-1">
                                    <i class="fas fa-check-circle text-success text-[10px]"></i> Achieved
                                </span>
                                <span class="text-xs font-bold text-success">${AutoComma(t.Acheived)} ฿</span>
                            </div>
                            <div class="info-row">
                                <span class="text-xs text-base-content/60 flex items-center gap-1">
                                    <i class="fas fa-hourglass text-warning text-[10px]"></i> Remaining
                                </span>
                                <span class="text-xs font-bold text-warning">${AutoComma(t.Remaining < 0 ? 0 : t.Remaining)} ฿</span>
                            </div>
                        </div>
                    </div>
                `;

                targetContainer.appendChild(targetElement);
                
                // Create chart
                const ctx = document.getElementById('target-' + t.Id).getContext('2d');
                const centerText = {
                    id: 'centerText',
                    afterDatasetsDraw(chart) {
                        const { ctx, chartArea: { width, height } } = chart;
                        ctx.save();
                        ctx.font = 'bold 24px "Noto Sans Thai", sans-serif';
                        ctx.fillStyle = progressColor;
                        ctx.textAlign = 'center';
                        ctx.textBaseline = 'middle';
                        ctx.fillText(t.AcheivedPercent + " %", width / 2, height / 1.8);
                        ctx.restore();
                    }
                };

                new Chart(ctx, {
                    type: 'doughnut',
                    data: {
                        labels: ['Achieved', 'Remaining'],
                        datasets: [{
                            data: [t.Acheived, t.Acheived > t.TargetValue ? 0 : t.TargetValue - t.Acheived],
                            backgroundColor: [progressColor, progressColor + '20'],
                            borderWidth: 0,
                            cutout: '78%',
                            circumference: 270,
                            rotation: 225,
                            borderRadius: 8,
                        }]
                    },
                    options: {
                        responsive: false,
                        maintainAspectRatio: true,
                        plugins: {
                            legend: { display: false },
                            tooltip: {
                                callbacks: {
                                    label: function(tooltipItem) {
                                        return AutoComma(tooltipItem.raw) + ' THB';
                                    }
                                }
                            }
                        }
                    },
                    plugins: [centerText]
                });
            }
            
            // Show empty state if no targets
            if (target.length === 0) {
                targetContainer.innerHTML = `
                    <div class="w-full flex flex-col items-center justify-center py-8 text-base-content/40">
                        <i class="fas fa-bullseye text-4xl mb-3"></i>
                        <p class="text-sm">ไม่มี Target</p>
                    </div>
                `;
            }
            
            console.log('Processed Targets:', target);
            resolve("Target displayed successfully.");
        } catch (error) {
            console.error("Failed to display target.", error);
            reject(new Error("Failed to display target."));
        }
    });
}

async function displayEvent(event, coopEvent) {
    return new Promise(async (resolve, reject) => {
        try {
            event.forEach(e => e.selfEvent = true);
            coopEvent.forEach(e => e.selfEvent = false);
            
            const combinedEvents = [...event, ...coopEvent];
            combinedEvents.sort((a, b) => new Date(a.StartDate) - new Date(b.StartDate));
            
            const filteredEvents = [];
            const now = new Date();
            
            combinedEvents.forEach(e => {
                const startDate = new Date(e.StartDate);
                const endDate = new Date(e.EndDate);

                if (endDate < now && (e.Report === null || e.Report === '')) {
                    e.reminder = "Need Report";
                    e.badgeClass = "badge-error";
                    e.icon = "fa-exclamation-circle";
                    e.valid = true;
                } else if (now >= startDate && now <= endDate) {
                    e.reminder = "กำลังดำเนินการ";
                    e.badgeClass = "badge-info";
                    e.icon = "fa-play-circle";
                    e.valid = true;
                } else if (startDate.toDateString() === now.toDateString()) {
                    e.reminder = "วันนี้";
                    e.badgeClass = "badge-primary";
                    e.icon = "fa-star";
                    e.valid = true;
                } else {
                    const tomorrow = new Date();
                    tomorrow.setDate(now.getDate() + 1);
                    
                    if (startDate.toDateString() === tomorrow.toDateString()) {
                        e.reminder = "พรุ่งนี้";
                        e.badgeClass = "badge-success";
                        e.icon = "fa-calendar-check";
                        e.valid = true;
                    } else {
                        const daysDifference = Math.ceil((startDate - now) / (1000 * 60 * 60 * 24));
                        if (daysDifference < 0) {
                            e.reminder = "เสร็จสิ้น";
                            e.badgeClass = "badge-ghost";
                            e.icon = "fa-check";
                            e.valid = false;
                        } else {
                            e.reminder = `อีก ${daysDifference} วัน`;
                            e.badgeClass = "badge-secondary";
                            e.icon = "fa-calendar";
                            e.valid = true;
                        }
                    }
                }
                
                if (e.valid) filteredEvents.push(e);
            });

            const eventContainer = document.getElementById("eventContainer");
            if (!eventContainer) {
                reject(new Error("Event container not found"));
                return;
            }
            
            eventContainer.innerHTML = '';

            filteredEvents.forEach(e => {
                const startDate = new Date(e.StartDate);
                const formattedDate = startDate.toLocaleDateString('th-TH', { 
                    day: 'numeric', 
                    month: 'short',
                    year: '2-digit'
                });
                
                const eventElement = document.createElement('div');
                eventElement.className = "event-card card rounded-2xl shadow-lg flex-shrink-0 overflow-hidden cursor-pointer";
                eventElement.onclick = () => window.location.href = `./event.html?id=${e.Id}`;
                
                eventElement.innerHTML = `
                    <div class="card-body p-4 h-full flex flex-col">
                        <!-- Top: Badge & Icon -->
                        <div class="flex items-center justify-between mb-2">
                            <div class="flex items-center gap-2">
                                <div class="w-8 h-8 rounded-lg ${e.selfEvent ? 'bg-primary/10 text-primary' : 'bg-secondary/10 text-secondary'} flex items-center justify-center">
                                    <i class="fas ${e.selfEvent ? 'fa-user' : 'fa-users'} text-sm"></i>
                                </div>
                                <span class="badge ${e.badgeClass} badge-sm gap-1">
                                    <i class="fas ${e.icon} text-[10px]"></i>
                                    ${e.reminder}
                                </span>
                            </div>
                            <a href="./event.html?id=${e.Id}" class="btn btn-ghost btn-circle btn-xs" onclick="event.stopPropagation()">
                                <i class="fas fa-external-link-alt text-xs"></i>
                            </a>
                        </div>
                        
                        <!-- Title -->
                        <h3 class="font-bold text-sm line-clamp-2 mb-2 flex-shrink-0">${e.Title}</h3>
                        
                        <!-- Description -->
                        <p class="text-xs text-base-content/60 line-clamp-3 flex-grow">${e.Plan?.trim() || 'ไม่มีรายละเอียด'}</p>
                        
                        <!-- Footer -->
                        <div class="flex items-center justify-between mt-3 pt-3 border-t border-base-200">
                            <span class="text-[10px] text-base-content/50 flex items-center gap-1">
                                <i class="far fa-calendar"></i>
                                ${formattedDate}
                            </span>
                            <span class="text-[10px] text-primary font-medium">ดูรายละเอียด →</span>
                        </div>
                    </div>
                `;

                eventContainer.appendChild(eventElement);
            });

            // Show empty state if no events
            if (filteredEvents.length === 0) {
                eventContainer.innerHTML = `
                    <div class="w-full flex flex-col items-center justify-center py-8 text-base-content/40">
                        <i class="fas fa-calendar-times text-4xl mb-3"></i>
                        <p class="text-sm">ไม่มี Event ที่กำลังจะมาถึง</p>
                    </div>
                `;
            }

            console.log("Event displayed successfully.");
            resolve("Event displayed successfully.");
        } catch (error) {
            console.error("Failed to display event.", error);
            reject(new Error("Failed to display event."));
        }
    });
}

// =====================================================
// Profile Picture Upload Functions
// =====================================================

function resizeImage(image, maxWidth, maxHeight) {
    var canvas = document.createElement('canvas');
    var ctx = canvas.getContext('2d');

    var width = image.width;
    var height = image.height;

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
        var image = new Image();
        var canvas = document.createElement('canvas');
        var ctx = canvas.getContext('2d');

        canvas.width = size;
        canvas.height = size;

        image.onload = function() {
            var width = image.width;
            var height = image.height;

            var x = (width - size) / 2;
            var y = (height - size) / 2;

            ctx.drawImage(image, x, y, size, size, 0, 0, size, size);
            resolve(canvas.toDataURL('image/jpeg'));
        };

        image.onerror = reject;
        image.src = imageDataUrl;
    });
}

function dataURItoBlob(dataURI) {
    var byteString = atob(dataURI.split(',')[1]);
    var mimeString = dataURI.split(',')[0].split(':')[1].split(';')[0];
    var ab = new ArrayBuffer(byteString.length);
    var ia = new Uint8Array(ab);
    for (var i = 0; i < byteString.length; i++) {
        ia[i] = byteString.charCodeAt(i);
    }
    return new Blob([ab], { type: mimeString });
}

function processImage(file) {
    var reader = new FileReader();
    reader.onload = function(event) {
        var image = new Image();
        image.onload = async function() {
            var resizedImageDataUrl = resizeImage(image, 300, 300);
            try {
                var croppedImageDataUrl = await cropImage(resizedImageDataUrl, 300);
                var formData = new FormData();
                formData.append('file', dataURItoBlob(croppedImageDataUrl));
                
                var xhr = new XMLHttpRequest();
                xhr.open('POST', url + '/biomedapi/upload/profile', true);
                xhr.setRequestHeader('Authorization', 'Bearer ' + readToken());
                xhr.onreadystatechange = function() {
                    if (xhr.readyState === 4) {
                        if (xhr.status === 200) {
                            xalert('อัปโหลดรูปโปรไฟล์เรียบร้อย', 0, 5000);
                            setTimeout(function() {
                                location.reload();
                            }, 2000);
                        } else {
                            xalert('เกิดข้อผิดพลาด: ' + xhr.status + ' - ' + xhr.responseText, 1, -1);
                        }
                    }
                };
                xhr.send(formData);
            } catch (error) {
                console.error("Error cropping image:", error);
                xalert('เกิดข้อผิดพลาดในการประมวลผลรูปภาพ', 1);
            }
        };
        image.src = event.target.result;
    };
    reader.readAsDataURL(file);
}

// Function to be called from handleProfilePicUpload in index.html
function uploadUserProfilePic(file) {
    processImage(file);
}

// =====================================================
// Update User / Change Password Functions
// =====================================================

function updateUserPassword(newPassword) {
    myUserRequest(function(err, user) {
        if (err) {
            xalert("ไม่สามารถดึงข้อมูลผู้ใช้ได้: " + err, 1, null);
            return;
        }
        
        var updateUserRequest = {
            Id: user.Id,
            Password: newPassword,
            ProfilePic: user.ProfilePic,
            FirstName: user.FirstName,
            LastName: user.LastName,
            MiddleName: user.MiddleName,
            Email: user.Email,
            PhoneNumber: user.PhoneNumber,
            SubEmail: user.SubEmail,
            SubPhoneNumber: user.SubPhoneNumber,
            Address: user.Address,
            LineID: user.LineID
        };
        
        var xhr = new XMLHttpRequest();
        xhr.open("POST", url + "/biomedapi/users/update", true);
        xhr.setRequestHeader("Content-Type", "application/json");
        xhr.setRequestHeader("Authorization", "Bearer " + readToken());
        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4) {
                if (xhr.status === 200) {
                    xalert("เปลี่ยนรหัสผ่านเรียบร้อย", 0, 5000);
                } else {
                    xalert("เกิดข้อผิดพลาด: " + xhr.status + " - " + xhr.responseText, 1, -1);
                }
            }
        };
        xhr.send(JSON.stringify(updateUserRequest));
    });
}
