
import base64
import os
import json
from typing import Literal, Dict, List
import requests
from Entities.exceptions import CredentialNotFound

class APIZendesk:
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
            },
            "juridico": {
                "group_id": 11065757529239,
                "brand_id": 11062040706839,
            },
        }
    
    @property
    def usuario_criador(self) -> Dict[str, dict]:
        return {
            "rpa_user": {
                "requester_id": 26079230247703, #id do RPA
                "submitter_id": 26079230247703  #id do RPA
            }
        }

    def __init__(self, user:str|None, password:str|None) -> None:
        if not ((user) and (password)):
            raise CredentialNotFound("não foi possivel identificar as credenciais")
        self.__user:str = user
        self.__password:str = password
        
    def get(self, id: str, *, type:Literal['tickets', 'comments', 'user']='tickets') -> dict:
        """
        Busca informações de um ticket específico na API do Zendesk.

        :param ticket: O ID do ticket a ser buscado.
        :return: Um dicionário contendo o status da resposta, a razão e o conteúdo da resposta.
        """
        # Constrói a URL para a requisição do ticket específico
        url:str
        if type == 'tickets':
            url = os.path.join(self.url, f"api/v2/tickets/{id}")
        elif type == 'comments':
            url = os.path.join(self.url, f"api/v2/tickets/{id}/comments")
        elif type == 'user':
            url = os.path.join(self.url, f"api/v2/users/{id}")
            
                    
        # Define os cabeçalhos da requisição, incluindo a autorização e o tipo de conteúdo
        headersList = {
            "Authorization": f"Basic {self.token}",
            "Content-Type": "application/json"
        }
        
        # Payload vazio, pois a requisição GET não necessita de um corpo
        payload = ""
        
        # Faz a requisição GET para a API do Zendesk
        response = requests.request("GET", url, data=payload, headers=headersList)
        
        try:
            # Tenta converter a resposta para JSON
            _response = response.json()
        except:
            # Se a conversão falhar, retorna um dicionário vazio
            _response = {}
        
        # Retorna um dicionário com o status da resposta, a razão e o conteúdo da resposta
        return {"status_code": response.status_code, "reason": response.reason, 'response': _response}    
    
        
    def attachment(self, file_path: str) -> str:
        """
        Faz o upload de um arquivo para o Zendesk e retorna o token do upload.

        :param file_path: O caminho do arquivo a ser enviado.
        :return: O token do upload se bem-sucedido, caso contrário, uma string vazia.
        """
        try:
            # Verifica se o arquivo existe no caminho especificado
            if not os.path.exists(file_path):
                print(f"arquivo '{file_path}' não foi encontrado")
                return ""
                raise FileNotFoundError(f"arquivo '{file_path}' não foi encontrado")

            # Constrói a URL para a requisição de upload
            reqUrl = f"https://patrimar.zendesk.com/api/v2/uploads?filename={os.path.basename(file_path)}"

            # Define os cabeçalhos da requisição, incluindo a autorização e o tipo de conteúdo
            headersList = {
                "Authorization": f"Basic {self.token}",
                "Content-Type": "application/octet-stream"
            }

            # Lê o conteúdo do arquivo em binário
            payload = open(file_path, 'rb').read()

            # Faz a requisição POST para a API do Zendesk
            response = requests.request("POST", reqUrl, data=payload, headers=headersList)

            try:
                # Tenta extrair o token do upload da resposta JSON
                return response.json().get('upload').get('token')
            except Exception as error:
                # Em caso de erro, imprime o tipo e a mensagem do erro
                print(type(error), error)
                return ""
        except Exception as error:
            # Em caso de erro, imprime o tipo e a mensagem do erro
            print(type(error), error)
            return ""        
        
        
    def add(self, *, 
            marca:Literal["administrativo", "juridico"],
            titulo:str,
            descri:str,
            ticket_form_id:int|None=None,
            fields:List[Dict[Literal["id", "value"],int|str]]=[],
            #custom_fields:List[Dict[Literal["id", "value"],int|str]]=[],
            tags:List[str] = [],
            attachment_path:List[str] = [], 
            criador_chamado:Literal['rpa_user'] = "rpa_user"
            ) -> dict:
        url = os.path.join(self.url, f"api/v2/tickets")

        headersList = {
        "Authorization": f"Basic {self.token}",
        "Content-Type": "application/json"
        }
        
        data:Dict[str,dict] = {
            "ticket":{}
        }
        
        data["ticket"]["requester_id"] = self.usuario_criador[criador_chamado]['requester_id']
        data["ticket"]["submitter_id"] = self.usuario_criador[criador_chamado]['submitter_id']
        
        data["ticket"]["group_id"] = self.marca[marca]['group_id']
        data["ticket"]["brand_id"] = self.marca[marca]['brand_id']
        data["ticket"]["subject"] = titulo
        data["ticket"]["raw_subject"] = titulo
        data["ticket"]["description"] = descri
        if ticket_form_id:
            data["ticket"]["ticket_form_id"] = ticket_form_id
        if fields:
            data["ticket"]["custom_fields"] = fields
        if fields:
            data["ticket"]["fields"] = fields
        if tags:
            data["ticket"]["tags"] = tags
        
        if attachment_path:
            if (attachment_token:=self.attachment(attachment_path[0])):
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
        
        if input(f"Tem certeza que quer excluir o ticket '{ticket}' [s/n]: ").lower() != 's':
            return {'status_code': 404, 'reason': "não respondeu para continuar a exclusão do script"}

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