const urlParams = new URLSearchParams(window.location.search);
const leadid = urlParams.get("leadid");
document.getElementById("d3Button").addEventListener("click", function () {
  window.location.href = `./d3.html?type=${"leads"}&id=${leadid}`;
});

const modalUsersList = document.getElementById("modalUsersList");
const select = document.getElementById("usersSelecter");
const groupSelect = document.getElementById("groupSelecter");
const contactSelect = document.getElementById("contactsSelecter");
const mainContactSelect = document.getElementById("mainContactsSelecter");

const modalContact = document.getElementById("modalContact");
const mainContactsList = document.getElementById("mainContactsList");

const modalContactsList = document.getElementById("modalContactsList");

// Sync modalIndividualPermissionsList with individualPermissionsUsersList
function syncContactsList() {
    const mainContactsList = document.getElementById('mainContactsList');
    mainContactsList.innerHTML = modalContactsList.innerHTML;
}

// Call the syncPermissionsList function whenever there is a change in modalIndividualPermissionsList
const observer = new MutationObserver(syncContactsList);
observer.observe(modalContactsList, { childList: true });

// Add an event listener to mainContactsList to update modalContact when its value changes

var mainuserid;





window.onload = function () {
  // Get the leadid from the URL parameter

  if (leadid === null) {
    xalert("Error: No leadid parameter found in the URL", 1, null);
    return;
  }

  // Get the token from the readToken() function
  const token = readToken();

  // Create a new XHR object
  const xhr = new XMLHttpRequest();

  // Open the XHR request
  xhr.open("GET", url + `/biomedapi/v2/crm/leads/${leadid}`, true);

  // Set the request headers
  xhr.setRequestHeader("Authorization", `Bearer ${token}`);

  // Set the onload function to handle the response
  xhr.onload = function () {
    if (xhr.status === 200) {
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
          // Add any additional attributes or data to the option element if needed
          // option.setAttribute("data-subtext", product.Description);
          // option.setAttribute("data-price", product.Price);
          // ...

          // Append the option to the select element
          productSelect.appendChild(option);
        });
      });

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
          // Add any additional attributes or data to the option element if needed
          // option.setAttribute("data-subtext", saleArea.Description);
          // option.setAttribute("data-price", saleArea.Price);
          // ...

          // Append the option to the select element
          saleAreaSelect.appendChild(option);
        });
      });
      // Parse the response JSON
      const response = JSON.parse(xhr.responseText);

      if (response.LeadName !== undefined && response.LeadName !== null) {
        document.getElementById("leadName").value = response.LeadName;
      }
      // if (response.MainCustomer !== undefined && response.MainCustomer !== null) {
      //     document.getElementById('mainCustomer').value = response.MainCustomer;
      // }
      // if (response.MainCustomerId !== undefined && response.MainCustomerId !== null) {
      //     document.getElementById('mainCustomerId').value = response.MainCustomerId;
      // }
      // if (response.MainUser !== undefined && response.MainUser !== null) {
      //     document.getElementById('mainUser').value = response.MainUser;
      // }
      // if (response.MainUserId !== undefined && response.MainUserId !== null) {
      //     document.getElementById('mainUserId').value = response.MainUserId;
      // }
      if (response.Creation !== undefined && response.Creation !== null) {
        document.getElementById("creation").value = timeFuck(response.Creation);
      }
      if (response.Expected !== undefined && response.Expected !== null) {
        document.getElementById("expected").value = timeFuck(response.Expected);
      }
      if (
        response.ExpectedRevenue !== undefined &&
        response.ExpectedRevenue !== null
      ) {
        document.getElementById("expectedRevenue").value =
          response.ExpectedRevenue;
      }
      if (
        response.AchivedRevenue !== undefined &&
        response.AchivedRevenue !== null
      ) {
        document.getElementById("achievedRevenue").value =
          response.AchivedRevenue;
      }
      if (
        response.CustomerNeeds !== undefined &&
        response.CustomerNeeds !== null
      ) {
        document.getElementById("customerNeeds").value = response.CustomerNeeds;
      }
      if (
        response.KeyDicisionMaker !== undefined &&
        response.KeyDicisionMaker !== null
      ) {
        document.getElementById("keyDecisionMaker").value =
          response.KeyDicisionMaker;
      }
      if (
        response.KeySellingPoints !== undefined &&
        response.KeySellingPoints !== null
      ) {
        document.getElementById("keySellingPoints").value =
          response.KeySellingPoints;
      }
      if (
        response.CompetitorInfo !== undefined &&
        response.CompetitorInfo !== null
      ) {
        document.getElementById("competitorInfo").value =
          response.CompetitorInfo;
      }
      if (
        response.AdditionalInfo !== undefined &&
        response.AdditionalInfo !== null
      ) {
        document.getElementById("additionalInfo").value =
          response.AdditionalInfo;
      }
      if (response.Budget !== undefined && response.Budget !== null) {
        document.getElementById("budget").value = response.Budget;
      }
      if (
        response.FundingSource !== undefined &&
        response.FundingSource !== null
      ) {
        document.getElementById("fundingSource").value = response.FundingSource;
      }
      if (response.ProjectID !== undefined && response.ProjectID !== null) {
        document.getElementById("projectID").value = response.ProjectID;
      }
      if (response.IsPO !== undefined && response.IsPO !== null) {
        document.getElementById("isPO").value = response.IsPO;
      }
      if (response.IsCollected !== undefined && response.IsCollected !== null) {
        document.getElementById("isCollected").value = response.IsCollected;
      }
      if (response.PaymentDue !== undefined && response.PaymentDue !== null) {
        document.getElementById("paymentDue").value = timeFuck(
          response.PaymentDue
        );
      }
      if (response.Other !== undefined && response.Other !== null) {
        document.getElementById("other").value = response.Other;
      }
      if (response.ProductId !== undefined && response.ProductId !== null) {
        document.getElementById("product").value = response.ProductId;
      }
      if (response.SaleAreaId !== undefined && response.SaleAreaId !== null) {
        document.getElementById("saleArea").value = response.SaleAreaId;
      }
      // Use the extracted data as needed
      // ...
      const pipelineId = response.CRMPipelineId;
      
      getPipelines((err, pipelines) => {
        if (err) {
          console.error("Failed to fetch pipelines:", err);
          return;
        }

        const pipelineSelection = document.getElementById("pipelineSelection");
        window.allPipelines = pipelines; // Store for later use

        pipelines.forEach((pipeline) => {
          const step = document.createElement("li");
          step.className = "step cursor-pointer hover:opacity-80 transition-opacity";
          step.id = `pipeline${pipeline.Id}`;
          step.setAttribute('data-pipeline-id', pipeline.Id);
          step.textContent = pipeline.PipelineName;
          step.onclick = function() {
            selectPipelineStep(pipeline.Id);
          };
          pipelineSelection.appendChild(step);
        });
        
        // Set selected pipeline AFTER steps are created
        selectPipelineStep(pipelineId);
        
        // Note: cachingObject() is called after Users MultiSelect is fully loaded
        // to ensure Responsibles display is complete before caching
      }, false);

      // === Users MultiSelect Integration ===
      const primaryUserId = response.MainUserId;
      mainuserid = primaryUserId;
      let allUsersData = [];
      let allGroupsData = [];
      let groupMembersMap = {}; // Store group members: { groupId: [userId1, userId2, ...] }

      // Load users first
      getUsers((error, users) => {
        if (error) {
          console.error("Failed to fetch users:", error);
          return;
        }
        
        allUsersData = users;
        
        // Find primary user data
        const primaryUser = users.find(u => u.Id === primaryUserId);
        const primaryUserDisplay = primaryUser 
          ? `${primaryUser.FirstName} ${primaryUser.LastName} (${primaryUser.Position})`
          : 'Unknown';
        
        // Build users options (excluding primary)
        const usersOptions = users
          .filter(u => u.Id !== primaryUserId)
          .map(u => ({
            value: u.Id.toString(),
            label: `${u.FirstName} ${u.LastName}`,
            subtext: u.Position
          }));

        // Load groups
        getGroups((err, groups) => {
          if (err) {
            console.error("Failed to fetch groups:", err);
            return;
          }
          
          allGroupsData = groups;
          
          // Build groups options
          const groupsOptions = groups.map(g => ({
            value: g.Id.toString(),
            label: g.GroupName
          }));
          
          // Initialize MultiSelects
          if (typeof initUsersMultiSelects === 'function') {
            initUsersMultiSelects(usersOptions, groupsOptions, primaryUserId, primaryUserDisplay);
          }
          
          // Store group members data for quick lookup
          // We need to preload all group members
          let groupsLoaded = 0;
          groups.forEach(group => {
            getGroupMembers(group.Id, (memberErr, memberData) => {
              groupsLoaded++;
              if (!memberErr && memberData && memberData.GroupUsers) {
                groupMembersMap[group.Id] = memberData.GroupUsers.map(u => u.UserId);
              }
              
              // When all groups loaded, set the data
              if (groupsLoaded === groups.length) {
                if (typeof setGroupsData === 'function') {
                  setGroupsData(groupMembersMap);
                }
                
                // Now set existing selected users
                const existingUserIds = response.LeadUsers
                  .map(lu => lu.UserId)
                  .filter(id => id !== primaryUserId)
                  .map(id => id.toString());
                
                if (existingUserIds.length > 0 && typeof setUsersValues === 'function') {
                  setUsersValues(existingUserIds);
                }
                
                // Cache object values AFTER Users MultiSelect is fully loaded
                setTimeout(() => cachingObject(), 100);
              }
            });
          });
          
          // If no groups, still set existing users
          if (groups.length === 0) {
            const existingUserIds = response.LeadUsers
              .map(lu => lu.UserId)
              .filter(id => id !== primaryUserId)
              .map(id => id.toString());
            
            if (existingUserIds.length > 0 && typeof setUsersValues === 'function') {
              setUsersValues(existingUserIds);
            }
            
            // Cache object values AFTER Users MultiSelect is fully loaded
            setTimeout(() => cachingObject(), 100);
          }
        }, false);
      }, false);


      
      //Get contacts


      mainContactSelect.innerHTML = "";
      contactSelect.innerHTML = "";
      getContacts((err, contacts) => {
        if (err) {
          console.error("Failed to fetch users:", err);
          xalert("Failed to fetch users:" + err, 1, null);
          return;
        }
        
        // Build options array for MultiSelect
        const msOptions = [];
        
        contacts.forEach((contact) => {
          const option = document.createElement("option");
          option.value = contact.Id;
          option.textContent = contact.Name;
          if (contact.Position !== null && contact.Position !== undefined) {
            option.setAttribute("data-subtext", `${contact.Position}`);
          }
          contactSelect.appendChild(option);

          const mainOption = document.createElement("option");
          mainOption.value = contact.Id;
          mainOption.textContent = contact.Name;
          if (contact.Position !== null && contact.Position !== undefined) {
            mainOption.setAttribute("data-subtext", `${contact.Position}`);
          }
          mainContactSelect.appendChild(mainOption);
          
          // Add to MultiSelect options
          msOptions.push({
            value: contact.Id.toString(),
            label: contact.Position ? `${contact.Name} (${contact.Position})` : contact.Name
          });
        });
        
        // Initialize MultiSelect component if function exists
        if (typeof initContactMultiSelects === 'function') {
            initContactMultiSelects(msOptions);
        } else if (typeof initAdditionalContactsMS === 'function') {
            initAdditionalContactsMS(msOptions);
        }
        
        // Set main contact value
        if (typeof setMainContactValue === 'function') {
            setMainContactValue(response.MainCustomerId);
        } else {
            mainContactSelect.value = response.MainCustomerId.toString();
        }
        
        // Set additional contacts
        const contactIds = response.LeadContacts.map(
            (contact) => contact.ContactId
        ).filter((id) => id !== response.MainCustomerId);
        const contactSelectValues = contactIds.map(String);
        
        // Set values in hidden select
        Array.from(contactSelect.options).forEach(opt => {
            opt.selected = contactSelectValues.includes(opt.value);
        });
        
        // Set values in MultiSelect
        if (typeof setAdditionalContactValues === 'function') {
            setAdditionalContactValues(contactSelectValues);
        } else if (typeof setContactCheckboxValues === 'function') {
            setContactCheckboxValues(contactSelectValues);
        }
        
        // Update preview
        if (typeof updateContactsPreview === 'function') {
            updateContactsPreview();
        }
        
        // Legacy selectpicker calls (will be no-op if not loaded)
        if ($.fn.selectpicker) {
            $(mainContactSelect).on("changed.bs.select", modalContactsUpdate);
            $(contactSelect).on("changed.bs.select", modalContactsUpdate);
            $(contactSelect).selectpicker("refresh");
            $(mainContactSelect).selectpicker("refresh");
            $(mainContactSelect).selectpicker("val", response.MainCustomerId.toString());
            $(contactSelect).selectpicker("val", contactSelectValues);
        }
      }, false);
      
      // Legacy selectpicker calls
      if ($.fn.selectpicker) {
          $(contactSelect).selectpicker("refresh");
          $(mainContactSelect).selectpicker("refresh");
      }
      
      // Load Activity Logs for this lead
      loadLogs(null, parseInt(leadid), null, null, null, null);
      
      // cachingObject() moved to getPipelines callback to ensure pipeline is selected first
    } else {
      // Handle the error case
      xalert("Error:" + xhr.status, 1, null);
      console.error("Error:", xhr.status);
    }
  };

  // Send the XHR request
  xhr.send();
};

