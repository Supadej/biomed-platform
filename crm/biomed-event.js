/**
 * Event Calendar JavaScript - daisyUI Version
 * Biomed ERP 2.0
 */

// ================================
// Logging Helper
// ================================
function log(module, level, message, data = null) {
  const timestamp = new Date().toISOString();
  const prefix = `[${timestamp}] [${module}] [${level}]`;
  if (data) {
    console.log(prefix, message, data);
  } else {
    console.log(prefix, message);
  }
}

// ================================
// Global Variables
// ================================
let ec = null; // Event Calendar instance
let currentEventId = null;
let currentEventsData = [];
let currentInfo = null; // Store info for revert on cancel
let currentMainUserID = null; // Store MainUserID when loading modal
let miniCalendarDate = new Date();
let selectedMiniDate = new Date();

// MultiSelect instances
let usersFilterMS = null;
let contactsFilterMS = null;
let productsFilterMS = null;
let eventUsersMS = null;
let eventContactsMS = null;
let eventProductsMS = null;

// User color cache
const userColorCache = new Map();

// ================================
// Initialization
// ================================
window.onload = async function () {
  console.log("Event: Page loading started");

  try {
    showLoading();

    // Check URL parameters
    const urlParams = new URLSearchParams(window.location.search);
    const eventIdFromUrl = urlParams.get("id") || urlParams.get("eventId");

    // Initialize filters
    await initializeFilters();

    // Initialize calendar
    initializeCalendar();

    // Initialize mini calendar for mobile
    renderMiniCalendar();

    // Load events
    await queryEvents();

    // Show today's events in mobile day list
    const todayStr = new Date().toISOString().split("T")[0];
    renderDayList(todayStr);

    // Update alert bar
    updateAlertBar("success", `โหลดข้อมูลเรียบร้อย`);

    // Open event from URL if specified
    if (eventIdFromUrl) {
      log("Event", "INFO", `Opening event from URL: ${eventIdFromUrl}`);
      await openEventModal(eventIdFromUrl);
    }

    hideLoading();
    log("Event", "INFO", "Page loaded successfully");
  } catch (error) {
    log("Event", "ERROR", "Failed to initialize page", {
      error: error.message,
    });
    updateAlertBar("error", `เกิดข้อผิดพลาด: ${error.message}`);
    hideLoading();
  }
};

// ================================
// Filter Initialization
// ================================
async function initializeFilters() {
  log("Event", "INFO", "Initializing filters");

  try {
    const [users, contacts, products] = await Promise.all([
      promiseUsers(),
      promiseContacts(),
      promiseProducts(),
    ]);

    // Cache user colors
    for (const user of users) {
      const color = await promiseColorById(user.Id);
      userColorCache.set(user.Id, color);
    }

    // Prepare user options (filter disabled users)
    const userOptions = users
      .filter((u) => u.Enabled !== false)
      .sort((a, b) => a.FirstName.localeCompare(b.FirstName))
      .map((u) => ({
        value: u.Id,
        label: `${u.FirstName} ${u.LastName}`,
      }));

    // Prepare contact options
    const contactOptions = contacts
      .sort((a, b) => (a.Name || "").localeCompare(b.Name || ""))
      .map((c) => ({
        value: c.Id,
        label: c.Name || "Unknown",
      }));

    // Prepare product options
    const productOptions = products
      .sort((a, b) => (a.Name || "").localeCompare(b.Name || ""))
      .map((p) => ({
        value: p.Id,
        label: p.Name || "Unknown",
      }));

    // Initialize dropdown filter MultiSelects
    usersFilterMS = new MultiSelect("usersFilterPanelContainer", {
      options: userOptions,
      placeholder: "เลือกผู้รับผิดชอบ...",
      badgeClass: "badge-primary",
      searchable: true,
      showSelectAll: true,
      maxDisplay: 2,
      text: {
        search: "ค้นหา...",
        selectAll: "เลือกทั้งหมด",
        clearAll: "ล้างทั้งหมด",
        noResults: "ไม่พบข้อมูล",
      },
    });

    contactsFilterMS = new MultiSelect("contactsFilterPanelContainer", {
      options: contactOptions,
      placeholder: "เลือกผู้ติดต่อ...",
      badgeClass: "badge-secondary",
      searchable: true,
      showSelectAll: true,
      maxDisplay: 2,
    });

    productsFilterMS = new MultiSelect("productsFilterPanelContainer", {
      options: productOptions,
      placeholder: "เลือกสินค้า...",
      badgeClass: "badge-accent",
      searchable: true,
      showSelectAll: true,
      maxDisplay: 2,
    });

    log("Event", "INFO", "Filters initialized", {
      users: userOptions.length,
      contacts: contactOptions.length,
      products: productOptions.length,
    });
  } catch (error) {
    log("Event", "ERROR", "Failed to initialize filters", {
      error: error.message,
    });
    throw error;
  }
}

// ================================
// Calendar Initialization
// ================================
function initializeCalendar() {
  log("Event", "INFO", "Initializing Event Calendar");

  const calendarEl = document.getElementById("ec");
  if (!calendarEl) {
    log("Event", "ERROR", "Calendar container not found");
    return;
  }

  ec = new EventCalendar(calendarEl, {
    view: "dayGridMonth",
    headerToolbar: {
      start: "title",
      center: "",
      end: "prev,next",
    },
    buttonText: {
      dayGridMonth: "เดือน",
    },
    displayEventTime: false,
    selectable: true,
    selectLongPressDelay: 1000,

    // Event handlers
    select: function (info) {
      log("Event", "DEBUG", "Date selected", { date: info.startStr });
      openEventModal(null, info);
    },

    dateClick: function (info) {
      log("Event", "DEBUG", "Date clicked", { date: info.dateStr });
      openEventModal(null, info);
    },

    eventClick: function (info) {
      log("Event", "DEBUG", "Event clicked", { id: info.event.id });
      openEventModal(info.event.id, info);
    },

    eventDrop: function (info) {
      log("Event", "DEBUG", "Event dropped", { id: info.event.id });
      openEventModal(info.event.id, info);
    },

    eventResize: function (info) {
      log("Event", "DEBUG", "Event resized", { id: info.event.id });
      openEventModal(info.event.id, info);
    },

    eventMouseEnter: function (info) {
      showEventTooltip(info);
    },

    eventMouseLeave: function () {
      hideEventTooltip();
    },

    events: [],
  });

  // Bind navigation events
  bindCalendarNavEvents();

  log("Event", "INFO", "Event Calendar initialized");
}

function bindCalendarNavEvents() {
  const prevBtn = document.querySelector(".ec-prev");
  const nextBtn = document.querySelector(".ec-next");

  if (prevBtn) {
    prevBtn.addEventListener("click", () => {
      queryEvents();
    });
  }

  if (nextBtn) {
    nextBtn.addEventListener("click", () => {
      queryEvents();
    });
  }

  // Bind view change buttons
  document.querySelectorAll(".ec-center button").forEach((button) => {
    button.addEventListener("click", () => {
      queryEvents();
    });
  });
}

// ================================
// Event Tooltip
// ================================
function showEventTooltip(info) {
  hideEventTooltip();

  const event = info.event.extendedProps?.event;
  if (!event) return;

  const color = info.event.extendedProps?.color;
  const attendees = info.event.extendedProps?.attendees || [];
  const subAttendees = info.event.extendedProps?.subAttendees || [];
  const subColors = info.event.extendedProps?.subAttendeeColor || [];

  const tooltip = document.createElement("div");
  tooltip.className = "ec-popup";
  tooltip.innerHTML = `
<div class="p-4 bg-base-100 rounded-lg">
<h6 class="font-bold text-base mb-2 truncate">
<i class="fas fa-calendar-alt text-primary mr-2"></i>${
    event.Title || "Untitled"
  }
</h6>
<div class="text-xs text-base-content/60 mb-2">
${
  event.IsAllDay
    ? '<i class="fas fa-sun mr-1"></i> ทั้งวัน'
    : `<i class="fas fa-clock mr-1"></i> ${formatDateTime(
        event.StartDate
      )} - ${formatDateTime(event.EndDate)}`
}
</div>
${
  event.Plan
    ? `<p class="text-sm text-base-content/80 mb-2 line-clamp-3">${event.Plan}</p>`
    : ""
}
<div class="flex flex-wrap gap-1">
${
  attendees[0]
    ? `
<span class="badge badge-sm gap-1" style="background-color: ${
        color?.color?.code || "#666"
      }; color: ${color?.textColor || "#fff"}">
<i class="fas fa-user"></i> ${attendees[0]}
</span>
`
    : ""
}
</div>
${
  subAttendees.length > 0
    ? `
<div class="flex flex-wrap gap-1 mt-2">
${subAttendees
  .slice(0, 3)
  .map(
    (name, i) => `
<span class="badge badge-sm badge-outline" style="border-color: ${
      subColors[i] || "#666"
    }; color: ${subColors[i] || "#666"}">
${name}
</span>
`
  )
  .join("")}
${
  subAttendees.length > 3
    ? `<span class="badge badge-sm badge-ghost">+${
        subAttendees.length - 3
      }</span>`
    : ""
}
</div>
`
    : ""
}
</div>
`;

  document.body.appendChild(tooltip);

  // Position tooltip
  const rect = info.el.getBoundingClientRect();
  const tooltipRect = tooltip.getBoundingClientRect();

  let left =
    rect.left + window.scrollX + rect.width / 2 - tooltipRect.width / 2;
  let top = rect.top + window.scrollY - tooltipRect.height - 8;

  // Adjust for screen bounds
  if (left < 8) left = 8;
  if (left + tooltipRect.width > window.innerWidth - 8) {
    left = window.innerWidth - tooltipRect.width - 8;
  }
  if (top < 8) {
    top = rect.bottom + window.scrollY + 8;
  }

  tooltip.style.position = "absolute";
  tooltip.style.left = `${left}px`;
  tooltip.style.top = `${top}px`;
  tooltip.style.zIndex = "1000";
}

function hideEventTooltip() {
  document.querySelectorAll(".ec-popup").forEach((el) => el.remove());
}

// ================================
// Query & Filter Events
// ================================
async function getFilter() {
  const filter = {
    Title: document.getElementById("queryTitlePanel")?.value || null,
    UserIDs: usersFilterMS?.getValues() || [],
    ContactIDs: contactsFilterMS?.getValues() || [],
    ProductIDs: productsFilterMS?.getValues() || [],
    OnlyMainResponsible:
      document.getElementById("onlyMainResponsiblePanel")?.checked || false,
  };

  // Clean up empty arrays
  if (filter.UserIDs.length === 0) filter.UserIDs = null;
  if (filter.ContactIDs.length === 0) filter.ContactIDs = null;
  if (filter.ProductIDs.length === 0) filter.ProductIDs = null;
  if (!filter.Title) filter.Title = null;

  return filter;
}

async function querySearch() {
  log("Event", "INFO", "Query search triggered");
  showLoading();
  await queryEvents();
  
  // Check if we're on stats tab - refresh statistics
  const statsView = document.getElementById("statsView");
  if (statsView && !statsView.classList.contains("hidden")) {
    await renderEventStatistics();
  }
  
  // Check if we're on table tab - refresh table
  const tableView = document.getElementById("tableView");
  if (tableView && !tableView.classList.contains("hidden")) {
    await populateEventsTable();
  }
  
  hideLoading();
  showToast("success", "ค้นหาเรียบร้อย");
}

