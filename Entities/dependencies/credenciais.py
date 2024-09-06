import json
import os
from copy import deepcopy
import traceback
from random import randint
from getpass import getuser
from typing import Literal, Dict
import asyncio

class Credential:
    def __init__(self, name_file:Literal["Microsoft-RPA", "API_ZENDESK"], path:str=f"C:\\Users\\{getuser()}\\PATRIMAR ENGENHARIA S A\\RPA - Documentos\\RPA - Dados\\CRD\\.patrimar_rpa\\credenciais\\") -> None:
        name:str = str(name_file)
        if not isinstance(path, str):
            raise TypeError("apenas strings")
        if not isinstance(name, str):
            raise TypeError("apenas strings")
        if not name.endswith('.json'):
            name += '.json'
        
        
        
        temp_path:str
        if "\\" in path:
            if not path.endswith("\\"):
                path += "\\"
            temp_path = "\\".join(path.split("\\")[0:-1]) + "\\"
            if not os.path.exists(temp_path):
                os.makedirs(temp_path)
        
        if "/" in path:
            if not path.endswith("/"):
                path += "/"
            temp_path = "/".join(path.split("/")[0:-1]) + "/"
            if not os.path.exists(temp_path):
                os.makedirs(temp_path)
                
        self.__path = path + name
    
    @property
    def path(self):
        return self.__path
            
        
    def load(self) -> dict:
        """crie / ler um arquivo json contendo as credenciais

        Args:
            path (str): caminho do arquivo que será salvo as crendicias

        Raises:
            FileNotFoundError: caso o arquivo não exista irá criar um e vai alertar que foi criado e pedira para iniciar o script novamente

        Returns:
            dict: dicionario com a credenciais salvas
        """
        
        if not os.path.exists(self.path):
            with open(self.path, 'w')as _file:
                json.dump({"key": 0},_file)
            #raise FileNotFoundError(f"{self.path=} não existe! então foi criar uma no repositorio, edite as credenciais e execute o codigo novamente!")

        with open(self.path, 'r')as _file:
            result:dict = json.load(_file)
        
        new_result = deepcopy(result)
        for key,value in new_result.items():
            if key == 'key':
                continue
            new_result[key] = self.decifrar(value, new_result['key'])
            
        return new_result
                            
    
    def save(self, **kargs) -> None:
        token = randint(500,6000)
        
        words:Dict[str,object] = {key:self.criar_cifra(value, token) for key,value in kargs.items()}
        words['key'] = token
        
        with open(self.path, 'w')as _file:
            json.dump(
                words,
                _file)
    
    def criar_cifra(self, text:str, key:int=1, response_json:bool=False) -> str:
        """criptografa a string informada orientada pela Key

        Args:
            text (str): texto a ser criptografado
            key (int, optional): chave para criptografia. Defaults to 1.
            response_json (bool, optional): retorna a string em formato json. Defaults to False.

        Returns:
            str: valor criptografado
        """
        if not isinstance(key, int):
            key = int(key)
        result:str = ""
        for letra in text:
            codigo:int = ord(letra) + key
            result += chr(codigo)
        
        if response_json:    
            return json.dumps(result)
        return result
    
    def decifrar(self, text:str, key:int) -> str:
        """descriptografa a string

        Args:
            text (str): texto a ser descriptografado
            key (int): chave para descriptografar

        Returns:
            str: texto descriptografado
        """
        return self.criar_cifra(text, -key)
        
if __name__ == "__main__":
    crd = Credential('API_ZENDESK')
    
    import base64
    crd = crd.load()
    
    def token(user, password) -> str:
        phrase:bytes = f"{user}/token:{password}".encode("utf-8")
        encode_phrase:str = base64.b64encode(phrase).decode()
        return encode_phrase
    
    print(token(crd['user'],crd['password']))
    print(token("rpa@patrimar.com.br",crd['password']))
    