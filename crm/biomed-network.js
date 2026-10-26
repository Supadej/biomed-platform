/**
 * Biomed Network Visualization using Sigma.js (WebGL)
 * Replaces D3.js SVG for better performance with large graphs
 * 
 * Supports same URL parameters as original:
 * - ?type=Users|Contacts|Events|Leads|Activities|Tickets
 * - ?id=<number>
 */

// Get URL parameters (same as original)
const urlParams = new URLSearchParams(window.location.search);
const id = urlParams.get('id');
const type = urlParams.get('type');

// Global state
let sigmaInstance = null;
let graph = null;
let isLayoutRunning = false;
let layoutAnimationFrame = null;
let filtered = false;

// Color scale (same as D3 version)
const colorScale = {
    "User": "#FFD700",
    "Event": "#A9DFBF", 
    "Lead": "#F9AFAF",
    "Activity": "#F7DC6F",
    "Ticket": "#D2B4DE",
    "Contact": "#FFB6A7"
};

// Size scale based on node type
const sizeScale = {
    "User": 5,
    "Contact": 5,
    "Event": 6,
    "Activity": 8,
    "Ticket": 8,
    "Lead": 10
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    let processedNodeData = JSON.parse(sessionStorage.getItem('processedNodeData'));
    
    if (processedNodeData) {
        console.log("Using cached data");
        initializeGraph(processedNodeData);
    } else {
        console.log("Requesting data from server");
        fetchData();
    }
});

// Fetch data from API
function fetchData() {
    const xhr = new XMLHttpRequest();
    const token = readToken();
    
    xhr.open("GET", url + "/biomedapi/visualization", true);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.setRequestHeader("Authorization", `Bearer ${token}`);
    
    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4) {
            if (xhr.status === 200) {
                const response = JSON.parse(xhr.responseText);
                console.log("API Response:", response);
                
                let processedNodeData = preprocessing(response);
                console.log("Processed Data:", processedNodeData);
                
                sessionStorage.setItem('processedNodeData', JSON.stringify(processedNodeData));
                initializeGraph(processedNodeData);
            } else {
                hideLoading();
                xalert("Failed to fetch visualization data", 1, null);
            }
        }
    };
    
    xhr.send();
}

// Initialize graph with data
function initializeGraph(data) {
    // Check if we need to filter
    const validTypes = ["Users", "Contacts", "Events", "Leads", "Activities", "Tickets"];
    const normalizedType = type ? type.charAt(0).toUpperCase() + type.slice(1).toLowerCase() : null;
    
    if (id && !isNaN(parseInt(id)) && validTypes.includes(normalizedType)) {
        data = Filter(data, normalizedType, parseInt(id));
        filtered = true;
        console.log("Filtered Mode:", normalizedType, id);
        
        // Show filter info
        document.getElementById('filterInfo').classList.remove('hidden');
        document.getElementById('filterText').textContent = `Filtered view: ${normalizedType} #${id}`;
        document.getElementById('viewMode').textContent = `${normalizedType} #${id}`;
    } else {
        console.log("All Mode");
        document.getElementById('viewMode').textContent = 'All Data';
    }
    
    renderGraph(data);
}

