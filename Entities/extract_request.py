import os
from typing import Literal
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from time import sleep
from Entities.dependencies.credenciais import Credential
from Entities import exceptions
from Entities.dependencies.nav_func import EncontrarBotoes
from dependencies.functions import P, Functions
from dependencies.logs import Logs
from .nav import Nav
import traceback
import pandas as pd

from office365.runtime.auth.authentication_context import AuthenticationContext
from office365.sharepoint.client_context import ClientContext

        
class SiteAppReten():
    """Gerencia a navegação e extração de dados do site da aplicação de retenção."""
    
    @property
    def nav(self) -> Nav:
        """Instância do navegador (Nav)."""
        return self.__nav
    @nav.deleter
    def nav(self) -> None:
        try:
            del self.__nav
        except:
            pass
    
    @property
    def nav_status(self) -> bool:
        """Indica se o navegador está aberto ou não."""
        try:
            self.nav
            return True
        except AttributeError:
            print(P("O navegador precisa ser iniciado com o metodo '.start_nav()'",color='red'))
            return False
    
        
    def start_nav(self, *, url:str="", timeout:int=10):
        """Inicia o navegador com base em uma URL e tempo limite."""
        print(P("iniciando Navegador"))
        if not self.nav_status:
            for _ in range(timeout):
                try:
                    self.__nav:Nav = Nav()
                    if url:
                        self.nav.get(url)
                        return
                    else:
                        return
                except:
                    self.nav.close()
                    del self.nav
                    sleep(1)
        else:
            print(P("navegador já está aberto!", color='red'))
    
    @staticmethod
    def esperar_conectar(f):
        """Verifica se há mensagem de conexão pendente antes de executar a ação."""
        def wrap(self, *args, **kwargs):
            result = f(self, args, kwargs)
            try:
                if 'Tentando Conectá-lo'.lower() in self.nav.find_element(By.TAG_NAME, 'html').text.lower():
                    print("esperando conectar ao site")
                while 'Tentando Conectá-lo'.lower() in self.nav.find_element(By.TAG_NAME, 'html').text.lower():
                    #print("esperando")
                    sleep(.25)
            except:
                pass
            return result
        return wrap           
    
    @esperar_conectar
    def login(self, exception:bool=True, register_log:bool=True) -> bool:           
        """Realiza o login no site utilizando credenciais salvas."""
        try:
            crd:dict = Credential('Microsoft-RPA').load()
            if (crd.get('email')) and (crd.get('password')):
                html = self.nav.find_element(By.TAG_NAME, 'html', wait=3)
                if not (("Entrar" in html.text) and ("Não consegue acessar sua conta?" in html.text)):
                    if self.nav.title == 'Janela da Engenharia | Controle de Obras':
                        print(P("ja está logado", color='green'))
                        return True
                    raise exceptions.LoginPageNotFound("Não foi possivel identificar a pagina de login")
                
                print(P("Fazendo Login"))
                login_camp = self.nav.find_element(By.ID, 'i0116')
                login_camp.clear()
                login_camp.send_keys(str(crd.get('email')))
                login_camp.send_keys(Keys.RETURN)
                
                try:
                    usernameError = self.nav.find_element(By.ID, "usernameError", timeout=3)
                    raise exceptions.LoginError(usernameError.text)
                except NoSuchElementException:
                    pass
                
                pass_camp = self.nav.find_element(By.ID, 'i0118')
                pass_camp.clear()
                pass_camp.send_keys(str(crd.get('password')))
                pass_camp.send_keys(Keys.RETURN)
                
                try:
                    passwordError = self.nav.find_element(By.ID, "passwordError", timeout=3)
                    raise exceptions.LoginError(passwordError.text)
                except NoSuchElementException:
                    pass
                
                if not "Continuar conectado?" in self.nav.find_element(By.TAG_NAME, 'html').text:
                    return True
                
                self.nav.find_element(By.ID, 'idBtn_Back').click()
                return True
                
            else:
                raise exceptions.CredentialNotFound("Não foi possivel encontrar as credenciais")
        except Exception as error:
            if register_log:
                Logs().register(status='Error', description='Erro ao efetuar login', exception=traceback.format_exc())
            if exception:
                raise error
            else:
                return True
            
            
    def start(self):
        """Responsável por iniciar a rotina de extração de dados."""
        if self.nav_status:
            self.login()
            
            print(P("iniciando extração"))
            buttons_class = EncontrarBotoes(self.nav)
            
            try:
                buttons_class.find_per_text('Exportar', type='in', timeout=2).click()
            except NoSuchElementException:
                buttons_class.find_per_attribute(attribute='data-id', target='more').click()
                buttons_class.find_per_text('Exportar', type='in').click()
            
            sleep(1)
            self.limpar_pasta(self.nav.download_path)
            print(P("baixando arquivo"))
            buttons_class.find_per_text('\uf1e5\nExportar para CSV').click()
            self.verificar_arquivos_em_download(self.nav.download_path)
            
            print(P("extração concluida", color='green'))
            
            return os.path.join(self.nav.download_path, os.listdir(self.nav.download_path)[0])
            
    def limpar_pasta(self, path:str) -> bool:
        """Limpa a pasta de destino, removendo arquivos existentes."""
        print(P("Limpando pasta"))
        if os.path.exists(path):
            for file in os.listdir(path):
                file = os.path.join(path, file)
                if os.path.isfile(file):
                    os.unlink(file)
            return True
        else:
            raise FileNotFoundError(f"o caminho '{path}' não foi encontrado")
        
    def verificar_arquivos_em_download(self, path:str):
        """Verifica se há arquivos em processo de download e aguarda sua conclusão."""
        print(P("verificando arquivos que estão baixando"))
        if os.path.exists(path):
            while len([x for x in os.listdir(path) if ".crdownload" in x]) > 0:
                sleep(.25)
            sleep(3)
            return 
        else:
            raise FileNotFoundError(f"o caminho '{path}' não foi encontrado")
    
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
    
    def __init__(self, *, url:str, lista:str, email:str|None, password:str|None) -> None:
        """Inicializa a conexão com o SharePoint usando URL, nome da lista e credenciais."""
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
        items = self.__lista.get_items()
        self.__ctx.load(items)
        self.__ctx.execute_query()
        
        self.limpar_pasta_download() if with_attachment else None
        
        list_valid = []
        for item in items:
            if not item.properties.get('AprovacaoJuridico'):
                if with_attachment:
                    path_attachment_download = []
                    if item.properties['NumChamadoZendesk']:
                        continue
                    if item.properties['Attachments']:
                        attachment_files = item.attachment_files
                        self.__ctx.load(attachment_files)
                        self.__ctx.execute_query()
                        for attachment_file in attachment_files:
                            file_name = os.path.join(self.download_path, f"{item.properties.get('ID')}-{attachment_file.properties['FileName']}")
                            path_attachment_download.append(file_name)
                            with open(file_name, 'wb')as _file_handle:
                                attachment_file.download(_file_handle)
                                self.__ctx.execute_query()
                            
                    item.properties['Attachment_Path'] = path_attachment_download
                                
                list_valid.append(item.properties)
                        
                    
        self.__df = pd.DataFrame(list_valid)
            
        return self
    
    def coletar_arquivos_controle(self):
        """Coleta arquivos aprovados, preparando-os para processamento de controle."""
        items = self.__lista.get_items()
        self.__ctx.load(items)
        self.__ctx.execute_query()
        
        self.limpar_pasta_download()
                
        list_valid = []
        for item in items:
            if item.properties.get('RegistroArquivoControle'):
                continue            
            if ("Aprovado".lower() in str(item.properties.get('AprovacaoJuridico')).lower()) and ("Sim".lower() in str(item.properties.get('EnviadoCentral')).lower()):
                path_attachment_download = []
                if item.properties['Attachments']:
                    attachment_files = item.attachment_files
                    self.__ctx.load(attachment_files)
                    self.__ctx.execute_query()
                    for attachment_file in attachment_files:
                        file_name = os.path.join(self.download_path, f"{item.properties.get('ID')}-{attachment_file.properties['FileName']}")
                        path_attachment_download.append(file_name)
                        with open(file_name, 'wb')as _file_handle:
                            attachment_file.download(_file_handle)
                            self.__ctx.execute_query()
                                    
                item.properties['Attachment_Path'] = path_attachment_download
                                        
                list_valid.append(item.properties)
                                
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