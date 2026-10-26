const urlParams = new URLSearchParams(window.location.search);
const hdid = urlParams.get("leadid");

document.getElementById("d3Button").addEventListener("click", function () {
  window.location.href = `./d3.html?type=${"tickets"}&id=${hdid}`;
});

const select = document.getElementById("usersSelecter");
const groupSelect = document.getElementById("groupSelecter");
const contactSelect = document.getElementById("contactsSelecter");
const mainContactSelect = document.getElementById("mainContactsSelecter");
const mainContactsList = document.getElementById("mainContactsList");
const modalContactsList = document.getElementById("modalContactsList");

const jobType = [
  { value: 0, jobType: "Sale_Support" },
  { value: 1, jobType: "Maintenance" },
  { value: 2, jobType: "Installation" },
  { value: 3, jobType: "Scheduled_Maintenance" },
  { value: 4, jobType: "Relocation" },
  { value: 5, jobType: "Repair" },
  { value: 6, jobType: "Training" },
  { value: 7, jobType: "Update" },
  { value: 8, jobType: "Calibration" },
  { value: 9, jobType: "Upgrade" },
  { value: 10, jobType: "Uninstallation" },
  { value: 11, jobType: "Preventive_Maintenance" },
  { value: 12, jobType: "Other" }
];

const instumentalStatus = [
  { value: 0, status: "In_Warranty" },
  { value: 1, status: "Reagent_Rental" },
  { value: 2, status: "Out_of_Warranty" },
  { value: 3, status: "Company_Property" },
  { value: 4, status: "Service_Contract" },
  { value: 5, status: "Customer_Property" },
  { value: 6, status: "Other" }
];

var mainuserid;
let currentHelpDeskItems = [];
let inventoryProducts = [];
let currentSearchResults = [];
let currentEditingItemId = null;
let globalGroups = {};
let pipelineList = [];

// Store assigned user ID to set after options are loaded
var pendingAssignedUserId = null;
var originalAssignedUserId = null; // Keep track of original to mark as "external"

function readPermission(assignedUserId = null) {
  pendingAssignedUserId = assignedUserId;
  originalAssignedUserId = assignedUserId;
  
  myPermission(function (err, Permissions) {
    if (err) {
      xalert("Failed to fetch permissions:" + err, 1, null);
      return;
    }
    
    if(Permissions.MainPermissions.find(permission => permission.Type === "helpdesk_manage")) {
      getUsers((error, users) => {
        if (error) {
          console.error("Failed to fetch users:", error);
          return;
        }
        const assignedUserSelect = document.getElementById("assignedUser");
        // Clear existing options except the first empty one
        assignedUserSelect.innerHTML = '<option value="">Select user...</option>';
        
        let assignedUserInList = false;
        let subordinateUsers = []; // Users we can assign to
        
        users.forEach((user) => {
          if(Permissions.IndividualPermissions.find(permission => permission.PermissionKey === user.Id.toString() && permission.Type === "helpdesk_manage_individual")) {
            const option = document.createElement("option");
            option.value = user.Id;
            option.textContent = `${user.FirstName} ${user.LastName}`;
            assignedUserSelect.appendChild(option);
            subordinateUsers.push(user.Id);
            
            if (pendingAssignedUserId && user.Id == pendingAssignedUserId) {
              assignedUserInList = true;
            }
          }
        });
        
        // If assigned user is not in our subordinate list, add them as "external" option
        if (pendingAssignedUserId && !assignedUserInList) {
          getUserById((err, user) => {
            if (err) {
              console.error("Failed to fetch assigned user:", err);
              return;
            }
            const option = document.createElement("option");
            option.value = user.Id;
            option.textContent = `${user.FirstName} ${user.LastName} (External)`;
            option.setAttribute('data-external', 'true');
            assignedUserSelect.appendChild(option);
            assignedUserSelect.value = pendingAssignedUserId;
          }, pendingAssignedUserId);
        } else if (pendingAssignedUserId) {
          // User is in list, just set value
          assignedUserSelect.value = pendingAssignedUserId;
        }
        
        // When user changes selection, remove external option if they select a subordinate
        assignedUserSelect.addEventListener('change', function() {
          const selectedValue = parseInt(this.value);
          const externalOption = this.querySelector('option[data-external="true"]');
          
          // If selected a subordinate (not the external user), remove external option
          if (externalOption && subordinateUsers.includes(selectedValue)) {
            externalOption.remove();
          }
        });
      });
    }
  });
}

function disableInputs() {
  const inputs = document.querySelectorAll('input');
  const textareas = document.querySelectorAll('textarea');
  const selects = document.querySelectorAll('select');

  inputs.forEach(input => input.setAttribute('readonly', true));
  textareas.forEach(textarea => textarea.setAttribute('readonly', true));
  selects.forEach(select => select.setAttribute('disabled', true));
}

