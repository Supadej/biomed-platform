const leadTable = $("#leadTable");
function tableView() {
    const pipelineContainer = document.getElementById('pipelineContainer');
    const tableContainer = document.getElementById('tableContainer');

    if (pipelineContainer && tableContainer) {
        pipelineContainer.classList.add('d-none');
        tableContainer.classList.remove('d-none');
    }
}

function cardView() {
    const pipelineContainer = document.getElementById('pipelineContainer');
    const tableContainer = document.getElementById('tableContainer');

    if (pipelineContainer && tableContainer) {
        pipelineContainer.classList.remove('d-none');
        tableContainer.classList.add('d-none');
    }
}


function loadLeads(leads){
    const filteredLeads = leads.map(lead => ({
        Id: lead.Id,
        LeadName: lead.LeadName,
        CRMPipelineId: lead.CRMPipelineId,
        MainCustomerId: lead.MainCustomerId,
        MainUserId: lead.MainUserId,
        SaleAreaId: lead.SaleAreaId,
        ProductId: lead.ProductId,
        Creation: lead.Creation,
        LastUpdated: lead.LastUpdated,
        Expected: lead.Expected,
        ExpectedRevenue: lead.ExpectedRevenue,
        AchivedRevenue: lead.AchivedRevenue,
        PaymentDue: lead.PaymentDue,
        CustomerNeeds: lead.CustomerNeeds,
        Budget: lead.Budget,
        FundingSource: lead.FundingSource,
        ProjectID: lead.ProjectID,
        KeyDecisionMaker: lead.KeyDecisionMaker,
        KeySellingPoints: lead.KeySellingPoints,
        CompetitorInfo: lead.CompetitorInfo,
        AdditionalInfo: lead.AdditionalInfo,
        IsPO: lead.IsPO,
        IsCollected: lead.IsCollected,
        Other: lead.Other
    }));
    leadTable.bootstrapTable('load', filteredLeads);
}
var UsersDummy = [];
getUsers((err, users) => {
  if (err) {
    console.error("Failed to fetch users:", err);
    xalert("Failed to fetch users:" + err, 1, null);
    return;
  }
  UsersDummy = users;
}, false);

function userFormatter(value, row, index) {
  var user = UsersDummy.find(function (c) {
    return c.Id === value;
  });
  return user
    ? user.FirstName + " " + user.LastName + "(" + user.Position + ")"
    : "Unknown User";
}

var ProductsDummy = [];
getProducts((err, products) => {
  if (err) {
    console.error("Failed to fetch products:", err);
    xalert("Failed to fetch products:" + err, 1, null);
    return;
  }
  ProductsDummy = products;
});

function productFormatter(value, row, index) {
  if (value === null || value === undefined) {
    return "Unassigned";
  }
  var product = ProductsDummy.find(function (c) {
    return c.Id === value;
  });
  return product ? product.Name : "Unknown Product";
}

var ContactDummy = [];
getContacts((err, contacts) => {
    if (err) {
      console.error("Failed to fetch products:", err);
      xalert("Failed to fetch products:" + err, 1, null);
      return;
    }
    ContactDummy = contacts;
});

function customerFormatter(value, row, index) {
    if (value === null || value === undefined) {
      return "Unassigned";
    }
    var product = ContactDummy.find(function (c) {
      return c.Id === value;
    });
    return product ? product.Name : "Unknown Custommer";
}
var PipelineDummy = [];
getPipelines((err, pipelines) => {
    if (err) {
      console.error("Failed to fetch pipelines:", err);
      xalert("Failed to fetch pipelines:" + err, 1, null);
      return;
    }
    PipelineDummy = pipelines;
});
function pipelineFormatter(value, row, index) {
    if (value === null || value === undefined) {
      return "Unassigned";
    }
    var pipeline = PipelineDummy.find(function (c) {
      return c.Id === value;
    });
    return pipeline ? pipeline.PipelineName : "Unknown Pipeline";
}
var SaleAreaDummy = [];
getSaleAreas((err, saleAreas) => {
    if (err) {
      console.error("Failed to fetch sale areas:", err);
      xalert("Failed to fetch sale areas:" + err, 1, null);
      return;
    }
    SaleAreaDummy = saleAreas;
});
function saleAreaFormatter(value, row, index) {
    if (value === null || value === undefined) {
      return "Unassigned";
    }
    var saleArea = SaleAreaDummy.find(function (c) {
      return c.Id === value;
    });
    return saleArea ? saleArea.Name : "Unknown Sale Area";
}





function tableTimeFormatter(value, row, index){
    return formatDateTime(value);
}

function operateFormatter(value, row, index) {

    return [
      '<a class="edit text-primary link link-underline link-underline-opacity-0" href="crm-detail.html?leadid='+row.Id +'" title="Edit">',
      '<i class="fi fi-rr-edit"></i>',
      "</a>  ",
    ].join("");
  }

  var operateEvents = {
    'click .edit': test
};

function test(){

};