// Filter function (same logic as D3 version)
function Filter(data, filterType, filterId) {
    const singularMap = {
        "Users": "User",
        "Contacts": "Contact",
        "Events": "Event",
        "Leads": "Lead",
        "Activities": "Activity",
        "Tickets": "Ticket"
    };
    
    const startType = singularMap[filterType];
    const startIdType = filterId.toString() + "-" + startType;
    
    // Build nodes map
    const nodesMap = {};
    data.nodes.forEach(node => {
        node.idType = node.id.toString() + "-" + node.type;
        nodesMap[node.idType] = node;
    });
    
    // Mark start node
    if (nodesMap[startIdType]) {
        nodesMap[startIdType].isStart = true;
    }
    
    // Build adjacency list
    const adjacency = {};
    data.links.forEach(link => {
        const originIdType = link.origin.id.toString() + "-" + link.origin.type;
        const destIdType = link.destination.id.toString() + "-" + link.destination.type;
        
        if (!adjacency[originIdType]) adjacency[originIdType] = [];
        if (!adjacency[destIdType]) adjacency[destIdType] = [];
        
        adjacency[originIdType].push(destIdType);
        adjacency[destIdType].push(originIdType);
    });
    
    // BFS traversal
    const visited = new Set();
    const queue = [];
    visited.add(startIdType);
    queue.push(startIdType);
    
    while (queue.length) {
        const current = queue.shift();
        if (adjacency[current]) {
            adjacency[current].forEach(neighbor => {
                if (!visited.has(neighbor)) {
                    visited.add(neighbor);
                    const neighborType = nodesMap[neighbor]?.type;
                    // Don't expand from User or Contact nodes (unless it's the start)
                    if (neighbor !== startIdType && (neighborType === "User" || neighborType === "Contact")) {
                        // Do not enqueue
                    } else {
                        queue.push(neighbor);
                    }
                }
            });
        }
    }
    
    // Filter nodes
    const resultNodes = [];
    visited.forEach(idType => {
        if (nodesMap[idType]) resultNodes.push(nodesMap[idType]);
    });
    
    // Filter links
    const resultLinks = data.links.filter(link => {
        const originIdType = link.origin.id.toString() + "-" + link.origin.type;
        const destIdType = link.destination.id.toString() + "-" + link.destination.type;
        return visited.has(originIdType) && visited.has(destIdType);
    });
    
    return { nodes: resultNodes, links: resultLinks };
}