function shareLead() {
  window.location.href = `ticket-report.html?id=${parseIntToRandomString(hdid)}`;
}

window.onload = function () {
  if (hdid === null) {
    xalert("Error: No hdid parameter found in the URL", 1, null);
    return;
  }

  // Initialize priority slider using RangeSlider
  window.prioritySlider = new RangeSlider('priorityContainer', {
    min: 0,
    max: 5,
    value: 0,
    step: 1,
    showTooltip: true,
    showLabels: true,
    showScale: true,
    scaleSteps: 5,
    colorClass: 'range-warning',
    text: {
      min: 'Priority'
    },
    formatValue: function(val) {
      return priorityFormatting(val);
    }
  });

  const token = readToken();
  const xhr = new XMLHttpRequest();

  xhr.open("GET", url + `/biomedapi/v2/helpdesk/ticket/${hdid}`, true);
  xhr.setRequestHeader("Authorization", `Bearer ${token}`);

  xhr.onload = function () {
    if (xhr.status === 200) {
      const response = JSON.parse(xhr.responseText);
      console.log(response);
      
      // Call readPermission with AssignedToUserId so it can be set properly
      readPermission(response.AssignedToUserId);

      // Load Products
      getProducts((err, products) => {
        if (err) {
          console.error("Failed to fetch products:", err);
          return;
        }
        var productSelect = document.getElementById("product");
        products.forEach((product) => {
          const option = document.createElement("option");
          option.value = product.Id;
          option.textContent = product.Name;
          productSelect.appendChild(option);
        });
        
        if (response.ProductId !== undefined && response.ProductId !== null) {
          document.getElementById("product").value = response.ProductId;
        }
      });

      // Load Sale Areas
      getSaleAreas((err, saleAreas) => {
        if (err) {
          console.error("Failed to fetch sale areas:", err);
          return;
        }
        var saleAreaSelect = document.getElementById("saleArea");
        saleAreas.forEach((saleArea) => {
          const option = document.createElement("option");
          option.value = saleArea.Id;
          option.textContent = saleArea.Name;
          saleAreaSelect.appendChild(option);
        });
        if (response.SaleAreaId !== undefined && response.SaleAreaId !== null) {
          document.getElementById("saleArea").value = response.SaleAreaId;
        }
      });

      // Permission Check - Handle cases where user doesn't have helpdesk_manage permission
      // Note: readPermission() already handles the Assigned User dropdown for users WITH permission
      myPermission(function (err, Permissions) {
        if (err) {
          xalert("Failed to fetch permissions:" + err, 1, null);
          return;
        }
        myUserRequest(function (error, currentUser) {
          if (error) {
            xalert("Failed to fetch user:" + error, 1, null);
            return;
          }
          
          // If user has helpdesk_manage permission, readPermission() handles everything
          if(Permissions.MainPermissions.find(permission => permission.Type === "helpdesk_manage")) {
            console.log("User has helpdesk_manage permission - Assigned User handled by readPermission()");
            return; // readPermission() already handles this case
          }
          
          // User is the assigned responsible (but doesn't have manage permission)
          if(response.AssignedToUserId == currentUser.Id) {
            if (window.prioritySlider) window.prioritySlider.disable();
            let assignedUserSelect = document.getElementById("assignedUser");
            assignedUserSelect.innerHTML = "";
            const option = document.createElement("option");
            option.value = currentUser.Id;
            option.textContent = `${currentUser.FirstName} ${currentUser.LastName}`;
            assignedUserSelect.appendChild(option);
            assignedUserSelect.disabled = true;
          } else {
            // User has no permission and is not assigned - readonly mode
            disableInputs();
            if (window.prioritySlider) window.prioritySlider.disable();
            if(response.AssignedToUserId !== null && response.AssignedToUserId !== undefined) {
              getUserById((err, assignedUser) => {
                if (err) {
                  console.error("Failed to fetch user:", err);
                  return;
                }
                let assignedUserSelect = document.getElementById("assignedUser");
                assignedUserSelect.innerHTML = "";
                const option = document.createElement("option");
                option.value = assignedUser.Id;
                option.textContent = `${assignedUser.FirstName} ${assignedUser.LastName}`;
                assignedUserSelect.appendChild(option);
                assignedUserSelect.disabled = true;
              }, response.AssignedToUserId);
            } else {
              let assignedUserSelect = document.getElementById("assignedUser");
              assignedUserSelect.innerHTML = "";
              const option = document.createElement("option");
              option.value = -1;
              option.textContent = `Unassigned`;
              assignedUserSelect.appendChild(option);
              assignedUserSelect.disabled = true;
            }
            console.log("Disabled inputs - user has no permission");
          }
        });
      });

      // Set form values
      if (response.Title) document.getElementById("leadName").value = response.Title;
      if (response.Problem) document.getElementById("problem").value = response.Problem;
      if (response.CreatedDate) document.getElementById("creation").value = timeFuck(response.CreatedDate);
      if (response.Priority !== undefined && window.prioritySlider) window.prioritySlider.setValues(response.Priority);
      if (response.Solution) document.getElementById("solution").value = response.Solution;
      if (response.Instumental) document.getElementById("instumental").value = response.Instumental;
      if (response.Model) document.getElementById("model").value = response.Model;
      if (response.SerialNumber) document.getElementById("serialNumber").value = response.SerialNumber;
      if (response.JobNumber) document.getElementById("JobNumber").value = response.JobNumber;
      
      // Set Ticket Creator
      if (response.CreatedByUserId) {
        document.getElementById("ticketCreatorId").value = response.CreatedByUserId;
        getUserById((err, creator) => {
          if (err) {
            document.getElementById("ticketCreator").value = `User ID: ${response.CreatedByUserId}`;
            return;
          }
          document.getElementById("ticketCreator").value = `${creator.FirstName} ${creator.LastName}`;
        }, response.CreatedByUserId);
      }
      
      if (response.InstumentalStatus !== undefined && response.InstumentalStatus !== null) {
        const instrumentalStatusValue = instumentalStatus.find(status => status.status === response.InstumentalStatus)?.value;
        document.getElementById("instumentalStatus").value = instrumentalStatusValue !== undefined ? instrumentalStatusValue : 0;
      }
      if (response.JobType !== undefined && response.JobType !== null) {
        const jobTypeValue = jobType.find(job => job.jobType === response.JobType)?.value;
        document.getElementById("jobType").value = jobTypeValue !== undefined ? jobTypeValue : 0;
      }
      if (response.ResponseOnTime !== undefined && response.ResponseOnTime !== null) {
        document.getElementById("respondedWithinTimeline").checked = response.ResponseOnTime;
      }

      // Load Pipeline Steps
      GetHelpdeskPipeline((err, pipelines) => {
        if (err) {
          console.error("Failed to fetch pipelines:", err);
          return;
        }
        pipelineList = pipelines;
        const pipelineSelection = document.getElementById("pipelineSelection");
        pipelineSelection.innerHTML = '';

        pipelines.forEach((pipeline, idx) => {
          const step = document.createElement("li");
          step.className = "step cursor-pointer";
          step.setAttribute("data-pipeline-id", pipeline.Id);
          step.setAttribute("data-content", idx + 1);
          step.textContent = pipeline.Name;
          step.onclick = function() { selectPipelineStep(pipeline.Id); };
          pipelineSelection.appendChild(step);
        });

        // Set current pipeline
        if (response.PipelineId) {
          selectPipelineStep(response.PipelineId);
        }
      }, false);

      // Load Users with MultiSelect
      getUsers((error, users) => {
        if (error) {
          console.error("Failed to fetch users:", error);
          return;
        }

        // Build options for MultiSelect
        const usersOptions = users
          .filter(user => user.Id !== response.CreatedByUserId)
          .map(user => ({
            value: user.Id.toString(),
            label: `${user.FirstName} ${user.LastName}`,
            subtext: user.Position || ''
          }));

        // Also populate hidden select for backward compatibility
        users.forEach(user => {
          if (user.Id !== response.CreatedByUserId) {
            const option = document.createElement("option");
            option.value = user.Id;
            option.textContent = `${user.FirstName} ${user.LastName}`;
            select.appendChild(option);
          }
        });

        mainuserid = response.CreatedByUserId;

        // Load Groups
        getGroups((err, groups) => {
          if (err) {
            console.error("Failed to fetch groups:", err);
            return;
          }

          const groupsOptions = groups.map(group => ({
            value: group.Id.toString(),
            label: group.GroupName
          }));

          // Populate hidden group select
          groups.forEach(group => {
            const option = document.createElement("option");
            option.value = group.Id;
            option.textContent = group.GroupName;
            groupSelect.appendChild(option);
          });

          // Load group members for each group
          let groupMembersMap = {};
          let loadedGroups = 0;
          
          groups.forEach(group => {
            getGroupMembers(group.Id, (err, data) => {
              loadedGroups++;
              if (!err && data && data.GroupUsers) {
                groupMembersMap[group.Id] = data.GroupUsers.map(gu => gu.UserId);
              }
              
              if (loadedGroups === groups.length) {
                globalGroups = groupMembersMap;
                setGroupsData(groupMembersMap);
                initUsersMultiSelects(usersOptions, groupsOptions);
                
                // Set selected users
                const userIds = response.UserHelpdesks.map(leadUser => leadUser.UserId.toString());
                setUsersValues(userIds);
              }
            });
          });
        }, false);
      }, false);

      // Load Contacts with MultiSelect
      getContacts((err, contacts) => {
        if (err) {
          console.error("Failed to fetch contacts:", err);
          xalert("Failed to fetch contacts:" + err, 1, null);
          return;
        }

        const contactOptions = contacts.map(contact => ({
          value: contact.Id.toString(),
          label: contact.Name,
          subtext: contact.Position || ''
        }));

        // Populate hidden selects for backward compatibility
        contacts.forEach(contact => {
          const option = document.createElement("option");
          option.value = contact.Id;
          option.textContent = contact.Name;
          contactSelect.appendChild(option);

          const mainOption = document.createElement("option");
          mainOption.value = contact.Id;
          mainOption.textContent = contact.Name;
          mainContactSelect.appendChild(mainOption);
        });

        // Initialize MultiSelects
        initContactMultiSelects(contactOptions);

        // Set selected contacts
        if (response.ContactId) {
          setMainContactValue(response.ContactId.toString());
        }
        
        const contactIds = response.ContactHelpdesks
          .map(contact => contact.ContactId.toString())
          .filter(id => id !== response.ContactId?.toString());
        
        setAdditionalContactValues(contactIds);
      }, false);

      // Load HelpDeskItems
      if (response.HelpDeskItems !== undefined && response.HelpDeskItems !== null) {
        currentHelpDeskItems = response.HelpDeskItems;
        displayHelpDeskItems(currentHelpDeskItems);
      }

      // Load inventory products
      loadInventoryProducts();
      
      cachingObject();
      
      // Load logs
      setTimeout(() => {
        autoload();
      }, 500);
    } else {
      xalert("Error:" + xhr.status, 1, null);
      console.error("Error:", xhr.status);
    }
  };

  xhr.send();
};

