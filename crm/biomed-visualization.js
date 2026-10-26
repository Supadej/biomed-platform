function getPivotHeight() {
    var container = document.getElementById('pivotContainer');
    if (container && container.offsetHeight > 100) return container.offsetHeight;
    return Math.max(500, window.innerHeight - 280);
}

const pivot = new WebDataRocks({
    width: "100%",
    height: getPivotHeight(),
    container: "#pivotContainer",
    toolbar: true, // Enable the toolbar
    reportcomplete: function() {
        pivot.off('reportcomplete');
        var h = getPivotHeight();
        pivot.setSize({ height: h });
    },
    beforetoolbarcreated: customizeToolbar, // Customize the toolbar
    global: {
        localization: {
            grid: {
                blankMember: ".Not Assigned"
            }
        }
    },
    options: {
        grid: {
            type: "classic",
            showFilter: true,
            showHeaders: true,
            showHierarchies: true,
            showReportFiltersArea: true
        },
        configuratorActive: false,
        showAggregations: false,
        showCalculatedValuesButton: true,
        showDefaultSlice: false
    }
});

function customizeToolbar(toolbar) {
    // Get all tabs from the toolbar
    let tabs = toolbar.getTabs();
    
    // Filter out the Connect, Open, Save, and Export tabs by their IDs
    toolbar.getTabs = function() {
        tabs = tabs.filter(tab => 
            tab.id !== "wdr-tab-connect" && 
            tab.id !== "wdr-tab-open" && 
            tab.id !== "wdr-tab-save" && 
            tab.id !== "wdr-tab-export"
        );

    // Add custom tabs for Pivot Leads, Pivot Events, and Pivot HelpDesk
    tabs.push(
        {
            id: "wdr-tab-pivotleads", // Unique ID for Pivot Leads tab
            title: "Leads", // Title displayed on the tab
            handler: pivotLeadsHandler, // Function to run when the tab is clicked
            icon: `<i class="fi fi-rr-list"></i>` // Bootstrap Icon for list (e.g., leads)
        }/*,
        {
            id: "wdr-tab-pivotevents", // Unique ID for Pivot Events tab
            title: "Events", // Title displayed on the tab
            handler: pivotEventsHandler, // Function to run when the tab is clicked
            icon: `<i class="fi fi-rr-calendar-day"></i>` // Bootstrap Icon for calendar/event
        },
        {
            id: "wdr-tab-pivothelpdesk", // Unique ID for Pivot HelpDesk tab
            title: "Tickets", // Title displayed on the tab
            handler: pivotHelpDeskHandler, // Function to run when the tab is clicked
            icon: `<i class="fi fi-rr-wrench-alt"></i>` // Bootstrap Icon for headset/support
        }*/ 
    );
        return tabs;
    };
}
// Handler functions for each custom tab
function pivotLeadsHandler() {
    console.log("Switching to Pivot Leads...");
    PivotLeads(); // Call the existing PivotLeads function
}

function pivotEventsHandler() {
    console.log("Switching to Pivot Events...");
    PivotEvents(); // Call the new PivotEvents function
}

function pivotHelpDeskHandler() {
    console.log("Switching to Pivot HelpDesk...");
    PivotHelpDesk(); // Call the new PivotHelpDesk function
}


