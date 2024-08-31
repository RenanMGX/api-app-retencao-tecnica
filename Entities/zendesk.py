
import base64
import os
import pdb
import json

import requests
from Entities.dependencies.credenciais import Credential

class API:
    @property
    def url(self) -> str:
        return "https://patrimar.zendesk.com/"
    
    @property
    def token(self) -> str:
        phrase:bytes = f"{self.__user}/token:{self.__password}".encode("utf-8")
        encode_phrase:str = base64.b64encode(phrase).decode()
        return encode_phrase

    def __init__(self) -> None:
        crd:dict = Credential('API_ZENDESK').load()
        self.__user:str|None = crd.get('user')
        self.__password:str|None = crd.get('password')
        
    def get(self, ticket:str) -> dict:
        url = os.path.join(self.url, f"api/v2/tickets/{ticket}")
        
        headersList = {
        "Authorization": f"Basic {self.token}",
        "Content-Type": "application/json"
        }

        payload = ""

        response = requests.request("GET", url, data=payload,  headers=headersList)
        
        try:
            _response = response.json()
        except:
            _response = {}

        return {"status_code": response.status_code, "reason": response.reason, 'response': _response}
        
    def add(self) -> dict:
        url = os.path.join(self.url, f"api/v2/tickets")

        headersList = {
        "Authorization": f"Basic {self.token}",
        "Content-Type": "application/json"
        }

        payload = json.dumps({
        "ticket": {
                "subject": "Teste",
            "raw_subject": "Teste",
            "description": "Teste"
        }
        })

        response = requests.request("POST", url, data=payload,  headers=headersList)
        
        try:
            _response = response.json()
        except:
            _response = {}
        
        return {'status_code': response.status_code, 'reason': response.reason, 'response': _response}
    
    def delete(self, ticket:str|int) -> dict:
        url = os.path.join(self.url, f"api/v2/tickets/{ticket}")

        headersList = {
        "Authorization": f"Basic {self.token}",
        "Content-Type": "application/json"
        }

        payload = ""
        
        response = requests.request("DELETE", url, data=payload,  headers=headersList)
        
        try:
            _response = response.json()
        except:
            _response = {}

        return {'status_code': response.status_code, 'reason': response.reason, 'response': _response}
        
    