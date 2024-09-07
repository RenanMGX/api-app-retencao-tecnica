
import base64
import os
import pdb
import json
from typing import Literal, Dict, List, LiteralString

import requests
from Entities.dependencies.credenciais import Credential

class API:
    @property
    def url(self) -> str:
        return "https://patrimar.zendesk.com/"
    
    @property
    def token(self) -> str:
        phrase:bytes = f"{self.__user}/token:{self.__password}".encode("utf-8")
        #phrase:bytes = f"rpa@patrimar.com.br/token:{self.__password}".encode("utf-8")
        encode_phrase:str = base64.b64encode(phrase).decode()
        return encode_phrase
    
    @property
    def marca(self) -> Dict[str, dict]:
        return {
            "administrativo": {
                "group_id": 26071794815383,
                "brand_id": 25317468115479,
            }
        }
        

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
        
    def attachment(self, file_path:str) -> str:
        try:
            if not os.path.exists(file_path):
                print(f"arquivo '{file_path}' não foi encontrado")
                return ""
                raise FileNotFoundError(f"arquivo '{file_path}' não foi encontrado")

            reqUrl = f"https://patrimar.zendesk.com/api/v2/uploads?filename={os.path.basename(file_path)}"

            headersList = {
            "Authorization": f"Basic {self.token}",
            "Content-Type": "application/octet-stream" 
            }

            payload = open(file_path, 'rb').read()

            response = requests.request("POST", reqUrl, data=payload,  headers=headersList)

            try:
                return response.json().get('upload').get('token')
            except Exception as error:
                print(type(error), error)
                return ""
        except Exception as error:
            print(type(error), error)
            return ""
        
    def add(self, *, 
            marca:Literal["administrativo"],
            titulo:str,
            descri:str,
            ticket_form_id:int|None=None,
            custom_fields:List[Dict[Literal["id", "value"],int|str]]=[],
            attachment_path:str=""
            ) -> dict:
        url = os.path.join(self.url, f"api/v2/tickets")

        headersList = {
        "Authorization": f"Basic {self.token}",
        "Content-Type": "application/json"
        }
        
        data:Dict[str,dict] = {
            "ticket":{}
        }
        
        data["ticket"]["requester_id"] = 26079230247703 #id do RPA
        data["ticket"]["submitter_id"] = 26079230247703 #id do RPA
        
        data["ticket"]["group_id"] = self.marca[marca]['group_id']
        data["ticket"]["brand_id"] = self.marca[marca]['brand_id']
        data["ticket"]["subject"] = titulo
        data["ticket"]["raw_subject"] = titulo
        data["ticket"]["description"] = descri
        if ticket_form_id:
            data["ticket"]["ticket_form_id"] = ticket_form_id
        if custom_fields:
            data["ticket"]["custom_fields"] = custom_fields
        
        if (attachment_token:=self.attachment(attachment_path)):
            data["ticket"]["comment"] =  {
                #"body": "\n\n testando anexo 0013 \n\n\n",
                "uploads": attachment_token
            }

        payload = json.dumps(data)
        
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
        
if __name__ == "__main__":
    pass