async function updateLead() {
  let changedComponent = await compareChange();
  let readableChanges = changedComponent.map(change => {
    let oldValue = Array.isArray(change.oldValue) ? change.oldValue.join(", ") : (typeof(change.oldValue) === 'boolean' ? change.oldValue : change.oldValue || "N/A");
    let newValue = Array.isArray(change.newValue) ? change.newValue.join(", ") : (typeof(change.newValue) === 'boolean' ? change.newValue : change.newValue || "N/A");
    return `${change.field}: ${oldValue} -> ${newValue}`;
  }).join("\n");

  console.log(readableChanges);
  createLog(readableChanges, JSON.stringify(changedComponent), null, null, null, parseInt(hdid), null, 4, function(err, log) {
    if (err) {
      console.error(err);
      return;
    }
    console.log('Log created successfully:', log);
    updateLeadRequest();
  });
}

function updateLeadRequest() {
  var xhr = new XMLHttpRequest();
  
  // Check if pipeline is selected
  const selectedPipeline = getSelectedPipelineId();
  if (!selectedPipeline) {
    xalert("Error: No pipeline selected", 2, 5000);
    return;
  }

  xhr.open("POST", url + "/biomedapi/v2/helpdesk/ticket/update", true);
  xhr.setRequestHeader("Content-Type", "application/json");
  xhr.setRequestHeader("Authorization", "Bearer " + readToken());

  // Get main contact from MultiSelect
  let mainContactId = null;
  if (mainContactMS) {
    const mainValues = mainContactMS.getValues();
    if (mainValues.length > 0) {
      mainContactId = parseInt(mainValues[0]);
    }
  }

  // Parse numeric values safely
  const parseIntSafe = (val) => {
    const parsed = parseInt(val);
    return isNaN(parsed) ? null : parsed;
  };

  var data = {
    Id: parseInt(hdid),
    Title: document.getElementById("leadName").value,
    ContactId: mainContactId,
    Description: document.getElementById("problem").value,
    JobNumber: document.getElementById("JobNumber").value,
    Solution: document.getElementById("solution").value,
    Instumental: document.getElementById("instumental").value,
    Model: document.getElementById("model").value,
    SerialNumber: document.getElementById("serialNumber").value,
    JobType: jobType[parseInt(document.getElementById("jobType").value)].jobType,
    InstumentalStatus: instumentalStatus[parseInt(document.getElementById("instumentalStatus").value)].status,
    Priority: window.prioritySlider ? parseInt(window.prioritySlider.getValues()) : 0,
    ProductId: parseIntSafe(document.getElementById("product").value),
    SaleAreaId: parseIntSafe(document.getElementById("saleArea").value),
    AssignedToUserId: parseIntSafe(document.getElementById("assignedUser").value),
    ResponseOnTime: document.getElementById("respondedWithinTimeline").checked,
    HelpDeskItems: currentHelpDeskItems.map(item => ({
      Order: item.Order,
      Description: item.Description,
      Cat: item.Cat,
      Quantity: item.Quantity,
      Bill: item.Bill,
      InventoryProductId: item.InventoryProductId || null
    })),
    PipelineId: parseInt(selectedPipeline)
  };

  // Get users from MultiSelect
  data.UserIds = getSelectedUserIds().map(id => parseInt(id));

  // Get additional contacts from MultiSelect
  let additionalContactIds = [];
  if (additionalContactsMS) {
    additionalContactIds = additionalContactsMS.getValues()
      .filter(id => id !== mainContactId?.toString())
      .map(id => parseInt(id));
  }
  data.ContactIds = additionalContactIds;

  // Debug: Log the data being sent
  console.log("=== UPDATE REQUEST DATA ===");
  console.log("Id:", data.Id, typeof data.Id);
  console.log("PipelineId:", data.PipelineId, typeof data.PipelineId);
  console.log("HelpDeskItems:", data.HelpDeskItems);
  console.log("Full data:", JSON.stringify(data, null, 2));
  console.log("===========================");

  xhr.onload = function () {
    if (xhr.status === 200) {
      xalert("Ticket updated successfully", 0, null);
      console.log("Ticket updated successfully");
      setTimeout(() => {
        window.location.href = "helpdesk.html";
      }, 1000);
    } else {
      xalert("Error:" + xhr.status + " " + xhr.responseText, 1, null);
      console.error("Error:", xhr.status);
    }
  };

  console.log(data);
  xhr.send(JSON.stringify(data));
}