async function LeadProcessing(leads) {
    
    // Get targets data from server
    let targets = [];
    try {
        targets = await promiseTargets({});
        console.log("Loaded targets:", targets);
    } catch (error) {
        console.error("Failed to load targets:", error);
    }
    
    let leadsProcessed = [];
    for (const lead of leads) {
        let leadProcessed = {
            Id: lead.Id,
            Name: lead.LeadName + "(" + lead.Id + ")",
            AchivedRevenue: lead.AchivedRevenue,
            Budget: lead.Budget,
            CRMPipelineId: lead.CRMPipelineId,
            Creation: lead.Creation,
            Expected: lead.Expected,
            ExpectedRevenue: lead.ExpectedRevenue,
            isCollected: lead.IsCollected === true ? true : false,
            isPO: lead.IsPO === true ? true : false,
            NumberOfUsers: lead.LeadUsers ? lead.LeadUsers.length + 1 : 1,
            LastLogDate: lead.Logs && lead.Logs.length > 0 ? lead.Logs[lead.Logs.length - 1].DateTime : lead.Creation,
            TotalDuration: Math.floor((new Date(lead.LastUpdated || lead.Creation) - new Date(lead.Creation)) / (1000 * 60 * 60 * 24))
        }
        
        // Get MainUser information
        let user = await promiseUserById(lead.MainUserId);
        leadProcessed.MainUser = user ? user.FirstName + " " + user.LastName + "(" + user.Position + ")" : "Unknown User";
        
        // Get MainCustomer information
        leadProcessed.MainCustomer = lead.MainCustomerId ? (await promiseContactById(lead.MainCustomerId)).Name : null;
        
        // Get SaleArea information
        let saleArea = lead.SaleAreaId ? await promiseSaleAreaById(lead.SaleAreaId) : null;
        leadProcessed.SaleArea = saleArea ? saleArea.Name : null;
        
        // Get Product information
        let product = lead.ProductId ? await promiseProductById(lead.ProductId) : null;
        leadProcessed.Product = product ? product.Name : null;
        
        // Get Pipeline information with Order prefix
        if (lead.CRMPipelineId) {
            let pipeline = await promiseCRMPipelineById(lead.CRMPipelineId);
            leadProcessed.Pipeline = pipeline ? `(${pipeline.Order}) ${pipeline.PipelineName}` : null;
        } else {
            leadProcessed.Pipeline = null;
        }
        
        // Process Expected date to Year-Month format (2025-04)
        if (lead.Expected) {
            let expectedDate = new Date(lead.Expected);
            let year = expectedDate.getFullYear();
            let month = String(expectedDate.getMonth() + 1).padStart(2, '0'); // Month is 0-indexed
            leadProcessed.ExpectedYearMonth = `${year}-${month}`;
            leadProcessed.ExpectedYear = year.toString();
        } else {
            leadProcessed.ExpectedYearMonth = null;
            leadProcessed.ExpectedYear = null;
        }
        
        // Find matching targets for this lead
        let matchingTargets = [];
        if (lead.Expected && lead.ProductId && lead.SaleAreaId) {
            const expectedDate = new Date(lead.Expected);
            
            matchingTargets = targets.filter(target => {
                const startDate = new Date(target.StartDate);
                const endDate = new Date(target.EndDate);
                
                return expectedDate >= startDate && 
                       expectedDate <= endDate && 
                       target.ProductID === lead.ProductId && 
                       target.SaleAreaID === lead.SaleAreaId;
            });
        }
        
        // Process target information
        if (matchingTargets.length > 0) {
            // Use the first matching target (or you could aggregate multiple targets)
            const target = matchingTargets[0];
            
            leadProcessed.TargetValue = target.TargetValue;
            // Format EndDate as Year-Month-Day[Name]
            
            const endDate = new Date(target.EndDate);
            const QandY = getQuarterAndYearByDate(endDate);
            const year = endDate.getFullYear();
            const month = String(endDate.getMonth() + 1).padStart(2, '0');
            const day = String(endDate.getDate()).padStart(2, '0');
            leadProcessed.TargetName = `Y${QandY.year}-${QandY.quarter}`;

            // Create TargetLabel: TargetName-ProductName-SaleAreaName
            const productName = product ? product.Name : "Unknown Product";
            const saleAreaName = saleArea ? saleArea.Name : "Unknown SaleArea";
            leadProcessed.TargetLabel = `${target.Name}-${productName}-${saleAreaName}`;
            leadProcessed.TargetId = target.Id;
            leadProcessed.TargetObject = target; // Store the full target object for reference
            
            // Add a unique target identifier for proper aggregation
            leadProcessed.UniqueTargetKey = `${target.Id}_${target.TargetValue}`;
            
        } else {
            leadProcessed.TargetValue = 0; // Changed from -1 to 0 for better aggregation
            leadProcessed.TargetName = "No Target";
            leadProcessed.TargetLabel = "No Target";
            leadProcessed.TargetId = -1; // No target ID if no target found
            leadProcessed.TargetObject = null; // No target object if no target found
            leadProcessed.UniqueTargetKey = "no_target";
        }
        
        leadsProcessed.push(leadProcessed);
    }

    // Post-process to handle unique target aggregation
    // For each unique combination of Product+SaleArea+TargetId, ensure target is only counted once
    const targetCounts = new Map();
    
    for (const lead of leadsProcessed) {
        if (lead.TargetId !== -1) {
            // Create a key for each unique combination of grouping fields + TargetId
            const groupKey = `${lead.Product || 'null'}_${lead.SaleArea || 'null'}_${lead.TargetId}`;
            
            if (!targetCounts.has(groupKey)) {
                targetCounts.set(groupKey, {
                    firstLeadIndex: leadsProcessed.indexOf(lead),
                    targetValue: lead.TargetValue,
                    count: 0
                });
            }
            targetCounts.get(groupKey).count++;
        }
    }
    
    // Set TargetValueForAggregation: only first lead in each group gets the target value
    for (const lead of leadsProcessed) {
        if (lead.TargetId !== -1) {
            const groupKey = `${lead.Product || 'null'}_${lead.SaleArea || 'null'}_${lead.TargetId}`;
            const targetInfo = targetCounts.get(groupKey);
            
            if (targetInfo && leadsProcessed.indexOf(lead) === targetInfo.firstLeadIndex) {
                // This is the first lead in this group, so it gets the full target value
                lead.TargetValueForAggregation = lead.TargetValue;
            } else {
                // This is not the first lead in this group, so it gets 0 to avoid double-counting
                lead.TargetValueForAggregation = 0;
            }
        } else {
            lead.TargetValueForAggregation = 0;
        }
    }

    console.log("Processed leads with targets:", leadsProcessed);
    return leadsProcessed;
}

