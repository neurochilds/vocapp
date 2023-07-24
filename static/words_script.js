document.addEventListener("DOMContentLoaded", function() {

    async function emailPreference() {
        let preference;
        await fetch('/emailpreference', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'same-origin' 
        })
        .then(response => response.json())
        .then(data => {
            if (!data.error) {
                preference = data.preference;
            } 
            else {
                console.log(data.error);
            }
        });
        return preference;
    }

    
    emailPreference().then(preference => {
        let message = ''
        let wants_emails = preference
        if (wants_emails) {
            message = 'You are subscribed to email updates';
        } else {
            message = 'You are not subscribed to email updates';
        }
        document.getElementById('email-preference').innerHTML = message;
    });




    document.getElementById('change-preference').addEventListener('click', changePreference);

    var elements = Array.from(document.getElementsByClassName('delete-button'));

    elements.forEach(element => {
        element.addEventListener('click', function() {
            deleteWord(element);
        })
    })

    function deleteWord(button) {
        let word = button.value;

        fetch('/delete', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({word: word}),
            credentials: 'same-origin' 
        })
        .then(response => response.json())
        .then(response => {
        if (response.delete_successful) {
            window.location.reload();
        } else {
            console.log(response.error)
        }})
    }

    function changePreference() {

        fetch('/changepreference', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            credentials: 'same-origin' 
        })
        .then(response => response.json())
        .then(response => {
        if (response.change_successful) {
            window.location.reload();
        } else {
            console.log(response.error)
        }})
    }
});