function deleteLead() {
  var xhr = new XMLHttpRequest();
  xhr.open("POST", url + "/biomedapi/v2/helpdesk/ticket/delete", true);
  xhr.setRequestHeader("Content-Type", "application/json");
  xhr.setRequestHeader("Authorization", "Bearer " + readToken());

  xhr.onload = function () {
    if (xhr.status === 200) {
      xalert("Ticket deleted successfully", 0, null);
      console.log("Ticket deleted successfully");
      setTimeout(() => {
        window.location.href = "helpdesk.html";
      }, 1000);
    } else {
      xalert("Error:" + xhr.status + " " + xhr.responseText, 1, null);
      console.error("Error:", xhr.status);
    }
  };

  xhr.send(JSON.stringify({ Id: parseInt(hdid) }));
}

// HelpDeskItem Management Functions

function loadInventoryProducts() {
  const token = readToken();
  const xhr = new XMLHttpRequest();
  
  xhr.open("GET", url + "/biomedapi/v2/product/inventory", true);
  xhr.setRequestHeader("Authorization", `Bearer ${token}`);
  
  xhr.onload = function () {
    if (xhr.status === 200) {
      const response = JSON.parse(xhr.responseText);
      inventoryProducts = response.data || response;
      setupInventoryDropdowns();
    } else {
      console.error("Failed to load inventory products:", xhr.status);
      console.log("Inventory integration not available - items can still be managed without product linking");
    }
  };
  
  xhr.send();
}

