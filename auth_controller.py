from keycloak import KeycloakOpenID
import logging as logger
import config
import requests
import sys
from vedis import Vedis

keycloak_openid = KeycloakOpenID(server_url=config.auth_url,
                                 client_id=config.client_id,
                                 realm_name=config.realm_name,
                                 client_secret_key=config.client_secret_key)


def check_auth(headers):
    if 'Authorization' in headers:
        try:
            token = headers['Authorization'].split()[1]
            token_info = keycloak_openid.introspect(token)
            return token
            """if 'active' in token_info:
                if token_info['active']:
                    return token_info
                else:
                    return False
            else:
                return False"""
        except:
            return False
    return False