function contactsModal() {
    var contactsModal = new bootstrap.Modal("#multiContactModal", {
        focus: true
    });
    contactsModal.show();
    
}

function usersModal() {
  var multiSelectModal = new bootstrap.Modal("#multiSelectModal", {
    focus: true
  });
  multiSelectModal.show();
}
async function updateLead(){
  let changedComponent = await compareChange();
  let readableChanges = changedComponent.map(change => {
    let oldValue = Array.isArray(change.oldValue) ? change.oldValue.join(", ") : (typeof(change.oldValue)==='boolean'? change.oldValue:change.oldValue || "N/A");
    let newValue = Array.isArray(change.newValue) ? change.newValue.join(", ") : (typeof(change.newValue)==='boolean'? change.newValue:change.newValue || "N/A");
    return `${change.field}: ${oldValue} -> ${newValue}`;
  }).join("\n");

  console.log(readableChanges);
  createLog(readableChanges, JSON.stringify(changedComponent), parseInt(leadid), null, null, null, null, 4, function(err, log){
    if(err){
      console.error(err);
      return;
    }
    console.log('Log created successfully:', log);
    updateLeadRequest();
  });
}

function updateLeadRequest() {
  // Create a new XMLHttpRequest object
  


  var xhr = new XMLHttpRequest();
  if (typeof getSelectedPipelineId !== 'function' || !getSelectedPipelineId()) {
    // No pipeline selected
    xalert("Error: No pipeline selected", 2, 5000);
    return;
  } 
  // Configure the POST request
  xhr.open("POST", url + "/biomedapi/v2/crm/leads/update", true);

  // Set the request headers
  xhr.setRequestHeader("Content-Type", "application/json");
  xhr.setRequestHeader("Authorization", "Bearer " + readToken());

  var mainContacts = Array.from(mainContactSelect.selectedOptions)
  // Prepare the data from the HTML form
  var data = {
    Id: leadid,
    LeadName: document.getElementById("leadName").value,
    MainCustomerId: parseInt(mainContacts[0].value),
    MainUserId: parseInt(mainuserid),
    Creation: timeFormater(document.getElementById("creation").value),
    LastUpdated: timeFormater(Date.now()),
    Expected: timeFormater(document.getElementById("expected").value),
    ExpectedRevenue: document.getElementById("expectedRevenue").value,
    AchivedRevenue: document.getElementById("achievedRevenue").value,
    CustomerNeeds: document.getElementById("customerNeeds").value,
    KeyDecisionMaker: document.getElementById("keyDecisionMaker").value,
    KeySellingPoints: document.getElementById("keySellingPoints").value,
    CompetitorInfo: document.getElementById("competitorInfo").value,
    AdditionalInfo: document.getElementById("additionalInfo").value,
    Budget: document.getElementById("budget").value,
    FundingSource: document.getElementById("fundingSource").value,
    ProjectID: document.getElementById("projectID").value,
    IsPO: document.getElementById("isPO").checked,
    IsCollected: document.getElementById("isCollected").checked,
    PaymentDue: timeFormater(document.getElementById("paymentDue").value),
    Other: document.getElementById("other").value,
    PipelineId: getSelectedPipelineId(),

    //UserIds: document.getElementById('userIds').value.split(',').map(Number)
  };
  // Get UserIds from MultiSelect + Primary User
  var selectedUserIds = typeof getSelectedUserIds === 'function' ? getSelectedUserIds() : [];
  var allUserIds = selectedUserIds.map(id => parseInt(id));
  // Add primary user ID (if available)
  if (typeof primaryUserId !== 'undefined' && primaryUserId) {
    allUserIds.unshift(parseInt(primaryUserId));
  }
  data.UserIds = allUserIds;
  data.ContactIds = Array.from(
      document.getElementById("contactsSelecter").selectedOptions
  ).filter(option => option.value !== mainContacts[0].value)
  .map(option => parseInt(option.value));
  data.ProductId = parseInt(document.getElementById("product").value);
  data.SaleAreaId = parseInt(document.getElementById("saleArea").value);

  // Set the onload function to handle the response
  xhr.onload = function () {
    if (xhr.status === 200) {
      // Handle the success case
      xalert("Lead updated successfully", 0, null);
      console.log("Lead updated successfully");
      setTimeout(() => {
        window.location.href = "crm.html";
      }, 1000);
    } else {
      // Handle the error case
      xalert("Error:" + xhr.status + " " + xhr.responseText, 1, null);
      console.error("Error:", xhr.status);
    }
  };

  // Send the request with the JSON stringified data
  xhr.send(JSON.stringify(data));
}