function setupInventoryDropdowns() {
  if (!inventoryProducts || inventoryProducts.length === 0) return;
  
  const brands = [...new Set(inventoryProducts.map(p => p.Brand?.Name).filter(Boolean))];
  const types = [...new Set(inventoryProducts.map(p => p.Type).filter(Boolean))];
  const brandTypes = [...new Set(inventoryProducts.map(p => p.Brand?.InventoryBrandType).filter(Boolean))];
  const distributors = [...new Set(inventoryProducts.map(p => p.Brand?.InventoryBrandDistriutor).filter(Boolean))];
  
  ['itemInventoryBrand', 'editItemInventoryBrand'].forEach(id => {
    const select = document.getElementById(id);
    if (select) {
      select.innerHTML = '<option value="">All Brands</option>';
      brands.forEach(brand => {
        const option = document.createElement('option');
        option.value = brand;
        option.textContent = brand;
        select.appendChild(option);
      });
    }
  });
  
  ['itemInventoryType', 'editItemInventoryType'].forEach(id => {
    const select = document.getElementById(id);
    if (select) {
      select.innerHTML = '<option value="">All Types</option>';
      types.forEach(type => {
        const option = document.createElement('option');
        option.value = type;
        option.textContent = type;
        select.appendChild(option);
      });
    }
  });
  
  ['itemInventoryBrandType', 'editItemInventoryBrandType'].forEach(id => {
    const select = document.getElementById(id);
    if (select) {
      select.innerHTML = '<option value="">All Brand Types</option>';
      brandTypes.forEach(brandType => {
        const option = document.createElement('option');
        option.value = brandType;
        option.textContent = brandType;
        select.appendChild(option);
      });
    }
  });
  
  ['itemInventoryDistributor', 'editItemInventoryDistributor'].forEach(id => {
    const select = document.getElementById(id);
    if (select) {
      select.innerHTML = '<option value="">All Distributors</option>';
      distributors.forEach(distributor => {
        const option = document.createElement('option');
        option.value = distributor;
        option.textContent = distributor;
        select.appendChild(option);
      });
    }
  });
}