async function getPivotLeadsData() {
    return new Promise((resolve) => {
        getLeads((err,data) => {
            if (err) {
                console.error("Failed to fetch leads:", err);
                xalert("Failed to fetch leads:" + err, 1, null);
                reject(err);
                return;
            }
            resolve(data);
        });
    });
}

async function PivotLeads(){
    try {
        let data = await getPivotLeadsData();
        let processedData = await LeadProcessing(data);
        pivot.updateData({ data: processedData });
        pivot.setReport({
            formats: [{
                name: "",
                maxDecimalPlaces: 2,
                currencySymbol: "",
                thousandsSeparator: ",",
                }],
            dataSource: {
                data: processedData
            },
            slice: {
                rows: [
                    { uniqueName: "Product" },
                    { uniqueName: "SaleArea" },
                    { uniqueName: "MainCustomer" }
                ],
                columns: [
                    { uniqueName: "[Measures]" },
                    { uniqueName: "TargetName" },
                    { uniqueName: "Pipeline" }
                ],
                measures: [
                    {
                        uniqueName: "AchivedRevenue", 
                        aggregation: "sum",
                        caption: "Achieved"
                    },
                    {
                        uniqueName: "TargetValueForAggregation",
                        aggregation: "sum",
                        caption: "Target"
                    },
                    {
                        uniqueName: "AchievedPercent",
                        formula: "(sum(\"AchivedRevenue\")*100) / sum(\"TargetValueForAggregation\")",
                        caption: "Achieved %",
                        format: "decimal2"
                    }
                ],
                reportFilters: [
                    { uniqueName: "Pipeline" },
                    { uniqueName: "ExpectedYearMonth" },
                    { uniqueName: "TargetName" },
                    { uniqueName: "isCollected" },
                    { uniqueName: "isPO" }
                ]
            },
            options: {
                grid: {
                    type: "classic"
                }
            },
            tableSizes: {
                columns: [
                    {
                        tuple: [],
                        measure: {
                            uniqueName: "AchivedRevenue", 
                            aggregation: "sum"
                        },
                        width: 75
                    },
                    {
                        tuple: [],
                        measure: {
                            uniqueName: "TargetValueForAggregation",
                            aggregation: "sum"
                        },
                        width: 75
                    },
                    {
                        tuple: [],
                        measure: {
                            uniqueName: "AchievedPercent"
                        },
                        width: 85
                    }
                ]
            }
        });
        console.log(processedData);
        
        // Update stats display if available
        if (typeof updateStats === 'function') {
            updateStats(processedData);
        }
        
        // Hide loader
        const loader = document.getElementById('loader');
        if (loader) loader.classList.add('hidden');
        
    } catch (error) {
        console.error("Error processing leads:", error);
        // Hide loader even on error
        const loader = document.getElementById('loader');
        if (loader) loader.classList.add('hidden');
    }

}

//Default Load
(async () => {
    await PivotLeads();
})();








//TO BE Implemented

