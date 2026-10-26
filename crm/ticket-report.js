function getTicketById() {
    const urlParams = new URLSearchParams(window.location.search);
    const ticketId = urlParams.get('id');

    if (!ticketId) {
        console.error('Ticket ID not found in URL parameters.');
        return;
    }

    const xhr = new XMLHttpRequest();
    const url = `/biomedapi/v2/helpdesk/ticket/${parseRandomStringToInt(ticketId)}`;

    xhr.open('GET', url, true);

    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4) {
            if (xhr.status === 200) {
                console.log('Response:', xhr.responseText);
                const ticket = JSON.parse(xhr.responseText);const creator=ticket.CreatedBy||{},assigned=ticket.AssignedTo||{};ticket.MainContact=ticket.Contact?.Name||'';ticket.Instrumental=ticket.Instumental||'';ticket.CreatedByImg=creator.ProfilePic||'';ticket.CreatedByPosition=creator.Position||'';ticket.CreatedBy=[creator.FirstName,creator.LastName].filter(Boolean).join(' ');ticket.AssignedToImg=assigned.ProfilePic||'';ticket.AssignedToPosition=assigned.Position||'';ticket.AssignedTo=[assigned.FirstName,assigned.LastName].filter(Boolean).join(' ');

                // Map the data to HTML elements
                document.getElementById('ticketId').textContent = ticket.Id;
                document.getElementById('ticketTitle').textContent = ticket.Title;
                document.getElementById('ticketProblem').textContent = ticket.Problem;
                document.getElementById('ticketSolution').textContent = ticket.Solution;
                document.getElementById('ticketMaincontact').value = ticket.MainContact;
                document.getElementById('ticketInstrumental').value = ticket.Instrumental;
                document.getElementById('ticketModel').value = ticket.Model;
                document.getElementById('ticketSerialNumber').value = ticket.SerialNumber;
                document.getElementById('createdDate').textContent = new Date(ticket.CreatedDate).toLocaleString();
                document.getElementById('updateDate').textContent = new Date(ticket.LastUpdate).toLocaleString();
                document.getElementById('requesterImg').src = ticket.CreatedByImg == ""?  'assets/profile-user.png':"./assets/profile/"+ticket.CreatedByImg+".jpg";
                document.getElementById('requesterName').textContent = ticket.CreatedBy;
                document.getElementById('requesterPosition').textContent = ticket.CreatedByPosition;
                document.getElementById('reponsibleImg').src = ticket.AssignedToImg ==""?  'assets/profile-user.png': "./assets/profile/"+ ticket.AssignedToImg+".jpg";
                document.getElementById('reponsibleName').textContent = ticket.AssignedTo==""? "Not assigned": ticket.AssignedTo;
                document.getElementById('responsiblePosition').textContent = ticket.AssignedToPosition == ""? "Not assigned": ticket.AssignedToPosition;

                // Update the status badge
                const statusBadge = document.querySelector('.badge');
                statusBadge.textContent = ticket.Status;

            } else {
                console.error('Error fetching ticket:', xhr.statusText);
                alert('Error fetching ticket. Please check the URL and try again.');
            }
        }
    };

    xhr.send();
}

getTicketById();