function modalContactsUpdate() {
    const mainselectedOptions = Array.from(mainContactSelect.selectedOptions);
    modalContactsList.innerHTML = "";
    mainselectedOptions.forEach((option) => {
      const badge = document.createElement("span");
      badge.classList.add(
        "badge",
        "bg-info",
        "text-dark",
        "py-1",
        "m-1",
        "align-middle",
        "text-wrap"
      );
      badge.innerHTML = option.getAttribute("data-subtext")
        ? `${option.textContent} (${option.getAttribute(
            "data-subtext"
          )})`
        : option.textContent;
      modalContactsList.appendChild(badge);
    });
    const selectedOptions = Array.from(contactSelect.selectedOptions);
    
    selectedOptions.forEach((option) => {
      const badge = document.createElement("span");
      badge.classList.add(
        "badge",
        "biomed-bg-accent",
        "text-dark",
        "py-1",
        "m-1",
        "align-middle",
        "text-wrap"
      );
      badge.innerHTML = option.getAttribute("data-subtext")
        ? `${option.textContent} (${option.getAttribute(
            "data-subtext"
          )})`
        : option.textContent;
        if(mainselectedOptions[0].value !== option.value){
            modalContactsList.appendChild(badge);
        }
      
    });
}

function deleteLead(){
  // Create a new XMLHttpRequest object
  var xhr = new XMLHttpRequest();

  // Configure the DELETE request
  xhr.open("POST", url + "/biomedapi/v2/crm/leads/delete", true);
  xhr.setRequestHeader("Content-Type", "application/json");
  // Set the request headers
  xhr.setRequestHeader("Authorization", "Bearer " + readToken());

  // Set the onload function to handle the response
  xhr.onload = function () {
    if (xhr.status === 200) {
      // Handle the success case
      xalert("Lead deleted successfully", 0, null);
      console.log("Lead deleted successfully");
      setTimeout(() => {
        window.location.href = "crm.html";
      }, 1000);
    } else {
      // Handle the error case
      xalert("Error:" + xhr.status + " " + xhr.responseText, 1, null);
      console.error("Error:", xhr.status);
    }
  };

  
  // Send the DELETE request
  xhr.send(JSON.stringify({ Id: parseInt(leadid) }));
}