// Preprocessing function (same logic as D3 version)
function preprocessing(data) {
    const nodes = [];
    const links = [];
    
    // Process Users
    if (data.Users) {
        data.Users.forEach(user => {
            nodes.push({
                id: user.Id.toString(),
                type: "User",
                name: "User: " + user.FirstName + (user.LastName ? " " + user.LastName : "") + (user.Position ? " (" + user.Position + ")" : "")
            });
        });
    }
    
    // Process Contacts
    if (data.Contacts) {
        data.Contacts.forEach(contact => {
            nodes.push({
                id: contact.Id.toString(),
                type: "Contact",
                name: "Contact: " + contact.Name
            });
        });
    }
    
    // Process Events
    if (data.Events) {
        data.Events.forEach(event => {
            nodes.push({
                id: event.Id.toString(),
                type: "Event",
                name: "Event: " + event.Title
            });
        });
    }
    
    // Process Leads
    if (data.Leads) {
        data.Leads.forEach(lead => {
            nodes.push({
                id: lead.Id.toString(),
                type: "Lead",
                name: "Lead: " + lead.LeadName
            });
        });
    }
    
    // Process Activities
    if (data.Activities) {
        data.Activities.forEach(activity => {
            nodes.push({
                id: activity.Id.toString(),
                type: "Activity",
                name: "Activity: " + activity.Name
            });
        });
    }
    
    // Process Tickets
    if (data.Tickets) {
        data.Tickets.forEach(ticket => {
            nodes.push({
                id: ticket.Id.toString(),
                type: "Ticket",
                name: "Ticket: " + ticket.Title
            });
        });
    }
    
    // Create links from Leads
    if (data.Leads) {
        data.Leads.forEach(lead => {
            if (lead.MainUserId) {
                links.push({
                    origin: { id: lead.Id.toString(), type: "Lead" },
                    destination: { id: lead.MainUserId.toString(), type: "User" }
                });
            }
            if (lead.MainCustomerId) {
                links.push({
                    origin: { id: lead.Id.toString(), type: "Lead" },
                    destination: { id: lead.MainCustomerId.toString(), type: "Contact" }
                });
            }
        });
    }
    
    // Create links from Tickets
    if (data.Tickets) {
        data.Tickets.forEach(ticket => {
            if (ticket.ContactId) {
                links.push({
                    origin: { id: ticket.Id.toString(), type: "Ticket" },
                    destination: { id: ticket.ContactId.toString(), type: "Contact" }
                });
            }
            if (ticket.AssignedToUserId) {
                links.push({
                    origin: { id: ticket.Id.toString(), type: "Ticket" },
                    destination: { id: ticket.AssignedToUserId.toString(), type: "User" }
                });
            }
            if (ticket.CreatedByUserId) {
                links.push({
                    origin: { id: ticket.Id.toString(), type: "Ticket" },
                    destination: { id: ticket.CreatedByUserId.toString(), type: "User" }
                });
            }
        });
    }
    
    // Create links from Events
    if (data.Events) {
        data.Events.forEach(event => {
            if (event.MainUserID) {
                links.push({
                    origin: { id: event.Id.toString(), type: "Event" },
                    destination: { id: event.MainUserID.toString(), type: "User" }
                });
            }
            if (event.MainContactID) {
                links.push({
                    origin: { id: event.Id.toString(), type: "Event" },
                    destination: { id: event.MainContactID.toString(), type: "Contact" }
                });
            }
        });
    }
    
    // Create links from Activities
    if (data.Activities) {
        data.Activities.forEach(activity => {
            if (activity.MainUserId) {
                links.push({
                    origin: { id: activity.Id.toString(), type: "Activity" },
                    destination: { id: activity.MainUserId.toString(), type: "User" }
                });
            }
        });
    }
    
    // Process additional link tables
    const propTypeMapping = {
        LeadId: "Lead",
        UserId: "User",
        EventId: "Event",
        ActivityId: "Activity",
        TicketId: "Ticket",
        HelpdeskTicketId: "Ticket",
        ContactId: "Contact"
    };
    
    const nodeKeys = ["Users", "Events", "Leads", "Activities", "Tickets", "Contacts"];
    
    Object.keys(data).forEach(key => {
        if (!nodeKeys.includes(key)) {
            data[key].forEach(item => {
                const itemKeys = Object.keys(item);
                if (itemKeys.length >= 2) {
                    const originKey = itemKeys[0];
                    const destKey = itemKeys[1];
                    if (propTypeMapping[originKey] && propTypeMapping[destKey]) {
                        links.push({
                            origin: { id: item[originKey].toString(), type: propTypeMapping[originKey] },
                            destination: { id: item[destKey].toString(), type: propTypeMapping[destKey] }
                        });
                    }
                }
            });
        }
    });
    
    return { nodes, links };
}