async function queryEvents(clear = true, deepDetails = false) {
  log("Event", "INFO", "Querying events");

  try {
    const filter = await getFilter();

    // Check if we're on Stats or Table tab and have date filter values
    const filterStartDate = document.getElementById("filterStartDate")?.value;
    const filterEndDate = document.getElementById("filterEndDate")?.value;
    const statsView = document.getElementById("statsView");
    const tableViewEl = document.getElementById("tableView");
    const isStatsTab = statsView && !statsView.classList.contains("hidden");
    const isTableTab = tableViewEl && !tableViewEl.classList.contains("hidden");
    
    if ((isStatsTab || isTableTab) && (filterStartDate || filterEndDate)) {
      // Use date filter from Control Panel for Statistics/Table view
      if (filterStartDate) {
        filter.StartDate = formatDateForApi(new Date(filterStartDate));
      } else {
        // Default to 1 year ago if no start date
        const yearAgo = new Date();
        yearAgo.setFullYear(yearAgo.getFullYear() - 1);
        filter.StartDate = formatDateForApi(yearAgo);
      }
      
      if (filterEndDate) {
        filter.EndDate = formatDateForApi(new Date(filterEndDate));
      } else {
        // Default to 1 year from now if no end date
        const yearLater = new Date();
        yearLater.setFullYear(yearLater.getFullYear() + 1);
        filter.EndDate = formatDateForApi(yearLater);
      }
    } else if (ec) {
      // Get calendar view date range
      const view = ec.getView();
      filter.StartDate = formatDateForApi(view.activeStart);
      filter.EndDate = formatDateForApi(view.activeEnd);
    } else {
      // Fallback to current month
      const now = new Date();
      const start = new Date(now.getFullYear(), now.getMonth(), 1);
      const end = new Date(now.getFullYear(), now.getMonth() + 1, 0);
      filter.StartDate = formatDateForApi(start);
      filter.EndDate = formatDateForApi(end);
    }

    filter.DeepSearch = true;
    filter.DeepDetails = deepDetails;

    // Clear existing events
    if (clear && ec) {
      const events = ec.getEvents();
      events.forEach((event) => ec.removeEventById(event.id));
    }

    // Fetch events
    const events = await v2_promiseEvents(filter);
    log("Event", "DEBUG", `Fetched ${events.length} events`);
    console.log("[Event] Loaded Events Data:", events);

    // Filter by main responsible if needed
    let filteredEvents = events;
    if (
      filter.OnlyMainResponsible &&
      filter.UserIDs &&
      filter.UserIDs.length > 0
    ) {
      // Convert UserIDs to integers for comparison
      const userIdsAsInts = filter.UserIDs.map(id => parseInt(id));
      filteredEvents = events.filter((e) =>
        userIdsAsInts.includes(e.MainUserID)
      );
    }

    // Store for table view
    currentEventsData = filteredEvents;

    // Map events for calendar
    const calendarEvents = await Promise.all(
      filteredEvents.map(async (event) => {
        return await mapEventForCalendar(event);
      })
    );

    // Add events to calendar
    if (ec) {
      calendarEvents.forEach((event) => ec.addEvent(event));
    }

    // Update filter count badge
    updateFilterCount();

    // Update mini calendar
    renderMiniCalendar();

    log("Event", "INFO", `Loaded ${calendarEvents.length} events to calendar`);
  } catch (error) {
    log("Event", "ERROR", "Failed to query events", { error: error.message });
    throw error;
  }
}

async function mapEventForCalendar(event) {
  const color =
    userColorCache.get(event.MainUserID) ||
    (await promiseColorById(event.MainUserID));
  const mainUser = await promiseUserById(event.MainUserID);
  const mainUserName = mainUser
    ? `${mainUser.FirstName} ${mainUser.LastName}`
    : "Unknown";

  // Get sub attendees
  const subAttendeeNames = [];
  const subAttendeeColors = [];

  for (const userId of event.Users || []) {
    const user = await promiseUserById(userId);
    if (user) {
      subAttendeeNames.push(`${user.FirstName} ${user.LastName}`);
      const userColor =
        userColorCache.get(userId) || (await promiseColorById(userId));
      subAttendeeColors.push(userColor?.color?.code || "#666");
    }
  }

  const startDate = event.StartDate.split("T")[0];
  const endDate = event.EndDate.split("T")[0];
  const isMultiDay = startDate !== endDate;
  const start = event.IsAllDay ? startDate : event.StartDate;
  const end = event.IsAllDay ? endDate : event.EndDate;

  // Build title HTML
  let titleHtml;
  if (event.IsAllDay || isMultiDay) {
    const days = isMultiDay
      ? Math.ceil(
          (new Date(endDate) - new Date(startDate)) / (1000 * 60 * 60 * 24)
        ) + 1
      : 1;
    titleHtml = `
<div class="flex items-center gap-1 px-2 py-1 rounded-md text-xs font-medium truncate" 
 style="background-color: ${color?.color?.code || "#666"}; color: ${
      color?.textColor || "#fff"
    }">
${
  isMultiDay
    ? `<i class="fas fa-calendar-week text-[10px]"></i> ${days}d `
    : '<i class="fas fa-sun text-[10px]"></i> '
}
${event.Title || "Untitled"}
</div>
`;
  } else {
    titleHtml = `
<div class="flex items-center gap-1 px-2 py-1 rounded-md text-xs bg-base-100 truncate">
<span style="color: ${color?.color?.code || "#666"}">●</span>
<span class="text-base-content/60">${formatTimeOnly(start)}</span>
${event.Title || "Untitled"}
</div>
`;
  }

  return {
    id: event.Id,
    resourceIds: [event.MainUserID],
    allDay: event.IsAllDay,
    start: new Date(start),
    end: new Date(end),
    title: titleHtml,
    display: "auto",
    backgroundColor: "transparent",
    textColor: "black",
    extendedProps: {
      plan: event.Plan,
      attendees: [mainUserName],
      subAttendees: subAttendeeNames,
      subAttendeeColor: subAttendeeColors,
      event: event,
      color: color,
    },
  };
}

function clearFilters() {
  document.getElementById("queryTitlePanel").value = "";
  document.getElementById("onlyMainResponsiblePanel").checked = false;

  if (usersFilterMS) usersFilterMS.clearAll();
  if (contactsFilterMS) contactsFilterMS.clearAll();
  if (productsFilterMS) productsFilterMS.clearAll();

  updateFilterCount();
  showToast("info", "ล้างตัวกรองแล้ว");
}

function updateFilterCount() {
  let count = 0;

  if (document.getElementById("queryTitlePanel")?.value) count++;
  if (usersFilterMS?.getValues()?.length > 0) count++;
  if (contactsFilterMS?.getValues()?.length > 0) count++;
  if (productsFilterMS?.getValues()?.length > 0) count++;
  if (document.getElementById("onlyMainResponsiblePanel")?.checked) count++;

  const badge = document.getElementById("filterCount");
  if (badge) {
    badge.textContent = count;
    badge.classList.toggle("hidden", count === 0);
  }
}

// ================================
// View Toggle
// ================================
function toggleViewMode(mode) {
  const calendarBtn = document.getElementById("calendarViewBtn");
  const tableBtn = document.getElementById("tableViewBtn");
  const vizBtn = document.getElementById("vizViewBtn");
  const calendarView = document.getElementById("calendarView");
  const tableView = document.getElementById("tableView");
  const statsView = document.getElementById("statsView");
  const dateRangeFilter = document.getElementById("dateRangeFilter");

  // Remove active from all buttons
  calendarBtn?.classList.remove("btn-active");
  tableBtn?.classList.remove("btn-active");
  vizBtn?.classList.remove("btn-active");

  // Hide all views
  calendarView?.classList.add("hidden");
  tableView?.classList.add("hidden");
  statsView?.classList.add("hidden");

  if (mode === "calendar") {
    calendarBtn?.classList.add("btn-active");
    calendarView?.classList.remove("hidden");
    dateRangeFilter?.classList.add("hidden");
  } else if (mode === "table") {
    tableBtn?.classList.add("btn-active");
    tableView?.classList.remove("hidden");
    dateRangeFilter?.classList.remove("hidden");
    populateEventsTable();
  } else if (mode === "stats") {
    vizBtn?.classList.add("btn-active");
    statsView?.classList.remove("hidden");
    dateRangeFilter?.classList.remove("hidden");
    renderEventStatistics();
  }
}

function switchTab(tab) {
  // Redirect to toggleViewMode for consistency
  toggleViewMode(tab);
}

// ================================
// Table View
// ================================
async function populateEventsTable() {
  const tableBody = document.getElementById("eventsTableBody");
  if (!tableBody) return;

  tableBody.innerHTML = "";

  if (currentEventsData.length === 0) {
    tableBody.innerHTML = `
<tr>
<td colspan="10" class="text-center py-8 text-base-content/50">
<i class="fas fa-calendar-times text-4xl mb-2"></i>
<p>ไม่พบ Event</p>
</td>
</tr>
`;
    return;
  }

  for (const event of currentEventsData) {
    const mainUser = await promiseUserById(event.MainUserID);
    const mainUserName = mainUser
      ? `${mainUser.FirstName} ${mainUser.LastName}`
      : "Unknown";
    const color = userColorCache.get(event.MainUserID);

    // Get attendees count
    const attendeesCount = event.Users?.length || 0;

    // Use same status logic as Viz
    const eventStatus = getEventStatus(event);

    const row = document.createElement("tr");
    row.className = "hover cursor-pointer";
    row.onclick = () => openEventModal(event.Id);

    // Plan/Report content
    const planContent = event.Plan && event.Plan.trim() ? event.Plan : '-';
    const reportContent = event.Report && event.Report.trim() ? event.Report : '-';
    
    // Get product names from EventProducts
    let productNames = '-';
    try {
      if (event.EventProducts && event.EventProducts.length > 0) {
        const products = await promiseProducts();
        console.log('[Event Table] EventProducts:', event.EventProducts);
        console.log('[Event Table] Products cache:', products?.length);
        
        const productNameList = event.EventProducts
          .map(ep => {
            // Handle both ep.ProductId and ep (if it's just the ID)
            const productId = ep.ProductId || ep;
            const product = products.find(p => p.Id == productId); // Use == for type coercion
            console.log('[Event Table] Looking for productId:', productId, 'Found:', product?.Name);
            return product ? product.Name : null;
          })
          .filter(name => name !== null);
        productNames = productNameList.length > 0 ? productNameList.join(', ') : '-';
      }
    } catch (err) {
      console.error('[Event Table] Error getting product names:', err);
    }

    row.innerHTML = `
<td class="font-medium whitespace-nowrap">${event.Title || "Untitled"}</td>
<td class="whitespace-nowrap">
<div>${formatDateThai(event.StartDate)}</div>
<div class="text-xs text-base-content/50">${
      event.IsAllDay ? "ทั้งวัน" : formatTimeOnly(event.StartDate)
    }</div>
</td>
<td class="whitespace-nowrap">
<div>${formatDateThai(event.EndDate)}</div>
<div class="text-xs text-base-content/50">${
      event.IsAllDay ? "ทั้งวัน" : formatTimeOnly(event.EndDate)
    }</div>
</td>
<td class="whitespace-nowrap">
<div class="flex items-center gap-2">
<span class="w-3 h-3 rounded-full" style="background-color: ${
      color?.color?.code || "#666"
    }"></span>
${mainUserName}
</div>
</td>
<td class="whitespace-nowrap">
${
  attendeesCount > 0
    ? `<span class="badge badge-sm">${attendeesCount} คน</span>`
    : '<span class="text-base-content/30">-</span>'
}
</td>
<td class="whitespace-nowrap">
<div class="text-sm">${productNames}</div>
</td>
<td class="min-w-[200px] max-w-[300px]">
<div class="text-sm whitespace-pre-wrap">${planContent}</div>
</td>
<td class="min-w-[200px] max-w-[300px]">
<div class="text-sm whitespace-pre-wrap">${reportContent}</div>
</td>
<td class="whitespace-nowrap"><span class="badge badge-sm ${eventStatus.badgeClass}">${eventStatus.label}</span></td>
<td class="whitespace-nowrap">
<button class="btn btn-ghost btn-xs" onclick="event.stopPropagation(); openEventModal(${
      event.Id
    })">
<i class="fas fa-edit"></i>
</button>
</td>
`;

    tableBody.appendChild(row);
  }
}

