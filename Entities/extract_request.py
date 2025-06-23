import os
from typing import Literal
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from time import sleep
from Entities import exceptions
from patrimar_dependencies.functions import P, Functions
from .nav import Nav
import traceback
import pandas as pd

from office365.runtime.auth.authentication_context import AuthenticationContext
from office365.sharepoint.client_context import ClientContext
from office365.sharepoint.listitems.collection import ListItemCollection
from office365.runtime.paths.resource_path import ResourcePath
from botcity.maestro import * # type: ignore

        
    
class APISharePoint:
    """Realiza consultas e manipulações em listas do SharePoint."""
    
    @property
    def df(self) -> pd.DataFrame:
        """DataFrame com os itens retornados da lista consultada."""
        try:
            return self.__df
        except AttributeError:
            self.consultar()
            return self.__df
    
    @property
    def download_path(self):
        """Pasta local onde os anexos baixados serão salvos."""
        download_path:str = os.path.join(os.getcwd(), "Attachments_Download")
        if not os.path.exists(download_path):
            os.makedirs(download_path)
        return download_path
    
    def __init__(self, *, maestro:BotMaestroSDK|None=None, url:str, lista:str, email:str|None, password:str|None) -> None:
        """Inicializa a conexão com o SharePoint usando URL, nome da lista e credenciais."""
        self.__maestro:BotMaestroSDK|None = maestro
        
        if not ((email) and (password)):
            raise exceptions.CredentialNotFound("não foi possivel identificar as credenciais")
        
        self.__ctx_auth = AuthenticationContext(url)
        if self.__ctx_auth.acquire_token_for_user(email, password):
            self.__ctx = ClientContext(url, self.__ctx_auth)
        else:
            raise PermissionError("não foi possivel acessar a lista")
        
        self.__lista = self.__ctx.web.lists.get_by_title(lista)
        
        self.consultar()

        
    def consultar(self, with_attachment:bool=False):
        """Consulta a lista, opcionalmente baixando anexos."""
        items = self.__lista.get_items().expand(["AttachmentFiles"])
        self.__ctx.load(items)
        self.__ctx.execute_query()
        
        self.limpar_pasta_download() if with_attachment else None
        
        list_valid = []
        
        from copy import deepcopy
        
        while True:
            #ctx2 = deepcopy(self.__ctx)
            for item in items:
                if not item.properties.get('AprovacaoJuridico'):
                    if with_attachment:
                        path_attachment_download = []
                        if item.properties['NumChamadoZendesk']:
                            continue
                        if item.properties['Attachments']:
                            attachment_files = item.attachment_files
                            #self.__ctx.load(attachment_files)
                            #self.__ctx.execute_query()
                            for attachment_file in attachment_files:
                                file_name = os.path.join(self.download_path, f"{item.properties.get('ID')}-{attachment_file.properties['FileName']}")
                                path_attachment_download.append(file_name)
                                with open(file_name, 'wb')as _file_handle:
                                    attachment_file.download(_file_handle)
                                    self.__ctx.execute_query()
                                
                        item.properties['Attachment_Path'] = path_attachment_download
                                    
                    list_valid.append(item.properties)
            
            if not items._next_request_url:
                break
            
            next_request_url:str = str(items._next_request_url)
            # Remove a parte da URL base, que pode ser algo como "https://patrimar.sharepoint.com/sites/controle/_api"
            service_root = self.__ctx.service_root_url()
            if next_request_url.startswith(service_root):
                next_request_url = next_request_url[len(service_root):]            
            
            items = ListItemCollection(self.__ctx, ResourcePath(next_request_url))
            self.__ctx.load(items)
            self.__ctx.execute_query()                        
                    
        self.__df = pd.DataFrame(list_valid)
            
        return self
    
    def coletar_arquivos_controle(self):
        """Coleta arquivos aprovados, preparando-os para processamento de controle."""
        items = self.__lista.get_items().expand(["AttachmentFiles"])
        self.__ctx.load(items)
        self.__ctx.execute_query()
        
        self.limpar_pasta_download()
                
        list_valid = []
        
        while True:
            for item in items:
                if item.properties.get('RegistroArquivoControle'):
                    continue            
                if ("Aprovado".lower() in str(item.properties.get('AprovacaoJuridico')).lower()) and ("Sim".lower() in str(item.properties.get('EnviadoCentral')).lower()):
                    path_attachment_download = []
                    if item.properties['Attachments']:
                        attachment_files = item.attachment_files
                        #self.__ctx.load(attachment_files)
                        #self.__ctx.execute_query()
                        for attachment_file in attachment_files:
                            file_name = os.path.join(self.download_path, f"{item.properties.get('ID')}-{attachment_file.properties['FileName']}")
                            path_attachment_download.append(file_name)
                            with open(file_name, 'wb')as _file_handle:
                                attachment_file.download(_file_handle)
                                self.__ctx.execute_query()
                                        
                    item.properties['Attachment_Path'] = path_attachment_download
                                            
                    list_valid.append(item.properties)
                    
            if not items._next_request_url:
                break
            
            next_request_url = str(items._next_request_url)
            # Remove a parte da URL base, que pode ser algo como "https://patrimar.sharepoint.com/sites/controle/_api"
            service_root = self.__ctx.service_root_url()
            if next_request_url.startswith(service_root):
                next_request_url = next_request_url[len(service_root):]            
            
            items = ListItemCollection(self.__ctx, ResourcePath(next_request_url))
            self.__ctx.load(items)
            self.__ctx.execute_query()   
                                         
        self.__df = pd.DataFrame(list_valid)    
        
        return self
        
            
    def alterar(self, id, *, valor:Literal['', 'Aprovado', 'Recusado']|str, coluna:Literal['', 'AprovacaoJuridico', 'NumChamadoZendesk', 'ComentarioJuridico', 'ConclusaoJuridico','ResponsavelJuridico', 'RegistroArquivoControle']) -> None:
        """Altera valores de uma coluna específica de um item da lista."""
        item_to_update = self.__lista.get_item_by_id(id)
        # Atualizando os campos do item
        item_to_update.set_property(coluna, valor)
        #item_to_update.set_property("OutroCampo", "Novo Valor")
        item_to_update.update()
            
        # Executando a atualização no servidor
        self.__ctx.execute_query()
        
        self.consultar()
        
    def limpar_pasta_download(self) -> None:
        """Limpa a pasta onde os anexos são baixados, liberando arquivos em uso."""
        for file in os.listdir(self.download_path):
            file:str = os.path.join(self.download_path, file)
            
            if os.path.isfile(file):
                try:
                    os.unlink(file)
                except PermissionError as error:
                    print(error)
                    Functions.fechar_excel(file)
                    os.unlink(file)    
            
    

if __name__ == "__main__":
    pass