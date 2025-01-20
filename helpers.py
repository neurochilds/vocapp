from datetime import datetime, timedelta
from mailjet_rest import Client
from apscheduler.schedulers.background import BackgroundScheduler
from models import engine, Word, User
from sqlmodel import Session, select, distinct
import os


def start_email_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(email_if_revision_due, 'interval', hours=24) 
    scheduler.start()


def email_if_revision_due():
    print('checking if emails due')
    with Session(engine) as session:
        user_ids = session.exec(select(distinct(Word.user_id)).where(Word.next_review_date < datetime.utcnow())).all()
        if user_ids:
            for user_id in user_ids:
                user = session.exec(select(User).where(User.id == user_id)).first()
                if user.wants_updates:
                    email = user.username

                    text_content = '''
                    Hello!\n\n
                    You have words to revise on Vocapp!\n\n
                    Best,\n
                    Vocapp
                    '''

                    html_content = '''
                    <html>
                    <body>
                        <p>Hello!</p>
                        <p>You have words to revise on <a href="https://vocapp.tomchilds.com/" target="_blank">Vocapp</a>!</p>
                        <p>Best,<br>Vocapp</p>
                    </body>
                    </html>
                    '''

                    send_email(email, subject='Words to revise', text_content=text_content, html_content=html_content)


def send_email(recipient_email, subject, text_content, html_content):
    print('sending email to', recipient_email)
    api_key = os.getenv('API_KEY')
    api_secret = os.getenv('API_SECRET')  
    mailjet = Client(auth=(api_key, api_secret), version='v3.1')

    data = {
        'Messages': [
            {
                "From": {
                    "Email": "vocapp.reminder@gmail.com", 
                    "Name": "Vocapp"  
                },
                "To": [
                    {
                        "Email": recipient_email
                    }
                ],
                "Subject": subject,
                "TextPart": text_content,
                "HTMLPart": html_content
            }
        ]
    }
    return mailjet.send.create(data=data)


def clean_dict(response: tuple):
    ''''
    Formats the response from PyMultiDictionary to neatly show just the grammatical category and definitions.
    '''

    # Gets the grammatical category (e.g., Noun, Adjective, Verb)
    categories = ''
    for category in response[0]:
        categories += category + ' '
    
    # Forms a list of each definition
    definitions_list = []
    definitions = response[1].split('.')[:-1]
    for index, definition in enumerate(definitions):
        if index == 2:
            definitions_list.append(definition.split('is also', 1)[1].strip())
            break
        definitions_list.append(definition.split('is', 1)[1].strip())

    return {categories: definitions_list}


def update_box(current_box: int, is_correct: bool):
    '''
    Implements spaced-repetition algo.
    When words are correctly recalled from their definition, they are moved to the next box.
    When incorrectly recalled, they are moved to a lower box.
    The box they are in depends when they will next be reviewed.
    Words in higher boxes are demoted most, up to -5 boxes lower.
    Words in higher boxes have a greater interval until their next revision date, up to 56 days.
    '''

    # NEXT_INTERVAL[current_box] -> learn words in box[1] every 1 day, in box[10] every 56 days
    NEXT_INTERVAL = [None, 1, 2, 3, 5, 8, 12, 18, 28, 42, 56] 

    # REDUCE_BOX[current_box] -> if word in box 3 wrong, move it back to box 2 (-1); if word in box 10 wrong, move word back to box 5 (-5)
    REDUCE_BOX = [None, 0, -1, -1, -1, -2, -2, -3, -3, -4, -5] 

    if is_correct and current_box < 10:
        new_box = current_box + 1
    elif not is_correct: 
        new_box = current_box + REDUCE_BOX[current_box]
    else:
        # Current box does not change as it either cannot go any lower or higher
        new_box = current_box

    last_reviewed_date = datetime.utcnow()
    next_review_date = datetime.utcnow() + timedelta(days=NEXT_INTERVAL[new_box])

    return new_box, last_reviewed_date, next_review_date


def days_hours_mins(end: datetime, start: datetime, is_last: bool = False):
    '''
    Takes in two datetimes and return the difference as a string -> 'X days, Y hours, Z minutes'.
    '''
    td = (end - start)

    if td < timedelta(minutes=1):
        if is_last: return 'Just now'
        return 'Now!'
    
    time = {}
    time['days'] = td.days
    seconds = td.seconds
    time['hours'] = seconds // 3600
    time['minutes'] = (seconds // 60) % 60

    string = ''

    for unit in time.keys():
        if time[unit] > 0 or string: string += f'{time[unit]} {unit} '

    return string