// ================================
// Mini Calendar (Mobile)
// ================================
function renderMiniCalendar() {
  const container = document.getElementById("miniCalendarDays");
  const titleEl = document.getElementById("miniCalendarTitle");

  if (!container) return;

  const year = miniCalendarDate.getFullYear();
  const month = miniCalendarDate.getMonth();

  // Update title
  const monthNames = [
    "มกราคม",
    "กุมภาพันธ์",
    "มีนาคม",
    "เมษายน",
    "พฤษภาคม",
    "มิถุนายน",
    "กรกฎาคม",
    "สิงหาคม",
    "กันยายน",
    "ตุลาคม",
    "พฤศจิกายน",
    "ธันวาคม",
  ];
  if (titleEl) {
    titleEl.textContent = `${monthNames[month]} ${year + 543}`;
  }

  // Get first day of month and total days
  const firstDay = new Date(year, month, 1).getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const daysInPrevMonth = new Date(year, month, 0).getDate();

  // Get today
  const today = new Date();
  const isCurrentMonth =
    today.getFullYear() === year && today.getMonth() === month;

  // Get events for this month
  const monthEvents = currentEventsData.filter((e) => {
    const eventDate = new Date(e.StartDate);
    return eventDate.getFullYear() === year && eventDate.getMonth() === month;
  });

  console.log(
    "Mini calendar - Events this month:",
    monthEvents.length,
    monthEvents
  );

  // Build calendar grid
  let html = "";
  let dayCount = 1;
  let nextMonthDay = 1;

  for (let i = 0; i < 42; i++) {
    let dayNum,
      isOtherMonth = false;

    if (i < firstDay) {
      // Previous month
      dayNum = daysInPrevMonth - firstDay + i + 1;
      isOtherMonth = true;
    } else if (dayCount > daysInMonth) {
      // Next month
      dayNum = nextMonthDay++;
      isOtherMonth = true;
    } else {
      dayNum = dayCount++;
    }

    const isToday =
      isCurrentMonth && !isOtherMonth && dayNum === today.getDate();
    const isSelected =
      !isOtherMonth &&
      selectedMiniDate.getFullYear() === year &&
      selectedMiniDate.getMonth() === month &&
      selectedMiniDate.getDate() === dayNum;

    // Check if day has events
    const hasEvents =
      !isOtherMonth &&
      monthEvents.some((e) => {
        const eventDay = new Date(e.StartDate).getDate();
        return eventDay === dayNum;
      });

    const classes = [
      "mini-calendar-day",
      isOtherMonth ? "other-month" : "",
      isToday ? "today" : "",
      isSelected ? "selected" : "",
      hasEvents ? "has-events" : "",
    ]
      .filter(Boolean)
      .join(" ");

    const dateStr = isOtherMonth
      ? ""
      : `${year}-${String(month + 1).padStart(2, "0")}-${String(
          dayNum
        ).padStart(2, "0")}`;

    // Use inline dot indicator for events
    const dotIndicator = hasEvents ? '<span class="event-dot"></span>' : "";

    html += `
<div class="${classes}" 
 ${!isOtherMonth ? `onclick="selectMiniCalendarDate('${dateStr}')"` : ""}>
${dayNum}
${dotIndicator}
</div>
`;

    // Stop after 6 weeks if we've finished the month
    if (i >= 35 && dayCount > daysInMonth) break;
  }

  container.innerHTML = html;
}

function miniCalendarPrev() {
  miniCalendarDate.setMonth(miniCalendarDate.getMonth() - 1);
  renderMiniCalendar();
}

function miniCalendarNext() {
  miniCalendarDate.setMonth(miniCalendarDate.getMonth() + 1);
  renderMiniCalendar();
}

function selectMiniCalendarDate(dateStr) {
  selectedMiniDate = new Date(dateStr);
  renderMiniCalendar();
  renderDayList(dateStr);
}

function renderDayList(dateStr) {
  const container = document.getElementById("dayListContainer");
  const titleEl = document.getElementById("dayListTitle");

  if (!container) return;

  // Update title
  const date = new Date(dateStr);
  if (titleEl) {
    titleEl.textContent = formatDateThai(dateStr);
  }

  // Filter events for this day
  const dayEvents = currentEventsData.filter((e) => {
    const eventStart = e.StartDate.split("T")[0];
    const eventEnd = e.EndDate.split("T")[0];
    return dateStr >= eventStart && dateStr <= eventEnd;
  });

  if (dayEvents.length === 0) {
    container.innerHTML = `
<div class="text-center text-base-content/50 py-8">
<i class="fas fa-calendar-day text-4xl mb-2"></i>
<p>ไม่มี Event ในวันนี้</p>
</div>
`;
    return;
  }

  // Sort by start time
  dayEvents.sort((a, b) => new Date(a.StartDate) - new Date(b.StartDate));

  let html = "";
  for (const event of dayEvents) {
    const color = userColorCache.get(event.MainUserID);
    const mainUser = promiseUserById(event.MainUserID);
    const timeStr = event.IsAllDay
      ? "ทั้งวัน"
      : formatTimeOnly(event.StartDate);

    html += `
<div class="day-event-item" style="border-left-color: ${
      color?.color?.code || "#666"
    }" 
 onclick="openEventModal(${event.Id})">
<div class="day-event-content">
<div class="day-event-title">
<span class="day-event-dot" style="background-color: ${
      color?.color?.code || "#666"
    }"></span>
${timeStr} ${event.Title || "Untitled"}
</div>
<div class="day-event-plan text-sm opacity-70">
${
  event.Plan
    ? event.Plan.substring(0, 50) + (event.Plan.length > 50 ? "..." : "")
    : ""
}
</div>
</div>
</div>
`;
  }

  container.innerHTML = html;
}

// ================================
// Event Modal
// ================================
async function openEventModal(eventId = null, info = null) {
  log("Event", "INFO", `Opening event modal`, { eventId, hasInfo: !!info });

  currentEventId = eventId;
  currentInfo = info;

  // Update URL parameter with event ID
  updateEventUrlParam(eventId);

  const modal = document.getElementById("eventModal");
  if (!modal) return;

  showLoading();

  try {
    // Reset modal state
    resetModalState();

    // Get required data
    const [users, contacts, products, groups, myUser] = await Promise.all([
      promiseUsers(),
      promiseContacts(),
      promiseProducts(),
      promiseGroups(),
      promiseMyUser(),
    ]);

    let eventData = {};
    let mainUser = myUser;

    if (eventId) {
      // Edit mode
      eventData = await promiseEventById(eventId);
      mainUser = users.find((u) => u.Id === eventData.MainUserID) || myUser;
      // Store MainUserID from loaded event
      currentMainUserID = eventData.MainUserID;
      document.getElementById("modalTitle").textContent = "แก้ไข Event";
      document.getElementById("deleteEventBtn").classList.remove("hidden");
    } else {
      // Create mode
      eventData = createNewEventData(info, myUser);
      // For new events, use current user's ID
      currentMainUserID = myUser.Id;
      document.getElementById("modalTitle").textContent = "สร้าง Event ใหม่";
      document.getElementById("deleteEventBtn").classList.add("hidden");
    }

    // Setup main user badge
    await setupMainUserBadge(mainUser);

    // Setup group select
    await setupGroupSelect(groups);

    // Setup MultiSelects for modal
    await setupModalMultiSelects(
      users,
      contacts,
      products,
      eventData,
      mainUser
    );

    // Populate form fields
    populateEventForm(eventData, info);

    // Load logs
    if (eventId) {
      await loadEventLogs(eventId);
    }

    hideLoading();

    // Load binder state
    loadBinderState();

    // Add ESC key prevention listener
    modal.addEventListener("keydown", preventEscClose);

    modal.showModal();
  } catch (error) {
    log("Event", "ERROR", "Failed to open event modal", {
      error: error.message,
    });
    hideLoading();
    showToast("error", `ไม่สามารถเปิด Event ได้: ${error.message}`);
  }
}

function createNewEventData(info, myUser) {
  const now = new Date();
  let startDate, endDate, isAllDay;

  if (info?.dateStr) {
    // Clicked on a specific date
    startDate = `${info.dateStr.split("T")[0]}T09:00:00`;
    endDate = `${info.dateStr.split("T")[0]}T10:00:00`;
    isAllDay = false;
  } else if (info?.startStr) {
    // Selected a range
    startDate = `${info.startStr.split("T")[0]}T09:00:00`;
    const endDateObj = new Date(info.endStr);
    endDateObj.setDate(endDateObj.getDate() - 1);
    endDate = `${endDateObj.toISOString().split("T")[0]}T10:00:00`;
    isAllDay = true;
  } else {
    // No info, use today
    const dateStr = now.toISOString().split("T")[0];
    startDate = `${dateStr}T09:00:00`;
    endDate = `${dateStr}T10:00:00`;
    isAllDay = false;
  }

  return {
    Title: "",
    StartDate: startDate,
    EndDate: endDate,
    IsAllDay: isAllDay,
    Plan: "",
    Report: "",
    Comment: "",
    MainUserID: myUser.Id,
    EventUsers: [],
    EventContacts: [],
    EventProducts: [],
  };
}

function resetModalState() {
  // Reset delete confirmation
  document.getElementById("eventActionButtons")?.classList.remove("hidden");
  document.getElementById("deleteConfirmButtons")?.classList.add("hidden");

  // Reset log input
  hideLogInput();

  // Clear logs container
  const logsContainer = document.getElementById("logsContainer");
  if (logsContainer) {
    logsContainer.innerHTML = `
<div class="text-center text-base-content/50 py-8" id="logsPlaceholder">
<i class="fas fa-clipboard-list text-3xl mb-2"></i>
<p class="text-sm">ยังไม่มี log</p>
</div>
`;
  }

  // Destroy existing MultiSelects
  if (eventUsersMS) eventUsersMS.destroy();
  if (eventContactsMS) eventContactsMS.destroy();
  if (eventProductsMS) eventProductsMS.destroy();
  eventUsersMS = null;
  eventContactsMS = null;
  eventProductsMS = null;
}

async function setupMainUserBadge(user) {
  const container = document.getElementById("mainUserBadgeContainer");
  if (!container) return;

  const color =
    userColorCache.get(user.Id) || (await promiseColorById(user.Id));

  container.innerHTML = `
<div class="main-user-badge" style="background-color: ${
    color?.color?.code || "#666"
  }; color: ${color?.textColor || "#fff"}">
<i class="fas fa-user-tie"></i>
<span>${user.FirstName} ${user.LastName}</span>
<span class="opacity-70">(${user.Position || "N/A"})</span>
</div>
`;
}

async function setupGroupSelect(groups) {
  const select = document.getElementById("eventGroup");
  if (!select) return;

  select.innerHTML =
    '<option value="" disabled selected>เลือกกลุ่ม...</option>';

  groups.sort((a, b) => (a.GroupName || "").localeCompare(b.GroupName || ""));

  for (const group of groups) {
    const option = document.createElement("option");
    option.value = group.Id;
    option.textContent = group.GroupName;
    select.appendChild(option);
  }

  // Handle group change to auto-select members
  select.onchange = async (e) => {
    const groupId = e.target.value;
    if (!groupId || !eventUsersMS) return;

    try {
      const groupMembers = await promiseGroupMembers(groupId);
      const memberIds = groupMembers.GroupUsers?.map((u) => u.UserId) || [];
      eventUsersMS.setValues(memberIds);
      showToast(
        "success",
        `เลือกกลุ่ม "${groups.find((g) => g.Id == groupId)?.GroupName}" แล้ว`
      );
    } catch (error) {
      log("Event", "ERROR", "Failed to load group members", {
        error: error.message,
      });
    }
  };
}

