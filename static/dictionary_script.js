document.addEventListener("DOMContentLoaded", function() {
    var wordInput = document.getElementById("word");
    var lookupButton = document.getElementById("lookup-button");
    var nWords = document.getElementById("n-words");

    wordInput.addEventListener("keyup", function() {
        var input = document.getElementById("word").value;
        lookupButton.disabled = !input;
    });

    function lookupWord() {
        lookupButton.disabled = true;
        var word = document.getElementById("word").value.trim();
        var requestUrl = '/lookup';
        fetch(requestUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({word: word}),
            credentials: 'same-origin' // Include cookies in the request
        })
        .then(response => response.json())
        .then(data => {
            document.getElementById("word").value = ''; // Clear the input field
            document.getElementById("message").innerText = data.message;
            var definitionsDiv = document.getElementById("definitions");
            definitionsDiv.innerHTML = ''; // Clear previous definitions

            // Show the definitions, separated by part of speech (e.g. Noun, Verb, Adjective)
            if (data.definition) {
                for (var partOfSpeech in data.definition) {
                    var definitions = data.definition[partOfSpeech];

                    var posDiv = document.createElement("div");
                    posDiv.className = "part-of-speech";
                    posDiv.innerText = partOfSpeech;
                    definitionsDiv.appendChild(posDiv);

                    var list = document.createElement("ol");
                    definitionsDiv.appendChild(list);
                    definitions.forEach(definition => {
                        var listItem = document.createElement("li");
                        listItem.innerText = definition;
                        list.appendChild(listItem);
                    });
                }
            }
        })
        .catch((error) => {
            console.error('Error:', error);
        });
    };

    function logout() {
        fetch('/logout', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'same-origin' // Include cookies in the request
        })
        .then(response => response.json())
        .then(response => {
            if (response.logged_out) {
                // Redirect to login page if logout was successful
                window.location.href = '/';
            } else {
                console.error('Logout failed');
            }
        })
        .catch((error) => {
            console.error('Error:', error);
        });
    }

    lookupButton.addEventListener("click", lookupWord);
    document.getElementById('logout-button').addEventListener("click", logout);

    function checkForWords() {
        fetch('/check', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'same-origin' 
        })
        .then(response => response.json())
        .then(response => {
            if (response.revision_time) {
                // If it's time to revise, enable the revise button
                document.getElementById('revise-button').disabled = false;
                nWords.innerHTML = 'You have words to revise!'
            } 
        });
    }
    checkForWords()
});