function searchInventoryProducts(modalType) {
  if (event) {
    event.preventDefault();
    event.stopPropagation();
  }
  
  if (!inventoryProducts || inventoryProducts.length === 0) {
    showSearchResults([], modalType);
    return;
  }
  
  let searchCriteria;
  if (modalType === 'add') {
    searchCriteria = {
      name: document.getElementById('itemInventoryProductName')?.value || '',
      brand: document.getElementById('itemInventoryBrand')?.value || '',
      type: document.getElementById('itemInventoryType')?.value || '',
      brandType: document.getElementById('itemInventoryBrandType')?.value || '',
      distributor: document.getElementById('itemInventoryDistributor')?.value || ''
    };
  } else {
    searchCriteria = {
      name: document.getElementById('editItemInventoryProductName')?.value || '',
      brand: document.getElementById('editItemInventoryBrand')?.value || '',
      type: document.getElementById('editItemInventoryType')?.value || '',
      brandType: document.getElementById('editItemInventoryBrandType')?.value || '',
      distributor: document.getElementById('editItemInventoryDistributor')?.value || ''
    };
  }
  
  let filteredProducts = inventoryProducts.filter(product => {
    let matches = true;
    
    if (searchCriteria.name && !product.Name.toLowerCase().includes(searchCriteria.name.toLowerCase())) matches = false;
    if (searchCriteria.brand && product.Brand && product.Brand.Name !== searchCriteria.brand) matches = false;
    if (searchCriteria.type && product.Type !== searchCriteria.type) matches = false;
    if (searchCriteria.brandType && product.Brand && product.Brand.InventoryBrandType !== searchCriteria.brandType) matches = false;
    if (searchCriteria.distributor && product.Brand && product.Brand.InventoryBrandDistriutor !== searchCriteria.distributor) matches = false;
    
    return matches;
  });
  
  showSearchResults(filteredProducts.slice(0, 20), modalType);
}

function showSearchResults(products, modalType) {
  const resultsContainer = modalType === 'add' ? 
    document.getElementById('inventorySearchResults') : 
    document.getElementById('editInventorySearchResults');
  
  const resultsContent = modalType === 'add' ? 
    document.getElementById('inventorySearchResultsContent') : 
    document.getElementById('editInventorySearchResultsContent');
    
  if (!resultsContainer || !resultsContent) return;
  
  currentSearchResults = products;
  resultsContent.innerHTML = '';
  
  if (products.length === 0) {
    resultsContent.innerHTML = '<div class="text-base-content/50 text-center p-3">No products found matching your criteria</div>';
    resultsContainer.classList.remove('hidden');
    return;
  }
  
  products.forEach((product, index) => {
    const productItem = document.createElement('div');
    productItem.className = 'product-item';
    productItem.innerHTML = `
      <div class="flex justify-between items-start">
        <div class="flex-1">
          <h6 class="font-semibold text-sm mb-1">${product.Name}</h6>
          <small class="text-base-content/60 text-xs">
            Cat No: ${product.CategoryNumber || 'N/A'} | 
            Brand: ${product.Brand?.Name || 'N/A'} | 
            Stock: ${product.StockCount || 0}
          </small>
          <div class="mt-1">
            <small class="text-base-content/50 text-xs">${product.Description || 'No description available'}</small>
          </div>
        </div>
        <button class="btn btn-sm btn-outline btn-primary ml-2" type="button" onclick="selectProductFromResults(${index}, '${modalType}')">
          Select
        </button>
      </div>
    `;
    resultsContent.appendChild(productItem);
  });
  
  resultsContainer.classList.remove('hidden');
}

function selectProductFromResults(index, modalType) {
  if (event) {
    event.preventDefault();
    event.stopPropagation();
  }
  
  if (currentSearchResults && currentSearchResults[index]) {
    selectInventoryProduct(currentSearchResults[index], modalType);
  }
}

function selectInventoryProduct(product, modalType) {
  if (modalType === 'add') {
    document.getElementById("itemOrder").value = product.Name || '';
    document.getElementById("itemCategory").value = product.CategoryNumber || '';
    document.getElementById("itemDescription").value = product.Description || '';
    document.getElementById("selectedInventoryProduct").textContent = product.Name || 'None';
    document.getElementById("itemInventoryProduct").value = product.Id || '';
    document.getElementById("inventorySearchResults").classList.add('hidden');
  } else if (modalType === 'edit') {
    document.getElementById("editItemOrder").value = product.Name || '';
    document.getElementById("editItemCategory").value = product.CategoryNumber || '';
    document.getElementById("editItemDescription").value = product.Description || '';
    document.getElementById("editSelectedInventoryProduct").textContent = product.Name || 'None';
    document.getElementById("editItemInventoryProduct").value = product.Id || '';
    document.getElementById("editInventorySearchResults").classList.add('hidden');
  }
}