async function setupModalMultiSelects(
  users,
  contacts,
  products,
  eventData,
  mainUser
) {
  // Prepare user options (exclude main user)
  const userOptions = users
    .filter((u) => u.Enabled !== false && u.Id !== mainUser.Id)
    .sort((a, b) => a.FirstName.localeCompare(b.FirstName))
    .map((u) => ({
      value: u.Id,
      label: `${u.FirstName} ${u.LastName} (${u.Position || ""})`,
    }));

  // Prepare contact options
  const contactOptions = contacts
    .sort((a, b) => (a.Name || "").localeCompare(b.Name || ""))
    .map((c) => ({
      value: c.Id,
      label: c.Name || "Unknown",
    }));

  // Prepare product options
  const productOptions = products
    .sort((a, b) => (a.Name || "").localeCompare(b.Name || ""))
    .map((p) => ({
      value: p.Id,
      label: p.Name || "Unknown",
    }));

  // Get selected values from event data
  const selectedUsers = eventData.EventUsers?.map((u) => u.UserId) || [];
  const selectedContacts =
    eventData.EventContacts?.map((c) => c.ContactId) || [];
  const selectedProducts =
    eventData.EventProducts?.map((p) => p.ProductId) || [];

  // Create MultiSelects
  eventUsersMS = new MultiSelect("eventUsersContainer", {
    options: userOptions,
    placeholder: "เลือกผู้รับผิดชอบร่วม...",
    badgeClass: "badge-primary",
    searchable: true,
    showSelectAll: false,
  });
  eventUsersMS.setValues(selectedUsers);

  eventContactsMS = new MultiSelect("eventContactsContainer", {
    options: contactOptions,
    placeholder: "เลือกผู้ติดต่อ...",
    badgeClass: "badge-secondary",
    searchable: true,
    showSelectAll: false,
  });
  eventContactsMS.setValues(selectedContacts);

  eventProductsMS = new MultiSelect("eventProductsContainer", {
    options: productOptions,
    placeholder: "เลือกสินค้า...",
    badgeClass: "badge-accent",
    searchable: true,
    showSelectAll: false,
  });
  eventProductsMS.setValues(selectedProducts);
}

function populateEventForm(eventData, info) {
  document.getElementById("eventTitle").value = eventData.Title || "";
  document.getElementById("eventPlan").value = eventData.Plan || "";
  document.getElementById("eventReport").value = eventData.Report || "";
  document.getElementById("eventComment").value = eventData.Comment || "";
  document.getElementById("eventAllDay").checked = eventData.IsAllDay || false;

  // Helper function to get local date string (YYYY-MM-DD)
  const getLocalDateStr = (date) => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };

  // Handle date/time with info override for drag/resize
  let startDate = eventData.StartDate;
  let endDate = eventData.EndDate;

  if (info?.event && info?.oldEvent) {
    // Drag or resize - use new date from calendar but keep original time
    const newStartDateStr = getLocalDateStr(info.event.start);
    
    // For end date: calendar uses exclusive end (next day at 00:00 for all-day events)
    // Need to subtract 1 day for all-day events
    let newEndDate = info.event.end ? new Date(info.event.end) : new Date(info.event.start);
    if (info.event.allDay && info.event.end) {
      newEndDate.setDate(newEndDate.getDate() - 1);
    }
    const newEndDateStr = getLocalDateStr(newEndDate);
    
    const originalStartTime = eventData.StartDate.split("T")[1];
    const originalEndTime = eventData.EndDate.split("T")[1];
    startDate = newStartDateStr + "T" + originalStartTime;
    endDate = newEndDateStr + "T" + originalEndTime;
  }

  // eventData.StartDate is already in format "YYYY-MM-DDTHH:mm:ss" (local time from API)
  // Just slice to "YYYY-MM-DDTHH:mm" for datetime-local input
  document.getElementById("eventStartDate").value = startDate
    ? startDate.slice(0, 16)
    : "";
  document.getElementById("eventEndDate").value = endDate
    ? endDate.slice(0, 16)
    : "";
}

function closeEventModal() {
  const modal = document.getElementById("eventModal");
  if (!modal) return;

  // Revert calendar changes if cancelled
  if (currentInfo?.revert && typeof currentInfo.revert === "function") {
    currentInfo.revert();
  }

  currentEventId = null;
  currentInfo = null;

  // Clear URL parameter when closing modal
  updateEventUrlParam(null);

  // Remove ESC key listener
  modal.removeEventListener("keydown", preventEscClose);

  modal.close();
}

// Prevent ESC key from closing modal
function preventEscClose(e) {
  if (e.key === "Escape") {
    e.preventDefault();
    e.stopPropagation();
  }
}

// ================================
// URL Parameter Management
// ================================
function updateEventUrlParam(eventId) {
  const url = new URL(window.location);
  
  if (eventId) {
    url.searchParams.set('id', eventId);
  } else {
    url.searchParams.delete('id');
  }
  
  // Update URL without reloading the page
  window.history.replaceState({}, '', url);
  log("Event", "INFO", `URL updated`, { eventId, url: url.toString() });
}

// Open QuickNav from inside Event Modal
function openQuickNavFromModal() {
  // QuickNav will read the current URL which now has the event ID
  if (typeof openQuickNavModal === 'function') {
    openQuickNavModal();
  } else if (window.QuickNav && typeof window.QuickNav.open === 'function') {
    window.QuickNav.open();
  } else {
    console.warn('QuickNav not available');
    showToast('warning', 'QuickNav ยังไม่พร้อมใช้งาน');
  }
}

// ================================
// Save Event
// ================================
async function saveEvent() {
  log("Event", "INFO", "Saving event", { eventId: currentEventId });

  showLoading();

  try {
    // Get form data
    const groupSelect = document.getElementById("eventGroup");
    const groupId = groupSelect?.value ? parseInt(groupSelect.value) : null;

    const eventData = {
      Id: currentEventId,
      Title: document.getElementById("eventTitle").value,
      StartDate: document.getElementById("eventStartDate").value,
      EndDate: document.getElementById("eventEndDate").value,
      IsAllDay: document.getElementById("eventAllDay").checked,
      Plan: document.getElementById("eventPlan").value,
      Report: document.getElementById("eventReport").value,
      Comment: document.getElementById("eventComment").value,
      Users: eventUsersMS?.getValues() || [],
      Contacts: eventContactsMS?.getValues() || [],
      Products: eventProductsMS?.getValues() || [],
      GroupId: groupId,
      // Use the MainUserID stored when modal was loaded
      MainUserID: currentMainUserID,
    };

    // Validate
    if (!eventData.Title.trim()) {
      showToast("error", "กรุณาระบุชื่อ Event");
      hideLoading();
      return;
    }

    // Get old event data for change logging (only if editing)
    let oldEventData = null;
    if (currentEventId) {
      try {
        oldEventData = await promiseEventById(currentEventId);
      } catch (e) {
        log("Event", "WARN", "Could not fetch old event data for logging");
      }
    }

    // Save event first
    const result = await PromiseUpdateEvent(currentEventId, eventData);
    log("Event", "INFO", "Event saved successfully", { result });

    // Get the event ID (either existing or newly created)
    const savedEventId = currentEventId || result?.Id || result?.id;

    // Log changes after successful save (only if editing and have old data)
    if (savedEventId && oldEventData) {
      await logEventChanges(oldEventData, eventData, savedEventId);
    }

    // Refresh calendar
    await queryEvents();

    // Close modal
    currentInfo = null; // Don't revert since we saved
    document.getElementById("eventModal")?.close();

    hideLoading();
    showToast(
      "success",
      currentEventId ? "บันทึก Event เรียบร้อย" : "สร้าง Event เรียบร้อย"
    );
  } catch (error) {
    log("Event", "ERROR", "Failed to save event", { error: error.message });
    hideLoading();
    showToast("error", `ไม่สามารถบันทึกได้: ${error.message}`);
  }
}

async function logEventChanges(oldEvent, newData, eventId) {
  if (!eventId) {
    log("Event", "WARN", "Cannot log changes: no eventId");
    return;
  }

  try {
    // Get lookup data for names
    const [users, contacts, products, groups] = await Promise.all([
      promiseUsers(),
      promiseContacts(),
      promiseProducts(),
      promiseGroups(),
    ]);

    // Helper functions to get names by ID
    const getUserName = (id) => {
      const user = users.find((u) => u.Id === id);
      return user ? `${user.FirstName} ${user.LastName}(${id})` : `ID:${id}`;
    };
    const getContactName = (id) => {
      const contact = contacts.find((c) => c.Id === id);
      return contact ? `${contact.Name}(${id})` : `ID:${id}`;
    };
    const getProductName = (id) => {
      const product = products.find((p) => p.Id === id);
      return product ? `${product.Name}(${id})` : `ID:${id}`;
    };
    const getGroupName = (id) => {
      const group = groups.find((g) => g.Id === id);
      return group ? group.Name : "N/A";
    };

    const changes = [];

    // Helper function to compare arrays of IDs
    const arraysEqual = (arr1, arr2) => {
      const a = (arr1 || []).map((x) => parseInt(x)).sort((a, b) => a - b);
      const b = (arr2 || []).map((x) => parseInt(x)).sort((a, b) => a - b);
      return a.length === b.length && a.every((v, i) => v === b[i]);
    };

    // Helper to get IDs from old event structure (EventUsers, EventContacts, EventProducts)
    const getOldUserIds = () =>
      (oldEvent.EventUsers || []).map((u) => u.UserId);
    const getOldContactIds = () =>
      (oldEvent.EventContacts || []).map((c) => c.ContactId);
    const getOldProductIds = () =>
      (oldEvent.EventProducts || []).map((p) => p.ProductId);

    // Helper to format list of names
    const formatNames = (ids, getNameFn) => {
      if (!ids || ids.length === 0) return "N/A";
      return ids.map((id) => getNameFn(id)).join(", ");
    };

    // Title
    if ((oldEvent.Title || "") !== (newData.Title || "")) {
      changes.push({
        field: "ชื่อ Event",
        old: oldEvent.Title || "-",
        new: newData.Title || "-",
      });
    }

    // StartDate (compare first 16 chars to ignore seconds)
    const oldStart = oldEvent.StartDate ? oldEvent.StartDate.slice(0, 16) : "";
    const newStart = newData.StartDate ? newData.StartDate.slice(0, 16) : "";
    if (oldStart !== newStart) {
      changes.push({
        field: "วันเริ่มต้น",
        old: formatDateTimeThai(oldEvent.StartDate) || "-",
        new: formatDateTimeThai(newData.StartDate) || "-",
      });
    }

    // EndDate
    const oldEnd = oldEvent.EndDate ? oldEvent.EndDate.slice(0, 16) : "";
    const newEnd = newData.EndDate ? newData.EndDate.slice(0, 16) : "";
    if (oldEnd !== newEnd) {
      changes.push({
        field: "วันสิ้นสุด",
        old: formatDateTimeThai(oldEvent.EndDate) || "-",
        new: formatDateTimeThai(newData.EndDate) || "-",
      });
    }

    // IsAllDay
    if (Boolean(oldEvent.IsAllDay) !== Boolean(newData.IsAllDay)) {
      changes.push({
        field: "All Day",
        old: oldEvent.IsAllDay ? "true" : "false",
        new: newData.IsAllDay ? "true" : "false",
      });
    }

    // Group
    const oldGroupId = oldEvent.GroupId || null;
    const newGroupId = newData.GroupId || null;
    if (oldGroupId !== newGroupId) {
      changes.push({
        field: "Group",
        old: oldGroupId ? getGroupName(oldGroupId) : "N/A",
        new: newGroupId ? getGroupName(newGroupId) : "N/A",
      });
    }

    // Plan
    if ((oldEvent.Plan || "") !== (newData.Plan || "")) {
      changes.push({
        field: "Plan",
        old: oldEvent.Plan || "N/A",
        new: newData.Plan || "N/A",
      });
    }

    // Report
    if ((oldEvent.Report || "") !== (newData.Report || "")) {
      changes.push({
        field: "Report",
        old: oldEvent.Report || "N/A",
        new: newData.Report || "N/A",
      });
    }

    // Comment
    if ((oldEvent.Comment || "") !== (newData.Comment || "")) {
      changes.push({
        field: "Comment",
        old: oldEvent.Comment || "N/A",
        new: newData.Comment || "N/A",
      });
    }

    // Users Dropdown (show names)
    const oldUserIds = getOldUserIds();
    const newUserIds = (newData.Users || []).map((x) => parseInt(x));
    if (!arraysEqual(oldUserIds, newUserIds)) {
      changes.push({
        field: "Users Dropdown",
        old: formatNames(oldUserIds, getUserName),
        new: formatNames(newUserIds, getUserName),
      });
    }

    // Contacts Dropdown (show names)
    const oldContactIds = getOldContactIds();
    const newContactIds = (newData.Contacts || []).map((x) => parseInt(x));
    if (!arraysEqual(oldContactIds, newContactIds)) {
      changes.push({
        field: "Contacts Dropdown",
        old: formatNames(oldContactIds, getContactName),
        new: formatNames(newContactIds, getContactName),
      });
    }

    // Products Dropdown (show names)
    const oldProductIds = getOldProductIds();
    const newProductIds = (newData.Products || []).map((x) => parseInt(x));
    if (!arraysEqual(oldProductIds, newProductIds)) {
      changes.push({
        field: "Products Dropdown",
        old: formatNames(oldProductIds, getProductName),
        new: formatNames(newProductIds, getProductName),
      });
    }

    console.log("Change detection:", {
      eventId,
      changesCount: changes.length,
      changes,
    });

    if (changes.length > 0) {
      // LogValue = Human readable text for users (field: old ▸ new)
      const logValue = changes
        .map((c) => `${c.field}: ${c.old} ▸ ${c.new}`)
        .join("\n");

      // SystemLog = Full JSON with all details for debugging
      const systemLogData = {
        eventId: parseInt(eventId),
        timestamp: new Date().toISOString(),
        changes: changes,
      };
      const systemLog = JSON.stringify(systemLogData);

      const eventIdInt = parseInt(eventId);

      console.log("Calling promiseCreateLog with:", {
        logValue,
        systemLog,
        eventId: eventIdInt,
        type: 4,
      });

      if (isNaN(eventIdInt)) {
        console.error("Invalid eventId - cannot create log");
        return;
      }

      const result = await promiseCreateLog(
        logValue,
        systemLog,
        null,
        eventIdInt,
        null,
        null,
        null,
        4
      );
      console.log("promiseCreateLog result:", result);
      log(
        "Event",
        "INFO",
        `Logged ${changes.length} changes for event ${eventId}`
      );
    } else {
      log("Event", "DEBUG", "No changes detected, skipping log");
      console.log("No changes detected - old and new data are identical");
    }
  } catch (error) {
    console.error("logEventChanges error:", error);
    log("Event", "WARN", "Failed to log changes", { error: error.message });
  }
}

