from fastapi import FastAPI, Request, Depends, HTTPException, Response, Form
from auth import AuthHandler
from schemas import AuthDetails, WordDetails, DeleteWord
import string
from helpers import clean_dict, update_box, days_hours_mins, start_email_scheduler
from validate_email_address import validate_email

from models import User, Word, engine
from sqlmodel import SQLModel, Session, select
from starlette.status import HTTP_403_FORBIDDEN, HTTP_401_UNAUTHORIZED
from typing import Optional

from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import json
from PyDictionary import PyDictionary
from datetime import datetime, timedelta

'''
TO DO:
- Implement change email function
- Change secret key and API to environment variables, upload to railway.app
- Check it works with 1 min delay...if so, change to 24 hours
- Change all cases of 'username' to 'email'
'''



SQLModel.metadata.create_all(engine)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static") # mount static files
templates = Jinja2Templates(directory="templates")

dictionary = PyDictionary()
auth_handler = AuthHandler()

start_email_scheduler()


@app.exception_handler(HTTP_403_FORBIDDEN)
async def forbidden_exception_handler(request: Request, exc: HTTPException):
    # Redirect users to login page if they try to access url that requires valid token
    return RedirectResponse(url='/login')


@app.exception_handler(HTTP_401_UNAUTHORIZED)
async def forbidden_exception_handler(request: Request, exc: HTTPException):
    # Redirect users to login page if they try to access url that requires valid token
    return RedirectResponse(url='/login')


@app.get('/register', response_class=HTMLResponse)
def register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@app.post('/register', status_code=201)
def register(request: Request, username: str = Form(...), password: str = Form(...), confirm_password: str = Form(...), wants_updates: Optional[bool] = Form(False)):
    '''
    Passing AuthDetails as the param ensures that the recieved object matches our schema.
    If username is unique, adds new user to users.
    Displays error to user if username or password invalid.
    '''
    auth_details = AuthDetails(username=username, password=password)

    if password != confirm_password:
        error = "Passwords don't match"
        return templates.TemplateResponse("register.html", {"request": request, "error": error})


    with Session(engine) as session:
        user = session.exec(select(User).where(User.username == auth_details.username)).first()
        if user:
            error = 'Username already taken'
            return templates.TemplateResponse("register.html", {"request": request, "error": error})
        
        if not validate_email(username):
            error = 'Invalid email'
            return templates.TemplateResponse("register.html", {"request": request, "error": error})

        
        letter_missing = not any(ch.isalpha() for ch in password)
        number_missing = not any(ch.isdigit() for ch in password)
        special_char_missing = not any(ch in string.punctuation for ch in password)

        if len(password) < 8 or any([letter_missing, number_missing, special_char_missing]):
            error = 'Password must be at least 8 characters and contain at least one letter, number and special character'
            return templates.TemplateResponse("register.html", {"request": request, "error": error})

        hashed_password = auth_handler.get_password_hash(auth_details.password)

        user = User(username=auth_details.username, password_hash=hashed_password, wants_updates=wants_updates)
        session.add(user)
        session.commit()
    return RedirectResponse(url='/login', status_code=303)