// New function for Pivot Events
async function PivotEvents() {
    try {
        let data = await getPivotEventsData(); // New function to fetch Events data
        let processedData = await EventProcessing(data); // New function to process Events data
        pivot.updateData({ data: processedData });
        pivot.setReport({
            dataSource: {
                data: processedData
            },
            slice: {
                rows: [
                    { uniqueName: "EventName" }, // Example field for events
                    { uniqueName: "Location" } // Example field for events
                ],
                columns: [
                    { uniqueName: "[Measures]" },
                    { uniqueName: "EventDate.Year" }, // Example date field
                    { uniqueName: "EventDate.Month" }
                ],
                measures: [
                    {
                        uniqueName: "Attendance", // Example measure for events
                        aggregation: "sum"
                    }
                ],
                reportFilters: [
                    { uniqueName: "EventType" } // Example filter for events
                ]
            }
        });
        console.log("Processed Events Data:", processedData);
    } catch (error) {
        console.error("Error processing Pivot Events:", error);
        alert("Error processing Pivot Events: " + error);
    }
}

// New function for Pivot HelpDesk
async function PivotHelpDesk() {
    try {
        let data = await getPivotHelpDeskData(); // New function to fetch HelpDesk data
        let processedData = await HelpDeskProcessing(data); // New function to process HelpDesk data
        pivot.updateData({ data: processedData });
        pivot.setReport({
            dataSource: {
                data: processedData
            },
            slice: {
                rows: [
                    { uniqueName: "IssueType" }, // Example field for helpdesk issues
                    { uniqueName: "Priority" } // Example field for helpdesk
                ],
                columns: [
                    { uniqueName: "[Measures]" },
                    { uniqueName: "CreatedDate.Year" }, // Example date field
                    { uniqueName: "CreatedDate.Month" }
                ],
                measures: [
                    {
                        uniqueName: "TicketCount", // Example measure for helpdesk
                        aggregation: "sum"
                    }
                ],
                reportFilters: [
                    { uniqueName: "Department" } // Example filter for helpdesk
                ]
            }
        });
        console.log("Processed HelpDesk Data:", processedData);
    } catch (error) {
        console.error("Error processing Pivot HelpDesk:", error);
        alert("Error processing Pivot HelpDesk: " + error);
    }
}

// New function to fetch Pivot Events data
async function getPivotEventsData() {
    return new Promise((resolve, reject) => {
        getEvents((err, data) => { // Replace with your actual Events API call
            if (err) {
                console.error("Failed to fetch events:", err);
                xalert("Failed to fetch events: " + err, 1, null);
                reject(err);
                return;
            }
            resolve(data);
        });
    });
}

// New function to fetch Pivot HelpDesk data
async function getPivotHelpDeskData() {
    return new Promise((resolve, reject) => {
        getTickets((err, data) => { // Replace with your actual HelpDesk API call
            if (err) {
                console.error("Failed to fetch helpdesk data:", err);
                xalert("Failed to fetch helpdesk data: " + err, 1, null);
                reject(err);
                return;
            }
            resolve(data);
        });
    });
}

// Placeholder for EventProcessing (implement based on your data structure)
async function EventProcessing(events) {
    let processedEvents = [];
    for (const event of events) {
        let processedEvent = {
            EventName: event.Name || "Unknown Event",
            Location: event.Location || "Unknown Location",
            EventDate: event.Date || new Date(),
            Attendance: event.Attendance || 0,
            EventType: event.Type || "Unknown"
        };
        processedEvents.push(processedEvent);
    }
    console.log("Processed Events:", processedEvents);
    console.log("Raw Events:", events);
    return processedEvents;
}

// Placeholder for HelpDeskProcessing (implement based on your data structure)
async function HelpDeskProcessing(tickets) {
    let processedTickets = [];
    for (const ticket of tickets) {
        let processedTicket = {
            IssueType: ticket.Issue || "Unknown Issue",
            Priority: ticket.Priority || "Low",
            CreatedDate: ticket.Created || new Date(),
            TicketCount: 1, // Assuming each ticket counts as 1 for aggregation
            Department: ticket.Department || "Unknown"
        };
        processedTickets.push(processedTicket);
    }
    console.log("Processed HelpDesk Tickets:", processedTickets);
    return processedTickets;
}

// Keep pivot height in sync with viewport
window.addEventListener('resize', function() {
    var h = getPivotHeight();
    if (pivot && pivot.setSize) {
        pivot.setSize({ height: h });
    }
});