// ================================
// Delete Event
// ================================
function confirmDeleteEvent() {
  document.getElementById("eventActionButtons")?.classList.add("hidden");
  document.getElementById("deleteConfirmButtons")?.classList.remove("hidden");
}

function cancelDelete() {
  document.getElementById("eventActionButtons")?.classList.remove("hidden");
  document.getElementById("deleteConfirmButtons")?.classList.add("hidden");
}

async function deleteEventConfirmed() {
  if (!currentEventId) return;

  log("Event", "INFO", "Deleting event", { eventId: currentEventId });

  showLoading();

  try {
    await promiseDeleteEventById(currentEventId);

    // Remove from calendar
    if (ec) {
      ec.removeEventById(currentEventId);
    }

    // Refresh events
    await queryEvents();

    // Close modal
    currentInfo = null;
    document.getElementById("eventModal")?.close();

    hideLoading();
    showToast("success", "ลบ Event เรียบร้อย");
  } catch (error) {
    log("Event", "ERROR", "Failed to delete event", { error: error.message });
    hideLoading();
    showToast("error", `ไม่สามารถลบได้: ${error.message}`);
  }
}

// ================================
// Log System
// ================================
function showLogInput() {
  document.getElementById("logInputContainer")?.classList.remove("hidden");
  document.getElementById("addLogBtn")?.classList.add("hidden");
  document.getElementById("logTextInput")?.focus();
}

function hideLogInput() {
  document.getElementById("logInputContainer")?.classList.add("hidden");
  document.getElementById("addLogBtn")?.classList.remove("hidden");
  document.getElementById("logTextInput").value = "";
}

async function saveLogEntry() {
  if (!currentEventId) {
    showToast("error", "กรุณาบันทึก Event ก่อน");
    return;
  }

  const text = document.getElementById("logTextInput")?.value?.trim();
  if (!text) {
    showToast("error", "กรุณาเขียน log");
    return;
  }

  try {
    // Type 0 = Text, 2 = File, 3 = Binder, 4 = System
    // LogValue = user readable, SystemLog = debug info (cannot be null)
    await promiseCreateLog(
      text,
      text,
      null,
      parseInt(currentEventId),
      null,
      null,
      null,
      0
    );
    hideLogInput();
    await loadEventLogs(currentEventId);
    showToast("success", "บันทึก log เรียบร้อย");
  } catch (error) {
    log("Event", "ERROR", "Failed to save log", { error: error.message });
    showToast("error", `ไม่สามารถบันทึก log ได้: ${error.message}`);
  }
}

async function loadEventLogs(eventId) {
  const container = document.getElementById("logsContainer");
  if (!container) return;

  console.log("loadEventLogs called with eventId:", eventId);

  try {
    const logs = await promiseLogs(eventId);

    console.log("Logs received:", logs);

    if (!logs || logs.length === 0) {
      console.log("No logs found");
      container.innerHTML = `
<div class="text-center text-base-content/50 py-8" id="logsPlaceholder">
<i class="fas fa-clipboard-list text-3xl mb-2"></i>
<p class="text-sm">ยังไม่มี log</p>
</div>
`;
      return;
    }

    // Sort logs by date (newest first)
    logs.sort((a, b) => new Date(b.DateTime) - new Date(a.DateTime));

    console.log("Logs sorted, processing", logs.length, "logs");

    let html = "";
    for (const logItem of logs) {
      console.log("Processing log item:", logItem);

      const user = await promiseUserById(logItem.UserId);
      const userName = user ? `${user.FirstName} ${user.LastName}` : "Unknown";
      const timeStr = formatDateTimeThai(logItem.DateTime);

      // Determine log type and styling
      // Type: 0=Text, 1=Image, 2=File, 3=Binder, 4=System
      let typeClass = "text";
      let typeLabel = "บันทึก";
      let typeIcon = "fa-comment";
      let itemClass = "";

      const logType =
        typeof logItem.Type === "string"
          ? ["Text", "Image", "File", "Binder", "System"].indexOf(logItem.Type)
          : logItem.Type;

      if (logType === 4) {
        typeClass = "change";
        typeLabel = "System";
        typeIcon = "fa-sync-alt";
        itemClass = "system";
      } else if (logType === 2) {
        typeClass = "file";
        typeLabel = "ไฟล์";
        typeIcon = "fa-paperclip";
        itemClass = "file";
      } else if (logType === 3) {
        typeClass = "binder";
        typeLabel = "Binder";
        typeIcon = "fa-link";
        itemClass = "binder";
      }

      // Parse content for change logs (use LogValue instead of Content)
      // Escape HTML for safety
      const escapeHtml = (str) => {
        if (!str) return "";
        return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
      };
      
      let contentHtml = escapeHtml(logItem.LogValue || "");
      if (logType === 4 && logItem.LogValue) {
        // For system logs, format each line with bold field names (text before :)
        const lines = logItem.LogValue.split("\n");
        const formattedLines = lines.map((line) => {
          const colonIndex = line.indexOf(":");
          if (colonIndex > 0) {
            const fieldName = escapeHtml(line.substring(0, colonIndex));
            const fieldValue = escapeHtml(line.substring(colonIndex + 1));
            return `<strong>${fieldName}:</strong>${fieldValue}`;
          }
          return escapeHtml(line);
        });
        contentHtml = `<div class="log-change-detail whitespace-pre-line">${formattedLines.join("<br>")}</div>`;
      }

      // File attachment (use SystemLog for file URL)
      let fileHtml = "";
      if (logType === 2 && logItem.SystemLog) {
        const fileUrl = `./storage/${logItem.SystemLog}`;
        const fileName = logItem.SystemLog.toLowerCase();
        const ext = fileName.split(".").pop();

        // Check file type
        const imageExts = ["jpg", "jpeg", "png", "gif", "bmp", "svg", "webp"];
        const videoExts = ["mp4", "avi", "mov", "wmv", "flv", "mkv", "webm"];

        if (imageExts.includes(ext)) {
          // Display image preview + download link
          fileHtml = `<div class="mt-2"><a href="${fileUrl}" target="_blank"><img src="${fileUrl}" alt="${logItem.LogValue}" class="rounded-lg max-w-full max-h-48 object-contain border border-base-300" /></a><a href="${fileUrl}" target="_blank" class="flex items-center gap-2 mt-1 text-sm text-primary hover:underline"><i class="fas fa-download"></i> ดาวน์โหลดไฟล์</a></div>`;
        } else if (videoExts.includes(ext)) {
          // Display video player + download link
          fileHtml = `<div class="mt-2"><video controls class="rounded-lg max-w-full max-h-48 border border-base-300"><source src="${fileUrl}" type="video/${ext === "mov" ? "quicktime" : ext}">Your browser does not support the video tag.</video><a href="${fileUrl}" target="_blank" class="flex items-center gap-2 mt-1 text-sm text-primary hover:underline"><i class="fas fa-download"></i> ดาวน์โหลดไฟล์</a></div>`;
        } else {
          // Regular file download link
          fileHtml = `<a href="${fileUrl}" target="_blank" class="flex items-center gap-2 mt-2 text-sm text-primary hover:underline"><i class="fas fa-download"></i> ดาวน์โหลดไฟล์</a>`;
        }
      }

      // Binder content rendering
      let binderHtml = "";
      if (logType === 3 && logItem.SystemLog) {
        try {
          const binderData = JSON.parse(logItem.SystemLog);
          let report = "";
          if (binderData.logLeadId !== null) {
            report += `<a href="./crm-detail.html?leadid=${binderData.logLeadId}" class="link link-primary">Lead (${binderData.logLeadId})</a> ⮜⬥⮞ `;
          }
          if (binderData.logEventId !== null) {
            report += `<a href="./event.html?id=${binderData.logEventId}" class="link link-primary">Event (${binderData.logEventId})</a> ⮜⬥⮞ `;
          }
          if (binderData.logHelpdeskTicketId !== null) {
            report += `<a href="./helpdesk-detail.html?hdid=${binderData.logHelpdeskTicketId}" class="link link-primary">Helpdesk (${binderData.logHelpdeskTicketId})</a> ⮜⬥⮞ `;
          }
          if (binderData.logActivityId !== null) {
            report += `<a href="./project-activity.html?activityid=${binderData.logActivityId}" class="link link-primary">Activity (${binderData.logActivityId})</a> ⮜⬥⮞ `;
          }
          // Remove trailing separator
          if (report.endsWith(" ⮜⬥⮞ ")) {
            report = report.slice(0, -5
            );
          }
          binderHtml = `<span class="opacity-70">Binding:</span> ${report}`;
          contentHtml = binderHtml; // Override content with binder links
        } catch (e) {
          console.error("Failed to parse binder data:", e);
        }
      }

      html += `<div class="log-item ${itemClass}"><div class="log-item-header"><span class="log-item-user"><i class="fas fa-user-circle mr-1"></i>${userName}</span><span class="log-item-time">${timeStr}</span></div><div class="log-item-content"><span class="log-item-type ${typeClass}"><i class="fas ${typeIcon} mr-1"></i>${typeLabel}</span>${contentHtml}${fileHtml}</div></div>`;
    }

    container.innerHTML = html;
  } catch (error) {
    log("Event", "ERROR", "Failed to load logs", { error: error.message });
    container.innerHTML = `<div class="text-center text-error py-4"><i class="fas fa-exclamation-triangle mr-2"></i>ไม่สามารถโหลด log ได้</div>`;
  }
}

