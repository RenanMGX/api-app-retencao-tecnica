import csv
import os
from typing import Literal
from datetime import datetime
import re
from .functions import Functions
import traceback
import asyncio
import requests
import json
from getpass import getuser
from socket import gethostname
from .project_name import PROJECT_NAME


class Logs:
    @property
    def path_folder(self) -> str:
        return self.__path_folder
    
    @property
    def name(self) -> str:
        return self.__name
    
    def __init__(self, name:str=PROJECT_NAME, *, path_folder:str=os.path.join(os.getcwd(), 'Logs'), hostname:str="192.168.1.218", port:str="8000", token:str="7841a44ce4619d9e3eaa151810cfc4babc8eb5ae") -> None:
        self.__path_folder:str = path_folder
        self.__name:str = name
        if not os.path.exists(self.path_folder):
            os.makedirs(self.path_folder)
            
        self.__hostname:str = hostname
        self.__port:str = port
        self.__token:str = token
            
    def online_register(self, *, name_rpa:str, status:Literal[0,1,2,99], date:datetime, descricao:str, exception:str="", nome_pc:str="", nome_agente=""):
        try:
            reqUrl = f"http://{self.__hostname}:{self.__port}/api/rpa_logs/registrar"

            headersList = {
            "Authorization": f"Token {self.__token}",
            "Content-Type": "application/json" 
            }

            payload = json.dumps({
            "nome_rpa": str(name_rpa),
            "nome_pc" : str(nome_pc),
            "nome_agente": str(nome_agente),
            "status": status,
            "horario" : date.strftime('%d/%m/%Y %H:%M:%S'),
            "descricao": str(descricao),
            "exception": str(exception)
            })

            response = requests.request("PATCH", reqUrl, data=payload,  headers=headersList)

            print(response.text)
        except Exception as error:
            print(error)
                    
        
    def register(self, *, status:Literal['Error', 'Concluido', 'Report', 'Test'], description:str="", exception:str|None=traceback.format_exc(), file:str="Logs_Operation.csv", date_format:str='%d/%m/%Y %H:%M:%S'):
        if not file.endswith('.csv'):
            file += '.csv'
        
        file_path:str = os.path.join(self.path_folder, file)
        
        if not exception is None:
            exception = str(exception)
            exception = re.sub(r'\n', ' <br> ', exception)
        else:
            exception = ""
        
        description = re.sub(r'\n', ' <br> ', description)
        
        exist:bool = os.path.exists(file_path)
        
        status_code:Literal[0,1,2,99]
        if status == 'Concluido':
            status_code = 0
        elif status == 'Error':
            status_code = 1
        elif status == 'Report':
            status_code = 2
        elif status == 'Test':
            status_code = 99
        
        self.online_register(name_rpa=self.name, status=status_code,date=datetime.now(), descricao=description, exception=exception, nome_pc=gethostname(), nome_agente=getuser())
        
        for _ in range(2):
            try:
                with open(file_path, 'a', encoding='utf-8', newline='') as _file:
                    csv_writer = csv.writer(_file, delimiter=';')
                    if not exist:
                        csv_writer.writerow(["Date", "Name", "Status", "Description", "Exception"])
                    csv_writer.writerow([datetime.now().strftime(date_format), self.name, status, description, exception])
                    return
            except PermissionError:
                #pass
                Functions.fechar_excel(file)
            except Exception as error:
                raise error   

if __name__ == "__main__":
    bot = Logs("testes")
    #asyncio.run(bot.register(status='Test', description="Test", exception=traceback.format_exc()))
    