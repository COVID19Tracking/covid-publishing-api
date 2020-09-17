"""
Authentication tests
"""
import pytest

from app.auth.auth_cli import getToken
from flask import json, jsonify
from flask_jwt_extended import decode_token

def test_getToken_cli(app):
    with app.app_context():
        # generate a token and make sure it comes out valid
        token = getToken('test_username')
        assert token
    
        decoded = decode_token(token)
        assert(decoded['identity'] == 'test_username')
        
        # confirm that changing the secret key results in an authentication error
        old_key = app.config['JWT_SECRET_KEY']
        app.config['JWT_SECRET_KEY'] = 'adifferentkey'
        with pytest.raises(Exception, match="Signature verification failed"):
            decoded = decode_token(token)
        assert(decoded['identity'] == 'test_username')
        app.config['JWT_SECRET_KEY'] = old_key
        
def test_auth(app, headers):
    """
    make various requests to the test_auth endpoint with invalid and valid tokens
    """
    client = app.test_client()
    resp = client.get('/api/v1/test_auth')
    # should fail because this request lacks an authorization header
    assert resp.status_code == 401 
    
    bad_headers = {
        'Authorization': 'Bearer {}'.format('this_is_not_a_valid_token')
    }
    resp = client.get('/api/v1/test_auth', headers=bad_headers)
    # should fail because the token is invalid and the error message should be informative
    assert resp.status_code == 422
    assert resp.json['msg'] == 'Your database password is invalid: did you enter a secret key?'
    
    with app.app_context(): 
        bad_headers = {
          'Authorization': 'Bearer {}'.format(getToken('test_username'))
        }
        old_key = app.config['JWT_SECRET_KEY']
        app.config['JWT_SECRET_KEY'] = 'adifferentkey'
        resp = client.get('/api/v1/test_auth', headers=bad_headers)
        # should fail because the token was generated against the wrong secret key
        assert resp.status_code == 422
        app.config['JWT_SECRET_KEY'] = old_key
    
    resp = client.get('/api/v1/test_auth', headers=headers)
    # should pass because this is a valid token
    assert resp.status_code == 200
    assert resp.json['user'] == 'authenticated'
    