@app.get('/login', response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post('/login')
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    '''
    Check user exists and retrieve hashed password.
    If user does not exist or password invliad, raise exception.
    Otherwise, encode token using username and return it.
    '''
    auth_details = AuthDetails(username=username, password=password)

    with Session(engine) as session:
        user = session.exec(select(User).where(User.username == auth_details.username)).first()
        if (not user) or (not auth_handler.verify_password(auth_details.password, user.password_hash)):
            error = 'Invalid username and/or password'
            return templates.TemplateResponse("login.html", {"request": request, "error": error})
        token = auth_handler.encode_token(user.username)

        response = RedirectResponse(url='/', status_code=303)
        response.set_cookie(key="access_token", value=f"Bearer {token}", httponly=True)

        auth_handler.decode_token(token)

        return response


@app.get('/')
def index(request: Request, username = Depends(auth_handler.auth_wrapper)):
    '''
    Adding a dependency on auth wrapper.
    This is called when endpoint is hit and ensures valid token has been passed in.
    If it passes, index.html is loaded.
    '''
    return templates.TemplateResponse("index.html", {"request": request, "username": username})
    

@app.post('/logout')
def logout(response: Response):
    '''
    Invalidate the current token by removing it from the client's cookies.
    Redirects the user to the login page.
    '''
    response.delete_cookie(key="access_token")
    return {'logged_out': True}


@app.post('/lookup')
async def lookup_word(request: Request, word: str = Form(...), username = Depends(auth_handler.auth_wrapper)):
    '''
    Look up the meaning of the word and add it to the user's word list.
    '''
    if len(word.split(' ')) > 1 or len(word.strip()) < 1:
        return {"word": word, "definition": None, "message": "Query must be a single word"}

    word = word.title()
    definition = dictionary.meaning(word)

    if definition == None:
        return {"word": word, "definition": None, "message": f"No results found for '{word}'"}
    
    # Limits to max 5 definitions per part of speech (e.g. per noun, verb, etc.)
    definition = clean_dict(definition)

    # Get the user's data
    with Session(engine) as session:
        user = session.exec(select(User).where(User.username == username)).first()

        # Check if the word is already in the user's word list
        existing_word = session.exec(select(Word).where(Word.word == word, Word.user_id == user.id)).first()
        if existing_word is not None:
            return {"word": word, "definition": definition, "message": f"'{word}' is already in your list!"}

        # Add the word to the user's word list
        new_word = Word(word=word, definition=json.dumps(definition), box_number=1, last_reviewed_date=datetime.utcnow(), next_review_date=(datetime.utcnow()+timedelta(days=1)), user_id=user.id)
        session.add(new_word)
        session.commit()

    return {"word": word, "definition": definition, "message": f"'{word}' added to your list!"}


@app.get('/check')
def check(username = Depends(auth_handler.auth_wrapper)):
    '''
    Checks database to see if any words are due for revision.
    '''
    with Session(engine) as session:
        user = session.exec(select(User).where(User.username == username)).first()
        if user:
            words = session.exec(select(Word).where(Word.user_id == user.id, Word.next_review_date < datetime.utcnow())).all()
            if words:
                return {'revision_time': True}
    return {'revision_time': False}


@app.get('/revise', response_class=HTMLResponse)
def revise(request: Request, username = Depends(auth_handler.auth_wrapper)):
    return templates.TemplateResponse("revise.html", {"request": request})


@app.get('/getwords')
def getwords(username = Depends(auth_handler.auth_wrapper)):
    '''
    Returns from the database all words that username is due to revise.
    '''
    with Session(engine) as session:
        user = session.exec(select(User).where(User.username == username)).first()
        if user:
            words = session.exec(select(Word).where(Word.user_id == user.id, Word.next_review_date < datetime.utcnow())).all()
    return {'words': [word.dict() for word in words]}


@app.post('/update')
def update(word_details: WordDetails):
    # Update database with new box_number, last_reviewed_date and next_review_date based on spaced-repetition algo 'update_box()'
    new_box, last_reviewed_date, next_review_date = update_box(word_details.current_box, word_details.is_correct)

    with Session(engine) as session:
        word_obj = session.exec(select(Word).where(Word.user_id == word_details.user_id, Word.word == word_details.word)).first()
        if word_obj is not None:
            word_obj.box_number = new_box
            word_obj.last_reviewed_date = last_reviewed_date
            word_obj.next_review_date = next_review_date
            session.add(word_obj)
            session.commit()
    return

@app.get('/words', response_class=HTMLResponse)
def words(request: Request, username = Depends(auth_handler.auth_wrapper)):
    words_list = []
    with Session(engine) as session:
        user = session.exec(select(User).where(User.username == username)).first()
        if user:
            words = session.exec(select(Word)
                .where(Word.user_id == user.id)
                .order_by(Word.next_review_date, (Word.last_reviewed_date))
                ).all()
            
            for word in words:
                last_reviewed = days_hours_mins(datetime.utcnow(), word.last_reviewed_date, is_last=True)
                next_review = days_hours_mins(word.next_review_date, datetime.utcnow())

                words_list.append({
                    'word': word.word,
                    'box_number': word.box_number,
                    'last_reviewed': last_reviewed,
                    'next_review': next_review
                })
            
    return templates.TemplateResponse("words.html", {"request": request, "words": words_list})


@app.post('/delete')
def delete(word: DeleteWord, username = Depends(auth_handler.auth_wrapper)):
   with Session(engine) as session:
       user = session.exec(select(User).where(User.username == username)).first()
       if user:
           word_to_delete = session.exec(select(Word).where(Word.word == word.word, Word.user_id == user.id)).first()
           if word_to_delete:
               session.delete(word_to_delete)
               session.commit()
               return {'delete_successful': True, 'error': None}
           else:
               return {'delete_successful': False, 'error': 'Word not found'}
       else:
           return {'delete_successful': False, 'error': 'User not found'}
       

@app.get('/emailpreference')
def words(request: Request, username = Depends(auth_handler.auth_wrapper)):
    with Session(engine) as session:
        user = session.exec(select(User).where(User.username == username)).first()
        if user:
            preference = user.wants_updates
            return {'preference': preference, 'error': None}
        return {'preference': preference, 'error': 'No user found'}
        

@app.post('/changepreference')
def change_preference(username = Depends(auth_handler.auth_wrapper)):
   with Session(engine) as session:
       user = session.exec(select(User).where(User.username == username)).first()
       if user:
           old_preference = user.wants_updates
           new_preference = not old_preference
           user.wants_updates = new_preference
           session.add(user)
           session.commit()
           return {'change_successful': True, 'error': None}
       else:
           return {'change_successful': False, 'error': 'USer not found'}