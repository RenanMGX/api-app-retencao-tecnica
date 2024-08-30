from imghdr import what
import os
import pdb
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from time import sleep
from Entities.dependencies.credenciais import Credential
from Entities import exceptions
from Entities.dependencies.nav_func import EncontrarBotoes
from dependencies.functions import P
from dependencies.logs import Logs
from .nav import Nav
import traceback

from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.remote.webdriver import WebDriver

        
class SiteAppReten():
    @property
    def nav(self) -> Nav:
        return self.__nav
    @nav.deleter
    def nav(self) -> None:
        try:
            del self.__nav
        except:
            pass
    
    @property
    def nav_status(self) -> bool:
        try:
            self.nav
            return True
        except AttributeError:
            print(P("O navegador precisa ser iniciado com o metodo '.start_nav()'",color='red'))
            return False
    
        
    def start_nav(self, *, url:str="", timeout:int=10):
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
        if self.nav_status:
            self.login()
            
            print(P("iniciando extração"))
            buttons_class = EncontrarBotoes(self.nav)
            
            try:
                buttons_class.find_per_text('Exportar', type='in').click()
            except NoSuchElementException:
                buttons_class.find_per_attribute(attribute='data-id', target='more').click()
                buttons_class.find_per_text('Exportar', type='in').click()
            
            sleep(1)
            self.limpar_pasta(self.nav.download_path)
            print(P("baixando arquivo"))
            buttons_class.find_per_text('\uf1e5\nExportar para CSV').click()
            self.verificar_arquivos_em_download(self.nav.download_path)
            
            print(P("extração concluida", color='green'))
            
    def limpar_pasta(self, path:str) -> bool:
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
        print(P("verificando arquivos que estão baixando"))
        if os.path.exists(path):
            while len([x for x in os.listdir(path) if ".crdownload" in x]) > 0:
                sleep(.25)
            sleep(3)
            return 
        else:
            raise FileNotFoundError(f"o caminho '{path}' não foi encontrado")
    
if __name__ == "__main__":
    pass