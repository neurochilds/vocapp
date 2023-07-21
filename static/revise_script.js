document.addEventListener("DOMContentLoaded", function() {
    async function getWords() {
        let words;
        await fetch('/getwords', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'same-origin' 
        })
        .then(response => response.json())
        .then(data => {
            if (data.words) {
                words = data.words;
            } 
            else {
                console.log('No words found.');
            }
        });
        return words;
    }

    function sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    var wordDefinitionDiv = document.getElementById("word-definition");
    var userAnswerInput = document.getElementById("user-answer");
    var getWordButton = document.getElementById('get-word');
    var submitAnswerButton = document.getElementById("submit-answer");
    var messageDiv = document.getElementById("message");
    var nWords = document.getElementById("n-words");
    var currentWordIndex = 0;
    var words;

    submitAnswerButton.disabled = true;

    userAnswerInput.addEventListener("keyup", function() {
        var input = document.getElementById("user-answer").value;
        if (input && nWords) {
            submitAnswerButton.disabled = false;
        } else {
            submitAnswerButton.disabled = true;
        }
    });

    getWords().then(receivedWords => {
        words = receivedWords
        nWords.innerHTML = (words.length - currentWordIndex) + ' words to revise'
    });

    function getWord() {
        // Clear previous definition
        getWordButton.disabled = true;
        wordDefinitionDiv.innerHTML = "";
        messageDiv.innerHTML = "<br>";

        // Get the current word object
        var currentWord = words[currentWordIndex];
        if (!currentWord) {
            console.log('No more words left!');
            getWordButton.disabled = true;
            return;
        }

        messageDiv.innerHTML = currentWord.word.length + ' letters'

        var definitionsPOS = JSON.parse(currentWord.definition)

        // Iterate through the definitions
        for (var partOfSpeech in definitionsPOS) {
            var definitions = definitionsPOS[partOfSpeech];

            var posDiv = document.createElement("div");
            posDiv.className = "part-of-speech";
            posDiv.innerText = partOfSpeech;
            wordDefinitionDiv.appendChild(posDiv);

            var list = document.createElement("ol");
            wordDefinitionDiv.appendChild(list);

            definitions.forEach(meaning => {
            var listItem = document.createElement("li");
            listItem.innerText = meaning;
            list.appendChild(listItem);
            });
        }
    }

    // Function to check the user's answer
    async function checkAnswer() {
        // Disable the ability to submit an answer until a new word definition is fetched
        submitAnswerButton.disabled = true;

        // Unless this is the last word, reenable the getWordButton 
        if (nWords) {getWordButton.disabled = false};

        var is_correct = false;
        var currentWordObj = words[currentWordIndex];
        var currentWord = currentWordObj.word.toLowerCase();
        var userAnswer = userAnswerInput.value.trim().toLowerCase();

        var match = false;

        // Check if words are perfect match
        if (currentWord == userAnswer) {
            console.log('perfect match');
            match = true;

        // Else, compare if they'd match as singular nouns
        } else { 
            var singularCurrentWord = nlp(currentWord).nouns().toSingular().out('text');
            var singularUserAnswer = nlp(userAnswer).nouns().toSingular().out('text');
            if (singularCurrentWord && (singularCurrentWord == singularUserAnswer)) {
                console.log('singular match')
                match = true;

            // Else, compare if they'd match as infinitive verbs
            } else {
                var infinitiveCurrentWord = nlp(currentWord).verbs().toInfinitive().out('text');
                var infinitiveUserAnswer = nlp(userAnswer).verbs().toInfinitive().out('text');
                if (infinitiveCurrentWord && (infinitiveCurrentWord == infinitiveUserAnswer)) {
                    console.log('infintive match')
                    match = true;
                }
            }
        }
    
        // Compare the user's answer with the correct word
        if (match) {
            is_correct = true;
            messageDiv.innerHTML = "Correct! The word was '" + currentWord + "'. Well done!";
        } else {
            messageDiv.innerHTML = "Oops! The correct word was '" + currentWord + "'. You said '" + userAnswer + "'.";
        }

        // Update the SQL database depending on whether word was correct or not.
        update(currentWordObj.word, currentWordObj.user_id, currentWordObj.box_number, is_correct);
    
        // Move to the next word
        currentWordIndex++;

        nWords.innerHTML = (words.length - currentWordIndex) + ' words to revise'
    
        // Check if all words have been tested
        if (currentWordIndex == words.length) {
            getWordButton.disabled = true;
            await sleep(3000); // Wait 2 seconds to ensure the user had time to read the correct/incorrect message
            messageDiv.innerHTML = "That's all for now!";
            wordDefinitionDiv.innerHTML = "";
        }
        // Clear the user's answer
        userAnswerInput.value = "";
    }

    function update(word, userId, currentBox, isCorrect) {
        // The '/update' endpoint updates the box_number, last_reviewed_date, and next_review_date in the SQL database, depending on whether answer was correct or not.
        var requestUrl = '/update';

        console.log(typeof(word), typeof(userId), typeof(currentBox), typeof(isCorrect))
      
        fetch(requestUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            word: word,
            user_id: userId,
            current_box: currentBox,
            is_correct: isCorrect
          }),
          credentials: 'same-origin' // Include cookies in the request
        })
    }


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

    // Add event listeners to buttons
    submitAnswerButton.addEventListener("click", checkAnswer);
    document.getElementById('logout-button').addEventListener("click", logout);
    getWordButton.addEventListener("click", getWord);
});