// Render graph using Sigma.js
function renderGraph(data) {
    const container = document.getElementById('sigma-container');
    
    // Create Graphology graph
    graph = new graphology.Graph();
    
    // Add nodes with random initial positions
    data.nodes.forEach(node => {
        const nodeId = `${node.id}-${node.type}`;
        const angle = Math.random() * 2 * Math.PI;
        const radius = Math.random() * 100;
        
        graph.addNode(nodeId, {
            label: node.name,
            x: Math.cos(angle) * radius,
            y: Math.sin(angle) * radius,
            size: sizeScale[node.type] || 5,
            color: colorScale[node.type] || "#999999",
            nodeType: node.type,  // Use nodeType instead of type (type is reserved by Sigma for node program)
            originalId: node.id,
            isStart: node.isStart || false
        });
    });
    
    // Add edges
    data.links.forEach((link, index) => {
        const sourceId = `${link.origin.id}-${link.origin.type}`;
        const targetId = `${link.destination.id}-${link.destination.type}`;
        
        if (graph.hasNode(sourceId) && graph.hasNode(targetId)) {
            try {
                graph.addEdge(sourceId, targetId, {
                    size: 1,
                    color: "#e0e0e0"
                });
            } catch (e) {
                // Edge might already exist (parallel edges)
            }
        }
    });
    
    // Update stats
    document.getElementById('nodeCount').textContent = graph.order;
    document.getElementById('edgeCount').textContent = graph.size;
    
    // Create Sigma instance
    sigmaInstance = new Sigma(graph, container, {
        minCameraRatio: 0.1,
        maxCameraRatio: 10,
        renderEdgeLabels: false,
        defaultNodeColor: "#999999",
        defaultEdgeColor: "#e0e0e0",
        labelDensity: 0.07,
        labelGridCellSize: 60,
        labelRenderedSizeThreshold: 6,
        labelFont: "Noto Sans Thai, sans-serif",
        labelSize: 12,
        labelWeight: "normal"
    });
    
    // Highlight start node if filtered
    if (filtered) {
        graph.forEachNode((node, attrs) => {
            if (attrs.isStart) {
                graph.setNodeAttribute(node, 'size', attrs.size * 2);
                graph.setNodeAttribute(node, 'highlighted', true);
            }
        });
    }
    
    // Node hover behavior - highlight neighbors
    let highlightedNodes = new Set();
    let highlightedEdges = new Set();
    
    sigmaInstance.on('enterNode', ({ node }) => {
        highlightedNodes = new Set([node]);
        highlightedEdges = new Set();
        
        // Get neighbors
        graph.forEachNeighbor(node, (neighbor) => {
            highlightedNodes.add(neighbor);
        });
        
        // Get connected edges
        graph.forEachEdge(node, (edge) => {
            highlightedEdges.add(edge);
        });
        
        // Show tooltip
        const attrs = graph.getNodeAttributes(node);
        const tooltip = document.getElementById('node-tooltip');
        tooltip.innerHTML = `<strong>${attrs.label}</strong><br><span class="text-xs opacity-60">${attrs.nodeType}</span>`;
        tooltip.style.display = 'block';
        
        // Apply highlighting
        sigmaInstance.setSetting('nodeReducer', (n, data) => {
            if (highlightedNodes.has(n)) {
                return { ...data, color: data.color, zIndex: 1 };
            }
            return { ...data, color: "#f0f0f0", zIndex: 0 };
        });
        
        sigmaInstance.setSetting('edgeReducer', (edge, data) => {
            if (highlightedEdges.has(edge)) {
                return { ...data, color: "#999999", size: 2 };
            }
            return { ...data, color: "#f8f8f8", size: 0.5 };
        });
    });
    
    sigmaInstance.on('leaveNode', () => {
        highlightedNodes = new Set();
        highlightedEdges = new Set();
        
        document.getElementById('node-tooltip').style.display = 'none';
        
        sigmaInstance.setSetting('nodeReducer', null);
        sigmaInstance.setSetting('edgeReducer', null);
    });
    
    // Move tooltip with mouse
    container.addEventListener('mousemove', (e) => {
        const tooltip = document.getElementById('node-tooltip');
        if (tooltip.style.display === 'block') {
            tooltip.style.left = (e.offsetX + 15) + 'px';
            tooltip.style.top = (e.offsetY + 15) + 'px';
        }
    });
    
    // Double-click to navigate (same URLs as D3 version)
    sigmaInstance.on('doubleClickNode', ({ node }) => {
        const attrs = graph.getNodeAttributes(node);
        let targetUrl = "";
        
        switch (attrs.nodeType) {
            case "Event":
                targetUrl = "./event.html?id=" + attrs.originalId;
                break;
            case "Lead":
                targetUrl = "./crm-detail.html?leadid=" + attrs.originalId;
                break;
            case "Ticket":
                targetUrl = "./helpdesk-detail.html?leadid=" + attrs.originalId;
                break;
            case "Activity":
                targetUrl = "./project-activity.html?activityid=" + attrs.originalId;
                break;
            default:
                return;
        }
        
        window.open(targetUrl, "_blank");
    });
    
    // Enable node dragging
    let draggedNode = null;
    let isDragging = false;
    
    sigmaInstance.on('downNode', (e) => {
        isDragging = true;
        draggedNode = e.node;
        graph.setNodeAttribute(draggedNode, 'highlighted', true);
    });
    
    sigmaInstance.getMouseCaptor().on('mousemovebody', (e) => {
        if (!isDragging || !draggedNode) return;
        
        // Get new position
        const pos = sigmaInstance.viewportToGraph(e);
        graph.setNodeAttribute(draggedNode, 'x', pos.x);
        graph.setNodeAttribute(draggedNode, 'y', pos.y);
        
        // Prevent camera from moving
        e.preventSigmaDefault();
        e.original.preventDefault();
        e.original.stopPropagation();
    });
    
    sigmaInstance.getMouseCaptor().on('mouseup', () => {
        if (draggedNode) {
            graph.removeNodeAttribute(draggedNode, 'highlighted');
        }
        isDragging = false;
        draggedNode = null;
    });
    
    // Hide loading
    hideLoading();
    
    // Auto-start layout for small graphs
    if (graph.order < 200) {
        setTimeout(() => toggleLayout(), 500);
    }
}

