import jwt
from fastapi import HTTPException, Security, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer # Delete
from passlib.context import CryptContext
from datetime import datetime, timedelta
import os

'''
HTTPException used to raise errors for invalid tokens which the framework handles to return an error to the user with the provided status code and errors message.

Security is used for dependency injection and will hihglight routes which require authorization headers in the swagger UI and provide a way to enter a bearer token there.

HTTPBearer is going to be used as part of the depednency injection to ensure a valid auth header has been provided when calling the endpoint.

HTTPAuthorizationCredentials is the object type that will be returned from the dependency injection.

CryptContext creates context for hashing and validating passwords.

Datetimw used for setting issue and expiry times of the jwt.
'''

class AuthHandler():
    # security = HTTPBearer()
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    secret = os.getenv('JWT_SECRET')

    def get_password_hash(self, password):
        '''
        Takes a plain text password and returns its securely hashed representation using CryptContext.
        '''
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password, hashed_password):
        '''
        Takes plain text password and hashed password and returns boolean indicating if passwords match.
        '''
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def encode_token(self, user_id):
        '''
        Takes a user ID and generates a JSON Web Token (JWT) for authentication.
        The token includes an expiration time, an issued at time, and the user ID as the subject.
        Returns the encoded token as a string.
        '''
        payload = {
            'exp': datetime.utcnow() + timedelta(days=1),
            'iat': datetime.utcnow(),
            'sub': user_id
        }
        return jwt.encode(
            payload,
            self.secret,
            algorithm='HS256'
        )
    
    def decode_token(self, token):
        '''
        Takes a token and decodes it to extract the subject (user ID).
        If the token is valid, returns the user ID.
        If the token has expired, raises an HTTPException with a 401 unauthorised status code and an expired signature error message.
        If the token is invalid, raises an HTTPException with a 401 unauthorised status code and an invalid token error message.
        '''
        try:
            payload = jwt.decode(token, self.secret, algorithms='HS256')
            return payload['sub']
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail='Signature has expired')
        except jwt.InvalidTokenError as e:
            raise HTTPException(status_code=401, detail='Invalid token')
        
    def auth_wrapper(self, request: Request):
        '''
        This function wraps the authentication process.
        It ensures that a valid bearer token is present in the authorization header of the request.
        If the token is present and valid, it returns the user ID extracted from the token.
        '''
        token = request.cookies.get("access_token")
        if not token:
            raise HTTPException(status_code=403, detail="Not authenticated")
        return self.decode_token(token.split(" ")[1]) # omitting "Bearer "
    
        # return self.decode_token(auth.credentials)