function clearInventorySelection(modalType) {
  if (modalType === 'add') {
    document.getElementById("itemInventoryProductName").value = '';
    document.getElementById("itemInventoryBrand").value = '';
    document.getElementById("itemInventoryType").value = '';
    document.getElementById("itemInventoryBrandType").value = '';
    document.getElementById("itemInventoryDistributor").value = '';
    document.getElementById("itemOrder").value = '';
    document.getElementById("itemCategory").value = '';
    document.getElementById("itemDescription").value = '';
    document.getElementById("selectedInventoryProduct").textContent = 'None';
    document.getElementById("itemInventoryProduct").value = '';
    document.getElementById("inventorySearchResults").classList.add('hidden');
  } else if (modalType === 'edit') {
    document.getElementById("editItemInventoryProductName").value = '';
    document.getElementById("editItemInventoryBrand").value = '';
    document.getElementById("editItemInventoryType").value = '';
    document.getElementById("editItemInventoryBrandType").value = '';
    document.getElementById("editItemInventoryDistributor").value = '';
    document.getElementById("editSelectedInventoryProduct").textContent = 'None';
    document.getElementById("editItemInventoryProduct").value = '';
    document.getElementById("editInventorySearchResults").classList.add('hidden');
  }
}

function displayHelpDeskItems(items) {
  const tbody = document.getElementById("helpDeskItemsTableBody");
  tbody.innerHTML = "";
  
  if (!items || items.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6" class="text-center text-base-content/50 py-4">No items/spare parts recorded</td></tr>';
    return;
  }
  
  items.forEach((item, index) => {
    const row = document.createElement("tr");
    
    row.innerHTML = `
      <td class="text-sm">${item.Order || 'N/A'}</td>
      <td class="text-sm">${item.Description || 'N/A'}</td>
      <td class="text-sm">${item.Cat || 'N/A'}</td>
      <td class="text-sm">${item.Quantity || 0}</td>
      <td>
        <span class="badge badge-sm ${item.Bill ? 'badge-warning' : 'badge-ghost'}">
          ${item.Bill ? 'Billable' : 'Internal'}
        </span>
      </td>
      <td>
        <div class="flex gap-1">
          <button type="button" class="btn btn-ghost btn-xs" onclick="editHelpDeskItem(${item.Id || index})" title="Edit">
            <i class="fas fa-edit"></i>
          </button>
          <button type="button" class="btn btn-ghost btn-xs text-error" onclick="deleteHelpDeskItem(${item.Id || index})" title="Delete">
            <i class="fas fa-trash"></i>
          </button>
        </div>
      </td>
    `;
    
    tbody.appendChild(row);
  });
}

function saveHelpDeskItem() {
  const formData = {
    TicketId: parseInt(hdid),
    Order: document.getElementById("itemOrder").value || null,
    Description: document.getElementById("itemDescription").value || null,
    Cat: document.getElementById("itemCategory").value || null,
    Quantity: parseInt(document.getElementById("itemQuantity").value) || 1,
    Bill: document.getElementById("itemBillable").value === "true",
    InventoryProductId: document.getElementById("itemInventoryProduct").value ? parseInt(document.getElementById("itemInventoryProduct").value) : null
  };
  
  const token = readToken();
  const xhr = new XMLHttpRequest();
  
  xhr.open("POST", url + "/biomedapi/v2/helpdesk/item/create", true);
  xhr.setRequestHeader("Content-Type", "application/json");
  xhr.setRequestHeader("Authorization", `Bearer ${token}`);
  
  xhr.onload = function () {
    if (xhr.status === 200) {
      // API returns just the item Id as a number, not a JSON object
      const itemId = parseInt(xhr.responseText);
      console.log("Item created with Id:", itemId);
      xalert("Item added successfully", 0, 3000);
      
      const newItem = {
        Id: itemId,
        Order: formData.Order,
        Description: formData.Description,
        Cat: formData.Cat,
        Quantity: formData.Quantity,
        Bill: formData.Bill,
        InventoryProductId: formData.InventoryProductId
      };
      
      currentHelpDeskItems.push(newItem);
      displayHelpDeskItems(currentHelpDeskItems);
      
      // Close modal
      document.getElementById("addItemModal").close();
      
      // Reset form
      document.getElementById("itemOrder").value = '';
      document.getElementById("itemDescription").value = '';
      document.getElementById("itemCategory").value = '';
      document.getElementById("itemQuantity").value = 1;
      document.getElementById("itemBillable").value = 'true';
      clearInventorySelection('add');
    } else {
      xalert("Failed to add item: " + xhr.responseText, 1, 5000);
    }
  };
  
  xhr.send(JSON.stringify(formData));
}

