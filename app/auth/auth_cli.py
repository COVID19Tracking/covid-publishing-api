""" Create authentication tokens """
from flask_jwt_extended import create_access_token

def getToken(name):
    """"
    Defines a `flask auth getToken` command-line interface to generate an API key
    The key is secured by the current environment's SECRET_KEY 
    """
    access_token = create_access_token(identity=name)
    return access_token