// Simple force-directed layout (lighter than full ForceAtlas2)
function toggleLayout() {
    if (isLayoutRunning) {
        stopLayout();
    } else {
        startLayout();
    }
}

function startLayout() {
    if (!graph || isLayoutRunning) return;
    
    isLayoutRunning = true;
    document.getElementById('layoutBtnText').textContent = 'Stop Layout';
    document.getElementById('toggleLayoutBtn').querySelector('i').className = 'fas fa-pause';
    
    // Simple force-directed algorithm
    const nodes = graph.nodes();
    const positions = {};
    
    nodes.forEach(node => {
        const mass = graph.getNodeAttribute(node, 'size') || 5;
        positions[node] = {
            x: graph.getNodeAttribute(node, 'x'),
            y: graph.getNodeAttribute(node, 'y'),
            vx: 0,
            vy: 0,
            mass: mass,
            degree: graph.degree(node)
        };
    });
    
    // Physics parameters
    let temperature = 100;  // Initial temperature for simulated annealing
    const gravity = 1;      // Center gravity
    const scalingRatio = 10;
    const edgeWeightInfluence = 1;
    const barnesHutTheta = 0.5;
    
    function tick() {
        if (!isLayoutRunning) return;
        
        const nodeCount = nodes.length;
        
        // Reset forces
        nodes.forEach(node => {
            positions[node].fx = 0;
            positions[node].fy = 0;
        });
        
        // 1. Gravity - pull nodes toward center
        const centerX = 0;
        const centerY = 0;
        nodes.forEach(node => {
            const pos = positions[node];
            const dx = centerX - pos.x;
            const dy = centerY - pos.y;
            const dist = Math.sqrt(dx * dx + dy * dy) || 1;
            
            // Gravity proportional to mass (degree + 1)
            const gravityForce = gravity * (pos.degree + 1);
            pos.fx += dx / dist * gravityForce;
            pos.fy += dy / dist * gravityForce;
        });
        
        // 2. Repulsion between all nodes (ForceAtlas2 style)
        for (let i = 0; i < nodeCount; i++) {
            const nodeA = nodes[i];
            const posA = positions[nodeA];
            
            for (let j = i + 1; j < nodeCount; j++) {
                const nodeB = nodes[j];
                const posB = positions[nodeB];
                
                const dx = posA.x - posB.x;
                const dy = posA.y - posB.y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                
                if (dist > 0) {
                    // ForceAtlas2: repulsion = k * (degree + 1) * (degree + 1) / distance
                    const repulsion = scalingRatio * (posA.degree + 1) * (posB.degree + 1) / dist;
                    
                    const fx = dx / dist * repulsion;
                    const fy = dy / dist * repulsion;
                    
                    posA.fx += fx;
                    posA.fy += fy;
                    posB.fx -= fx;
                    posB.fy -= fy;
                } else {
                    // If nodes overlap, push apart randomly
                    const angle = Math.random() * 2 * Math.PI;
                    posA.fx += Math.cos(angle) * scalingRatio;
                    posA.fy += Math.sin(angle) * scalingRatio;
                }
            }
        }
        
        // 3. Attraction along edges (spring force)
        graph.forEachEdge((edge, attrs, source, target) => {
            const posA = positions[source];
            const posB = positions[target];
            
            const dx = posB.x - posA.x;
            const dy = posB.y - posA.y;
            const dist = Math.sqrt(dx * dx + dy * dy) || 1;
            
            // ForceAtlas2: attraction = distance / (degree + 1)
            // Linlog mode: attraction = log(1 + distance)
            const attraction = dist / (Math.min(posA.degree, posB.degree) + 1);
            
            const fx = dx / dist * attraction;
            const fy = dy / dist * attraction;
            
            posA.fx += fx;
            posA.fy += fy;
            posB.fx -= fx;
            posB.fy -= fy;
        });
        
        // 4. Apply forces with temperature (simulated annealing)
        let totalSwing = 0;
        let totalEffectiveTraction = 0;
        
        nodes.forEach(node => {
            const pos = positions[node];
            
            // Calculate swing (how much the node oscillates)
            const forceNorm = Math.sqrt(pos.fx * pos.fx + pos.fy * pos.fy);
            const oldVelocityNorm = Math.sqrt(pos.vx * pos.vx + pos.vy * pos.vy);
            
            // Adaptive temperature per node
            const swinging = Math.abs(forceNorm - oldVelocityNorm);
            const effectiveTraction = (forceNorm + oldVelocityNorm) / 2;
            
            totalSwing += (pos.degree + 1) * swinging;
            totalEffectiveTraction += (pos.degree + 1) * effectiveTraction;
            
            // Speed limit based on node degree
            const speedLimit = 10 / (pos.degree + 1);
            
            // Apply force with damping
            let speed = temperature * forceNorm / (1 + Math.sqrt(temperature * swinging));
            speed = Math.min(speed, speedLimit);
            
            if (forceNorm > 0) {
                pos.vx = pos.fx / forceNorm * speed;
                pos.vy = pos.fy / forceNorm * speed;
            }
            
            pos.x += pos.vx;
            pos.y += pos.vy;
            
            graph.setNodeAttribute(node, 'x', pos.x);
            graph.setNodeAttribute(node, 'y', pos.y);
        });
        
        // Adapt temperature (simulated annealing)
        if (totalEffectiveTraction > 0) {
            const targetSpeed = totalSwing / totalEffectiveTraction;
            if (targetSpeed > 1) {
                temperature *= 0.9;  // Cool down if oscillating too much
            } else {
                temperature *= 1.01; // Heat up slightly if stable
            }
        }
        temperature = Math.max(0.1, Math.min(temperature, 100));
        
        // Stop if converged
        const avgMovement = nodes.reduce((sum, node) => {
            const pos = positions[node];
            return sum + Math.sqrt(pos.vx * pos.vx + pos.vy * pos.vy);
        }, 0) / nodeCount;
        
        if (avgMovement < 0.05 || temperature < 0.2) {
            stopLayout();
            return;
        }
        
        layoutAnimationFrame = requestAnimationFrame(tick);
    }
    
    tick();
}

function stopLayout() {
    isLayoutRunning = false;
    if (layoutAnimationFrame) {
        cancelAnimationFrame(layoutAnimationFrame);
        layoutAnimationFrame = null;
    }
    document.getElementById('layoutBtnText').textContent = 'Start Layout';
    document.getElementById('toggleLayoutBtn').querySelector('i').className = 'fas fa-play';
}

function resetCamera() {
    if (sigmaInstance) {
        sigmaInstance.getCamera().animate({ x: 0.5, y: 0.5, ratio: 1 }, { duration: 300 });
    }
}

function hideLoading() {
    const loader = document.getElementById('loading-overlay');
    if (loader) {
        loader.style.display = 'none';
    }
}
