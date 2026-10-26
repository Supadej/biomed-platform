function login() {
    var username = document.getElementById('username').value;
    var password = document.getElementById('password').value;

    sendLoginRequest(username, password, function(error, token) {
        if (error === null) {
           //xalert(token, 0, -1); // Successful scenario
         setTimeout(function() {
            window.location.href = 'index.html';
         }, 2000);
        } else if (error.message === "Incorrect Username/Password") {
           xalert(error.message, 2, null); // Warning scenario
        } else {
           xalert(error.status + "-" + error.message, 1, null); // Error scenario
        }
    });
}