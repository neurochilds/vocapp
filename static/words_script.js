document.addEventListener("DOMContentLoaded", function() {

    var elements = Array.from(document.getElementsByClassName('delete-button'));

    elements.forEach(element => {
        element.addEventListener('click', function() {
            console.log('Adding function to', element.value, 'delete button')
            deleteWord(element);
        })
    })

    function deleteWord(button) {
        let word = button.value;
        console.log(typeof(word))

        fetch('/delete', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({word: word}),
            credentials: 'same-origin' // Include cookies in the request
        })
        .then(response => response.json())
        .then(response => {
        if (response.delete_successful) {
            window.location.reload();
        } else {
            console.log(response.error)
        }})
    }});