// Format change log content for better display
function formatChangeLog(content) {
  if (!content) return "";

  // Try to parse as JSON (new format)
  try {
    const changes = JSON.parse(content);
    if (Array.isArray(changes)) {
      let html = '<div class="log-change-detail">';
      for (const change of changes) {
        html += `
<div class="mb-1">
<span class="log-change-field">${change.field}:</span>
<span class="log-change-old">${change.old || "-"}</span>
<span class="log-change-arrow">→</span>
<span class="log-change-new">${change.new || "-"}</span>
</div>
`;
      }
      html += "</div>";
      return html;
    }
  } catch (e) {
    // Not JSON, return as plain text
  }

  return content;
}

// Format datetime in Thai style
function formatDateTimeThai(dateStr) {
  if (!dateStr) return "";
  const date = new Date(dateStr);
  const options = {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  };
  return date.toLocaleDateString("th-TH", options);
}

function addLogFile() {
  if (!currentEventId) {
    showToast("error", "กรุณาบันทึก Event ก่อน");
    return;
  }

  uploadFile(async function (err, file) {
    if (err) {
      console.error("Upload error:", err);
      showToast("error", "ไม่สามารถอัพโหลดไฟล์ได้");
      return;
    }

    try {
      // file = filename returned from server (e.g. "timestamp_userid_filename.ext")
      // Extract display name (remove timestamp and userid prefix)
      const fileName = file.split("_").slice(2).join("_") || file;

      // Type 2 = File
      // LogValue = display name, SystemLog = actual filename for download
      await promiseCreateLog(
        fileName,
        file,
        null,
        parseInt(currentEventId),
        null,
        null,
        null,
        2
      );
      await loadEventLogs(currentEventId);
      showToast("success", "อัพโหลดไฟล์เรียบร้อย");
    } catch (error) {
      console.error("Create log error:", error);
      showToast("error", `ไม่สามารถบันทึก log ได้: ${error.message}`);
    }
  });
}

function pickupBinder() {
  if (!currentEventId) {
    showToast("error", "กรุณาบันทึก Event ก่อน");
    return;
  }
  
  const binderTemporary = {
    logLeadId: null,
    logEventId: parseInt(currentEventId),
    logHelpdeskTicketId: null,
    logActivityId: null
  };
  localStorage.setItem('binderTemporary', JSON.stringify(binderTemporary));
  console.log('Binder data saved from Event:', binderTemporary);
  showToast("success", "Pickup Binder สำเร็จ - ไปที่หน้าอื่นเพื่อ Drop");
  loadBinderState();
}

async function dropBinder() {
  if (!currentEventId) {
    showToast("error", "กรุณาบันทึก Event ก่อน");
    return;
  }
  
  const binderTemporary = JSON.parse(localStorage.getItem('binderTemporary'));
  if (!binderTemporary) {
    showToast("error", "ไม่พบข้อมูล Binder");
    return;
  }
  
  const { logLeadId: binderLeadId, logEventId: binderEventId, logHelpdeskTicketId: binderHelpdeskId, logActivityId: binderActivityId } = binderTemporary;
  
  const localEventId = parseInt(currentEventId);
  
  // Validation: Check for conflicting IDs
  if (binderEventId !== null && localEventId !== null) {
    showToast("error", "ไม่สามารถ Bind Event กับ Event ได้");
    return;
  }
  
  const newBinder = {
    logLeadId: binderLeadId,
    logEventId: binderEventId !== null ? binderEventId : localEventId,
    logHelpdeskTicketId: binderHelpdeskId,
    logActivityId: binderActivityId
  };
  
  // Build report text
  let report = '';
  if (newBinder.logLeadId !== null) report += `Lead (${newBinder.logLeadId}) <-> `;
  if (newBinder.logEventId !== null) report += `Event (${newBinder.logEventId}) <-> `;
  if (newBinder.logHelpdeskTicketId !== null) report += `Helpdesk (${newBinder.logHelpdeskTicketId}) <-> `;
  if (newBinder.logActivityId !== null) report += `Activity (${newBinder.logActivityId}) <-> `;
  
  if (report.endsWith(' <-> ')) {
    report = report.slice(0, -5);
  }
  
  console.log('Creating binder log:', report);
  
  try {
    // Type 3 = Binder
    await promiseCreateLog(
      "Binding between " + report,
      JSON.stringify(newBinder),
      newBinder.logLeadId,
      newBinder.logEventId,
      null,
      newBinder.logHelpdeskTicketId,
      newBinder.logActivityId,
      3
    );
    
    localStorage.removeItem('binderTemporary');
    showToast("success", "Drop Binder สำเร็จ");
    loadBinderState();
    await loadEventLogs(currentEventId);
  } catch (error) {
    console.error('Error creating binder log:', error);
    showToast("error", `ไม่สามารถสร้าง Binder ได้: ${error.message}`);
  }
}

function cancelBinder() {
  localStorage.removeItem('binderTemporary');
  console.log('Binder data removed from localStorage');
  showToast("info", "ยกเลิก Binder แล้ว");
  loadBinderState();
}

function loadBinderState() {
  const bindingBtn = document.getElementById("bindingBtn");
  const dropBtn = document.getElementById("dropBtn");
  const cancelBinderBtn = document.getElementById("cancelBinderBtn");
  
  console.log('loadBinderState called - buttons found:', {
    bindingBtn: !!bindingBtn,
    dropBtn: !!dropBtn,
    cancelBinderBtn: !!cancelBinderBtn
  });
  
  if (!bindingBtn || !dropBtn || !cancelBinderBtn) {
    console.log('Binder buttons not found in Event modal');
    return;
  }
  
  const binderTemporary = localStorage.getItem('binderTemporary');
  console.log('Binder localStorage value:', binderTemporary);
  
  if (binderTemporary) {
    const parsedBinder = JSON.parse(binderTemporary);
    console.log('Binder data loaded in Event:', parsedBinder);
    
    bindingBtn.classList.add("hidden");
    dropBtn.classList.remove("hidden");
    cancelBinderBtn.classList.remove("hidden");
    
    // Check if we can drop here (no conflicting Event ID)
    const localEventId = currentEventId ? parseInt(currentEventId) : null;
    if (parsedBinder.logEventId !== null && localEventId !== null) {
      // Cannot bind Event to Event
      dropBtn.setAttribute('disabled', '');
      dropBtn.classList.add('btn-disabled');
    } else {
      dropBtn.removeAttribute('disabled');
      dropBtn.classList.remove('btn-disabled');
    }
  } else {
    bindingBtn.classList.remove("hidden");
    dropBtn.classList.add("hidden");
    cancelBinderBtn.classList.add("hidden");
  }
}

// ================================
// API Functions
// ================================
async function PromiseUpdateEvent(id, eventData) {
  return new Promise((resolve, reject) => {
    const token = readToken();
    const xhr = new XMLHttpRequest();
    const endpoint = id
      ? "/biomedapi/v2/event/update"
      : "/biomedapi/v2/event/create";

    const data = {
      Id: id ? parseInt(id) : null,
      Title: eventData.Title || "",
      Description: eventData.Description || "",
      StartDate: timeFormater(eventData.StartDate),
      EndDate: timeFormater(eventData.EndDate),
      IsAllDay: eventData.IsAllDay || false,
      Location: eventData.Location || null,
      Plan: eventData.Plan || "",
      Report: eventData.Report || "",
      Comment: eventData.Comment || "",
      Conferenceurl: eventData.ConferenceURL || "",
      Mainuserid: eventData.MainUserID ? parseInt(eventData.MainUserID) : null,
      MaincontactID: eventData.MainContactID
        ? parseInt(eventData.MainContactID)
        : null,
      ProductIDs: (eventData.Products || []).map((p) => parseInt(p)),
      SubUserIDs: (eventData.Users || []).map((u) => parseInt(u)),
      SubContactIDs: (eventData.Contacts || []).map((c) => parseInt(c)),
    };

    // DEBUG: Log request body
    console.log("📤 PromiseUpdateEvent - Endpoint:", endpoint);
    console.log(
      "📤 PromiseUpdateEvent - Request Body:",
      JSON.stringify(data, null, 2)
    );

    xhr.open("POST", url + endpoint, true);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.setRequestHeader("Authorization", "Bearer " + token);

    xhr.onreadystatechange = function () {
      if (xhr.readyState === 4) {
        if (xhr.status === 200) {
          resolve(xhr.responseText);
        } else {
          reject(
            new Error(`Request failed: ${xhr.status} ${xhr.responseText}`)
          );
        }
      }
    };

    xhr.send(JSON.stringify(data));
  });
}

async function promiseDeleteEventById(id) {
  return new Promise((resolve, reject) => {
    const token = readToken();
    const xhr = new XMLHttpRequest();

    xhr.open("POST", url + "/biomedapi/v2/event/delete", true);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.setRequestHeader("Authorization", "Bearer " + token);

    xhr.onreadystatechange = function () {
      if (xhr.readyState === 4) {
        if (xhr.status === 200) {
          resolve(xhr.responseText);
        } else {
          reject(
            new Error(`Request failed: ${xhr.status} ${xhr.responseText}`)
          );
        }
      }
    };

    xhr.send(JSON.stringify({ Id: id }));
  });
}

// ================================
// Utility Functions
// ================================
function showLoading() {
  const overlay = document.getElementById("loadingOverlay");
  if (overlay) {
    overlay.classList.remove("hidden");
    overlay.classList.add("flex");
  }
}

function hideLoading() {
  const overlay = document.getElementById("loadingOverlay");
  if (overlay) {
    overlay.classList.add("hidden");
    overlay.classList.remove("flex");
  }
}

function updateAlertBar(type, message, autoHide = true) {
  const alertBar = document.getElementById("alertBar");
  if (!alertBar) return;

  const types = {
    info: { class: "alert-info", icon: "fa-info-circle" },
    success: { class: "alert-success", icon: "fa-check-circle" },
    warning: { class: "alert-warning", icon: "fa-exclamation-triangle" },
    error: { class: "alert-error", icon: "fa-times-circle" },
  };

  const config = types[type] || types.info;

  alertBar.className = `alert ${config.class} shadow-sm transition-opacity duration-300`;
  alertBar.style.opacity = "1";
  alertBar.innerHTML = `
<i class="fas ${config.icon}"></i>
<span>${message}</span>
`;

  // Auto hide after 3 seconds for success messages, 5 seconds for others
  if (autoHide) {
    const delay = type === "success" ? 3000 : 5000;
    setTimeout(() => {
      alertBar.style.opacity = "0";
      setTimeout(() => {
        alertBar.style.display = "none";
      }, 300);
    }, delay);
  }
}