function editHelpDeskItem(itemId) {
  const item = currentHelpDeskItems.find(item => (item.Id || currentHelpDeskItems.indexOf(item)) == itemId);
  if (!item) return;
  
  currentEditingItemId = itemId;
  
  document.getElementById("editItemId").value = item.Id || '';
  document.getElementById("editItemOrder").value = item.Order || '';
  document.getElementById("editItemDescription").value = item.Description || '';
  document.getElementById("editItemCategory").value = item.Cat || '';
  document.getElementById("editItemQuantity").value = item.Quantity || 1;
  document.getElementById("editItemBillable").value = item.Bill ? "true" : "false";
  
  // Clear search form fields
  document.getElementById("editItemInventoryProductName").value = '';
  document.getElementById("editItemInventoryBrand").value = '';
  document.getElementById("editItemInventoryType").value = '';
  document.getElementById("editItemInventoryBrandType").value = '';
  document.getElementById("editItemInventoryDistributor").value = '';
  document.getElementById("editSelectedInventoryProduct").textContent = 'None';
  document.getElementById("editItemInventoryProduct").value = '';
  document.getElementById("editInventorySearchResults").classList.add('hidden');
  
  document.getElementById("editItemModal").showModal();
}

function updateHelpDeskItem() {
  const formData = {
    Id: parseInt(document.getElementById("editItemId").value) || currentEditingItemId,
    Order: document.getElementById("editItemOrder").value || null,
    Description: document.getElementById("editItemDescription").value || null,
    Cat: document.getElementById("editItemCategory").value || null,
    Quantity: parseInt(document.getElementById("editItemQuantity").value) || 1,
    Bill: document.getElementById("editItemBillable").value === "true",
    InventoryProductId: document.getElementById("editItemInventoryProduct").value ? parseInt(document.getElementById("editItemInventoryProduct").value) : null
  };
  
  const token = readToken();
  const xhr = new XMLHttpRequest();
  
  xhr.open("POST", url + "/biomedapi/v2/helpdesk/item/update", true);
  xhr.setRequestHeader("Content-Type", "application/json");
  xhr.setRequestHeader("Authorization", `Bearer ${token}`);
  
  xhr.onload = function () {
    if (xhr.status === 200) {
      xalert("Item updated successfully", 0, 3000);
      
      const itemIndex = currentHelpDeskItems.findIndex(item => 
        (item.Id || currentHelpDeskItems.indexOf(item)) == currentEditingItemId
      );
      
      if (itemIndex !== -1) {
        currentHelpDeskItems[itemIndex] = {
          ...currentHelpDeskItems[itemIndex],
          Order: formData.Order,
          Description: formData.Description,
          Cat: formData.Cat,
          Quantity: formData.Quantity,
          Bill: formData.Bill,
          InventoryProductId: formData.InventoryProductId
        };
      }
      
      displayHelpDeskItems(currentHelpDeskItems);
      document.getElementById("editItemModal").close();
    } else {
      xalert("Failed to update item: " + xhr.responseText, 1, 5000);
    }
  };
  
  xhr.send(JSON.stringify(formData));
}

function deleteHelpDeskItem(itemId) {
  if (!confirm("Are you sure you want to delete this item/spare part?")) {
    return;
  }
  
  const item = currentHelpDeskItems.find(item => (item.Id || currentHelpDeskItems.indexOf(item)) == itemId);
  if (!item || !item.Id) {
    currentHelpDeskItems = currentHelpDeskItems.filter((_, index) => index != itemId);
    displayHelpDeskItems(currentHelpDeskItems);
    return;
  }
  
  const token = readToken();
  const xhr = new XMLHttpRequest();
  
  xhr.open("POST", url + "/biomedapi/v2/helpdesk/item/delete", true);
  xhr.setRequestHeader("Content-Type", "application/json");
  xhr.setRequestHeader("Authorization", `Bearer ${token}`);
  
  xhr.onload = function () {
    if (xhr.status === 200) {
      xalert("Item deleted successfully", 0, 3000);
      currentHelpDeskItems = currentHelpDeskItems.filter(item => item.Id != itemId);
      displayHelpDeskItems(currentHelpDeskItems);
    } else {
      xalert("Failed to delete item: " + xhr.responseText, 1, 5000);
    }
  };
  
  xhr.send(JSON.stringify({ Id: parseInt(item.Id) }));
}