function showToast(type, message) {
  const container = document.getElementById("toastContainer");
  if (!container) return;

  const types = {
    info: "alert-info",
    success: "alert-success",
    warning: "alert-warning",
    error: "alert-error",
  };

  const toast = document.createElement("div");
  toast.className = `alert ${types[type] || "alert-info"} shadow-lg toast-item`;
  toast.innerHTML = `<span>${message}</span>`;

  container.appendChild(toast);

  // Auto remove after 3 seconds
  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(100%)";
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

function formatDateForApi(date) {
  if (!date) return null;
  const d = new Date(date);
  return d.toISOString().split(".")[0];
}

function formatDateTimeLocal(date) {
  if (!date) return "";
  const d = new Date(date);

  // Use local time components (like timeFuck function)
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  const hours = String(d.getHours()).padStart(2, "0");
  const minutes = String(d.getMinutes()).padStart(2, "0");

  // Format: YYYY-MM-DDTHH:mm (for datetime-local input)
  return `${year}-${month}-${day}T${hours}:${minutes}`;
}

function formatDateTime(date) {
  if (!date) return "";
  const d = new Date(date);
  return d.toLocaleString("th-TH", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatDateThai(date) {
  if (!date) return "";
  const d = new Date(date);
  return d.toLocaleDateString("th-TH", {
    year: "numeric",
    month: "long",
    day: "numeric",
    weekday: "long",
  });
}

function formatTimeOnly(date) {
  if (!date) return "";
  const d = new Date(date);
  return d.toLocaleTimeString("th-TH", {
    hour: "2-digit",
    minute: "2-digit",
  });
}

// ================================
// Theme Functions
// ================================
function setTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
  localStorage.setItem("theme", theme);
}

// ================================
// Event Statistics & Charts
// ================================
let chartInstances = {};

/**
 * คำนวณสถานะ Event จาก StartDate, EndDate และ Report
 * - ต้องการ Report: ผ่านไปแล้ว (EndDate < now) และไม่มี Report
 * - เสร็จสิ้น: ผ่านไปแล้ว (EndDate < now) และมี Report
 * - กำลังดำเนินการ: ปัจจุบันอยู่ระหว่าง StartDate กับ EndDate
 * - กำลังจะมา: StartDate อยู่ใน 7 วันข้างหน้า
 * - นัดหมาย: StartDate มากกว่า 7 วันข้างหน้า
 */
function getEventStatus(event) {
  const now = new Date();
  now.setHours(0, 0, 0, 0);
  
  const startDate = new Date(event.StartDate);
  startDate.setHours(0, 0, 0, 0);
  
  const endDate = new Date(event.EndDate);
  endDate.setHours(23, 59, 59, 999);
  
  const hasReport = event.Report && event.Report.trim() !== '';
  const sevenDaysFromNow = new Date(now);
  sevenDaysFromNow.setDate(sevenDaysFromNow.getDate() + 7);
  
  // Check if event has ended (EndDate < now)
  if (endDate < now) {
    if (hasReport) {
      return { key: 'completed', label: 'เสร็จสิ้น', color: '#22c55e', badgeClass: 'badge-success' };
    } else {
      return { key: 'needsReport', label: 'ต้องการ Report', color: '#ef4444', badgeClass: 'badge-error' };
    }
  }
  
  // Check if currently in progress (now is between StartDate and EndDate)
  if (startDate <= now && now <= endDate) {
    return { key: 'inProgress', label: 'กำลังดำเนินการ', color: '#f59e0b', badgeClass: 'badge-warning' };
  }
  
  // Check if coming within 7 days
  if (startDate > now && startDate <= sevenDaysFromNow) {
    return { key: 'upcoming', label: 'กำลังจะมา', color: '#3b82f6', badgeClass: 'badge-info' };
  }
  
  // Default: scheduled (more than 7 days away)
  return { key: 'scheduled', label: 'นัดหมาย', color: '#8b5cf6', badgeClass: 'badge-primary' };
}

async function renderEventStatistics() {
  if (currentEventsData.length === 0) {
    return;
  }

  const events = currentEventsData;
  
  // Destroy existing charts
  Object.values(chartInstances).forEach(chart => {
    if (chart && typeof chart.destroy === 'function') {
      chart.destroy();
    }
  });
  chartInstances = {};

  // Calculate statistics with new status
  const totalEvents = events.length;
  const allDayEvents = events.filter(e => e.IsAllDay).length;
  
  // Calculate status counts
  const statusCounts = {
    needsReport: 0,
    completed: 0,
    inProgress: 0,
    upcoming: 0,
    scheduled: 0
  };
  
  events.forEach(e => {
    const status = getEventStatus(e);
    statusCounts[status.key]++;
  });
  
  // Unique users, products
  const uniqueUsers = new Set();
  const uniqueProducts = new Set();
  
  events.forEach(e => {
    uniqueUsers.add(e.MainUserID);
    e.Users?.forEach(u => uniqueUsers.add(u.UserId));
    // Use EventProducts instead of Products
    e.EventProducts?.forEach(p => uniqueProducts.add(p));
  });

  // Update stat cards
  document.getElementById('statTotalEvents').textContent = totalEvents;
  document.getElementById('statWithReport').textContent = statusCounts.completed;
  document.getElementById('statReportPercent').textContent = `เสร็จสิ้น ${Math.round(statusCounts.completed / totalEvents * 100)}%`;
  document.getElementById('statAllDay').textContent = statusCounts.needsReport;
  document.getElementById('statAllDayPercent').textContent = `ต้องการ Report ${statusCounts.needsReport} รายการ`;
  document.getElementById('statUniqueUsers').textContent = uniqueUsers.size;
  document.getElementById('statUniqueContacts').textContent = statusCounts.upcoming + statusCounts.scheduled;
  document.getElementById('statUniqueProducts').textContent = uniqueProducts.size;

  // Render charts
  await renderEventsByUserChart(events);
  renderEventsByDayOfWeekChart(events);
  renderEventsByMonthChart(events);
  await renderEventsByProductChart(events);
  renderEventStatusChart(events, statusCounts);
  renderEventsTimelineChart(events);
  renderEventsDurationChart(events);
  renderAttendeesDistributionChart(events);
  await renderWorkloadHeatmap(events);
  await renderRecentEventsTable(events);
}

async function renderEventsByUserChart(events) {
  const userCounts = {};
  events.forEach(e => {
    userCounts[e.MainUserID] = (userCounts[e.MainUserID] || 0) + 1;
  });

  const sortedUsers = Object.entries(userCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10);

  const labels = [];
  const data = [];
  const colors = [];

  for (const [userId, count] of sortedUsers) {
    const user = await promiseUserById(parseInt(userId));
    labels.push(user ? `${user.FirstName} ${user.LastName}` : 'Unknown');
    data.push(count);
    const color = userColorCache.get(parseInt(userId));
    colors.push(color?.color?.code || '#6b7280');
  }

  const ctx = document.getElementById('chartEventsByUser');
  if (!ctx) return;
  
  ctx.innerHTML = '<canvas></canvas>';
  chartInstances.eventsByUser = new Chart(ctx.querySelector('canvas'), {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'จำนวน Events',
        data,
        backgroundColor: colors,
        borderRadius: 4
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } }
    }
  });
}

function renderEventsByDayOfWeekChart(events) {
  const dayNames = ['อาทิตย์', 'จันทร์', 'อังคาร', 'พุธ', 'พฤหัสบดี', 'ศุกร์', 'เสาร์'];
  const dayCounts = [0, 0, 0, 0, 0, 0, 0];

  events.forEach(e => {
    const day = new Date(e.StartDate).getDay();
    dayCounts[day]++;
  });

  const ctx = document.getElementById('chartEventsByDayOfWeek');
  if (!ctx) return;
  
  ctx.innerHTML = '<canvas></canvas>';
  chartInstances.eventsByDayOfWeek = new Chart(ctx.querySelector('canvas'), {
    type: 'bar',
    data: {
      labels: dayNames,
      datasets: [{
        label: 'จำนวน Events',
        data: dayCounts,
        backgroundColor: ['#ef4444', '#f59e0b', '#eab308', '#22c55e', '#14b8a6', '#3b82f6', '#8b5cf6'],
        borderRadius: 4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } }
    }
  });
}

function renderEventsByMonthChart(events) {
  const monthNames = ['ม.ค.', 'ก.พ.', 'มี.ค.', 'เม.ย.', 'พ.ค.', 'มิ.ย.', 'ก.ค.', 'ส.ค.', 'ก.ย.', 'ต.ค.', 'พ.ย.', 'ธ.ค.'];
  const monthCounts = {};

  events.forEach(e => {
    const date = new Date(e.StartDate);
    // Use padded month (01-12) for correct string sorting
    const month = String(date.getMonth()).padStart(2, '0');
    const key = `${date.getFullYear()}-${month}`;
    monthCounts[key] = (monthCounts[key] || 0) + 1;
  });

  const sortedMonths = Object.entries(monthCounts).sort((a, b) => a[0].localeCompare(b[0]));
  const labels = sortedMonths.map(([key]) => {
    const [year, month] = key.split('-');
    return `${monthNames[parseInt(month)]} ${year}`;
  });
  const data = sortedMonths.map(([, count]) => count);

  const ctx = document.getElementById('chartEventsByMonth');
  if (!ctx) return;
  
  ctx.innerHTML = '<canvas></canvas>';
  chartInstances.eventsByMonth = new Chart(ctx.querySelector('canvas'), {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: 'จำนวน Events',
        data,
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        fill: true,
        tension: 0.3
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } }
    }
  });
}

async function renderEventsByProductChart(events) {
  const productCounts = {};
  events.forEach(e => {
    // EventProducts is array of objects with ProductId property
    e.EventProducts?.forEach(p => {
      const productId = p.ProductId || p; // Handle both object and direct ID formats
      productCounts[productId] = (productCounts[productId] || 0) + 1;
    });
  });

  console.log('[Event] Product counts from EventProducts:', productCounts);

  if (Object.keys(productCounts).length === 0) {
    document.getElementById('chartEventsByProduct').innerHTML = '<div class="flex items-center justify-center h-full text-base-content/50">ไม่มีข้อมูล Product</div>';
    return;
  }

  const sortedProducts = Object.entries(productCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 8);

  const products = await promiseProducts();
  const labels = sortedProducts.map(([id]) => {
    const product = products.find(p => p.Id === parseInt(id));
    return product?.Name || `Product ID: ${id}`;
  });
  const data = sortedProducts.map(([, count]) => count);
  const colors = ['#f59e0b', '#eab308', '#22c55e', '#14b8a6', '#3b82f6', '#8b5cf6', '#ec4899', '#ef4444'];

  const ctx = document.getElementById('chartEventsByProduct');
  if (!ctx) return;
  
  ctx.innerHTML = '<canvas></canvas>';
  chartInstances.eventsByProduct = new Chart(ctx.querySelector('canvas'), {
    type: 'doughnut',
    data: {
      labels,
      datasets: [{
        data,
        backgroundColor: colors
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { position: 'right' } }
    }
  });
}

// renderEventStatusChart - shows status distribution using new status logic
function renderEventStatusChart(events, statusCounts) {
  const ctx = document.getElementById('chartEventsByContact'); // reuse this container
  if (!ctx) return;
  
  const statusLabels = [
    { key: 'needsReport', label: 'ต้องการ Report', color: '#ef4444' },
    { key: 'completed', label: 'เสร็จสิ้น', color: '#22c55e' },
    { key: 'inProgress', label: 'กำลังดำเนินการ', color: '#f59e0b' },
    { key: 'upcoming', label: 'กำลังจะมา', color: '#3b82f6' },
    { key: 'scheduled', label: 'นัดหมาย', color: '#8b5cf6' }
  ];
  
  const labels = statusLabels.map(s => s.label);
  const data = statusLabels.map(s => statusCounts[s.key] || 0);
  const colors = statusLabels.map(s => s.color);

  ctx.innerHTML = '<canvas></canvas>';
  chartInstances.eventStatus = new Chart(ctx.querySelector('canvas'), {
    type: 'doughnut',
    data: {
      labels,
      datasets: [{
        data,
        backgroundColor: colors
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { position: 'right' } }
    }
  });
}

function renderEventsTimelineChart(events) {
  const dateCounts = {};
  events.forEach(e => {
    const dateKey = e.StartDate.split('T')[0];
    dateCounts[dateKey] = (dateCounts[dateKey] || 0) + 1;
  });

  const sortedDates = Object.entries(dateCounts).sort((a, b) => a[0].localeCompare(b[0]));
  const labels = sortedDates.map(([date]) => {
    const d = new Date(date);
    return `${d.getDate()}/${d.getMonth() + 1}`;
  });
  const data = sortedDates.map(([, count]) => count);

  const ctx = document.getElementById('chartEventsTimeline');
  if (!ctx) return;
  
  ctx.innerHTML = '<canvas></canvas>';
  chartInstances.eventsTimeline = new Chart(ctx.querySelector('canvas'), {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Events',
        data,
        backgroundColor: '#14b8a6',
        borderRadius: 2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: { x: { ticks: { maxRotation: 45 } } }
    }
  });
}

function renderEventsDurationChart(events) {
  const durationBuckets = {
    '< 1 ชม.': 0,
    '1-2 ชม.': 0,
    '2-4 ชม.': 0,
    '4-8 ชม.': 0,
    'ทั้งวัน': 0
  };

  events.forEach(e => {
    if (e.IsAllDay) {
      durationBuckets['ทั้งวัน']++;
    } else {
      const start = new Date(e.StartDate);
      const end = new Date(e.EndDate);
      const hours = (end - start) / (1000 * 60 * 60);
      
      if (hours < 1) durationBuckets['< 1 ชม.']++;
      else if (hours <= 2) durationBuckets['1-2 ชม.']++;
      else if (hours <= 4) durationBuckets['2-4 ชม.']++;
      else durationBuckets['4-8 ชม.']++;
    }
  });

  const ctx = document.getElementById('chartEventsDuration');
  if (!ctx) return;
  
  ctx.innerHTML = '<canvas></canvas>';
  chartInstances.eventsDuration = new Chart(ctx.querySelector('canvas'), {
    type: 'pie',
    data: {
      labels: Object.keys(durationBuckets),
      datasets: [{
        data: Object.values(durationBuckets),
        backgroundColor: ['#22c55e', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6']
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { position: 'right' } }
    }
  });
}

function renderAttendeesDistributionChart(events) {
  // Count attendees per event (Users array) and group by attendee count
  const attendeeBuckets = {
    '0 คน': 0,
    '1 คน': 0,
    '2 คน': 0,
    '3 คน': 0,
    '4 คน': 0,
    '5+ คน': 0
  };

  events.forEach(e => {
    // นับจาก Users array (ผู้ร่วมงาน)
    const attendeeCount = (e.Users && Array.isArray(e.Users)) ? e.Users.length : 0;
    
    if (attendeeCount === 0) attendeeBuckets['0 คน']++;
    else if (attendeeCount === 1) attendeeBuckets['1 คน']++;
    else if (attendeeCount === 2) attendeeBuckets['2 คน']++;
    else if (attendeeCount === 3) attendeeBuckets['3 คน']++;
    else if (attendeeCount === 4) attendeeBuckets['4 คน']++;
    else attendeeBuckets['5+ คน']++;
  });

  const ctx = document.getElementById('chartAttendeesDistribution');
  if (!ctx) return;
  
  ctx.innerHTML = '<canvas></canvas>';
  chartInstances.attendeesDistribution = new Chart(ctx.querySelector('canvas'), {
    type: 'bar',
    data: {
      labels: Object.keys(attendeeBuckets),
      datasets: [{
        label: 'จำนวน Events',
        data: Object.values(attendeeBuckets),
        backgroundColor: ['#94a3b8', '#22c55e', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6']
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: { 
        legend: { display: false }
      },
      scales: {
        x: {
          beginAtZero: true,
          ticks: { precision: 0 }
        }
      }
    }
  });
}

async function renderWorkloadHeatmap(events) {
  const dayNames = ['อา', 'จ', 'อ', 'พ', 'พฤ', 'ศ', 'ส'];
  
  // Get unique users
  const userWorkload = {};
  events.forEach(e => {
    const userId = e.MainUserID;
    const day = new Date(e.StartDate).getDay();
    
    if (!userWorkload[userId]) {
      userWorkload[userId] = [0, 0, 0, 0, 0, 0, 0];
    }
    userWorkload[userId][day]++;
  });

  // Build table
  const container = document.getElementById('chartWorkloadHeatmap');
  if (!container) return;

  let html = '<table class="table table-sm"><thead><tr><th>ผู้รับผิดชอบ</th>';
  dayNames.forEach(d => html += `<th class="text-center">${d}</th>`);
  html += '<th class="text-center">รวม</th></tr></thead><tbody>';

  const sortedUsers = Object.entries(userWorkload)
    .sort((a, b) => b[1].reduce((s, v) => s + v, 0) - a[1].reduce((s, v) => s + v, 0))
    .slice(0, 15);

  for (const [userId, counts] of sortedUsers) {
    const user = await promiseUserById(parseInt(userId));
    const userName = user ? `${user.FirstName} ${user.LastName}` : 'Unknown';
    const total = counts.reduce((s, v) => s + v, 0);
    const maxCount = Math.max(...counts);
    
    html += `<tr><td class="font-medium">${userName}</td>`;
    counts.forEach(count => {
      const intensity = maxCount > 0 ? count / maxCount : 0;
      const bgColor = count === 0 ? '#f3f4f6' : `rgba(59, 130, 246, ${0.2 + intensity * 0.8})`;
      const textColor = intensity > 0.5 ? '#fff' : '#374151';
      html += `<td class="text-center" style="background-color: ${bgColor}; color: ${textColor}">${count || '-'}</td>`;
    });
    html += `<td class="text-center font-bold">${total}</td></tr>`;
  }

  html += '</tbody></table>';
  container.innerHTML = html;
}

// Store events for sorting
let statsEventsData = [];
let currentSortColumn = 'date';
let currentSortDirection = 'desc';

// ================================
// Main Table Sorting
// ================================
let mainTableSortColumn = 'startDate';
let mainTableSortDirection = 'desc';

function sortMainTable(column) {
  if (mainTableSortColumn === column) {
    mainTableSortDirection = mainTableSortDirection === 'asc' ? 'desc' : 'asc';
  } else {
    mainTableSortColumn = column;
    mainTableSortDirection = (column === 'startDate' || column === 'endDate') ? 'desc' : 'asc';
  }

  // Sort currentEventsData in place
  currentEventsData.sort((a, b) => {
    let valueA, valueB;
    switch (column) {
      case 'title':
        valueA = (a.Title || '').toLowerCase();
        valueB = (b.Title || '').toLowerCase();
        break;
      case 'startDate':
        valueA = new Date(a.StartDate).getTime();
        valueB = new Date(b.StartDate).getTime();
        break;
      case 'endDate':
        valueA = new Date(a.EndDate).getTime();
        valueB = new Date(b.EndDate).getTime();
        break;
      case 'mainUser':
        valueA = a.MainUserID || 0;
        valueB = b.MainUserID || 0;
        break;
      case 'attendees':
        valueA = a.Users?.length || 0;
        valueB = b.Users?.length || 0;
        break;
      case 'product':
        valueA = a.EventProducts?.length || 0;
        valueB = b.EventProducts?.length || 0;
        break;
      case 'status':
        valueA = getEventStatusOrder(a);
        valueB = getEventStatusOrder(b);
        break;
      default:
        return 0;
    }
    if (valueA < valueB) return mainTableSortDirection === 'asc' ? -1 : 1;
    if (valueA > valueB) return mainTableSortDirection === 'asc' ? 1 : -1;
    return 0;
  });

  // Update sort icons
  updateMainTableSortIcons();

  // Re-render table
  populateEventsTable();
}

function updateMainTableSortIcons() {
  const columns = ['title', 'startDate', 'endDate', 'mainUser', 'attendees', 'product', 'status'];
  columns.forEach(col => {
    const iconId = 'mainSortIcon' + col.charAt(0).toUpperCase() + col.slice(1);
    const icon = document.getElementById(iconId);
    if (icon) {
      if (col === mainTableSortColumn) {
        icon.className = `fas fa-sort-${mainTableSortDirection === 'asc' ? 'up' : 'down'} text-primary ml-1`;
      } else {
        icon.className = 'fas fa-sort text-base-content/30 ml-1';
      }
    }
  });
}

async function renderRecentEventsTable(events) {
  const tbody = document.getElementById('recentEventsTable');
  const countEl = document.getElementById('allEventsCount');
  if (!tbody) return;

  // Store events for sorting
  statsEventsData = events;
  
  // Update count
  if (countEl) countEl.textContent = events.length;

  // Sort events
  const sortedEvents = sortEvents(events, currentSortColumn, currentSortDirection);

  let html = '';
  for (const event of sortedEvents) {
    const user = await promiseUserById(event.MainUserID);
    const userName = user ? `${user.FirstName} ${user.LastName}` : 'Unknown';
    const status = getEventStatus(event);
    const statusBadge = `<span class="badge ${status.badgeClass} badge-sm">${status.label}</span>`;
    
    const dateStr = new Date(event.StartDate).toLocaleDateString('th-TH', {
      day: 'numeric',
      month: 'short',
      year: 'numeric'
    });

    html += `<tr class="hover cursor-pointer" onclick="openEventModal(${event.Id})">
      <td class="font-medium">${event.Title || 'Untitled'}</td>
      <td>${dateStr}</td>
      <td>${userName}</td>
      <td>${statusBadge}</td>
    </tr>`;
  }

  tbody.innerHTML = html || '<tr><td colspan="4" class="text-center text-base-content/50">ไม่มีข้อมูล</td></tr>';
  
  // Update sort icons
  updateSortIcons();
}

function sortEvents(events, column, direction) {
  const sorted = [...events].sort((a, b) => {
    let valueA, valueB;
    
    switch (column) {
      case 'title':
        valueA = (a.Title || '').toLowerCase();
        valueB = (b.Title || '').toLowerCase();
        break;
      case 'date':
        valueA = new Date(a.StartDate).getTime();
        valueB = new Date(b.StartDate).getTime();
        break;
      case 'user':
        valueA = a.MainUserID || 0;
        valueB = b.MainUserID || 0;
        break;
      case 'status':
        valueA = getEventStatusOrder(a);
        valueB = getEventStatusOrder(b);
        break;
      default:
        return 0;
    }
    
    if (valueA < valueB) return direction === 'asc' ? -1 : 1;
    if (valueA > valueB) return direction === 'asc' ? 1 : -1;
    return 0;
  });
  
  return sorted;
}

function getEventStatusOrder(event) {
  const now = new Date();
  const start = new Date(event.StartDate);
  const end = new Date(event.EndDate);
  
  if (now < start) return 1; // กำลังจะมา
  if (now >= start && now <= end) return 2; // นัดหมาย
  if (event.Report && event.Report.trim()) return 4; // เสร็จสิ้น
  return 3; // ต้องการ Report
}

function sortEventsTable(column) {
  if (currentSortColumn === column) {
    // Toggle direction
    currentSortDirection = currentSortDirection === 'asc' ? 'desc' : 'asc';
  } else {
    currentSortColumn = column;
    currentSortDirection = column === 'date' ? 'desc' : 'asc';
  }
  
  // Re-render table
  renderRecentEventsTable(statsEventsData);
}

function updateSortIcons() {
  const columns = ['title', 'date', 'user', 'status'];
  columns.forEach(col => {
    const icon = document.getElementById(`sortIcon${col.charAt(0).toUpperCase() + col.slice(1)}`);
    if (icon) {
      if (col === currentSortColumn) {
        icon.className = `fas fa-sort-${currentSortDirection === 'asc' ? 'up' : 'down'} text-primary ml-1`;
      } else {
        icon.className = 'fas fa-sort text-base-content/30 ml-1';
      }
    }
  });
}

// Load saved theme
(function () {
  const savedTheme = localStorage.getItem("theme") || "light";
  document.documentElement.setAttribute("data-theme", savedTheme);
})();
