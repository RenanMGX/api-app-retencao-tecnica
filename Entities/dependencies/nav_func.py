
from typing import List, Literal

from Entities.dependencies.functions import P
from ..nav import Nav
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from time import sleep


class EncontrarBotoes:
    @property
    def buttons(self) -> List[WebElement]:
        return self.__nav.find_elements(By.TAG_NAME, 'button')
    
    def __init__(self, driver:Nav) -> None:
        self.__nav:Nav = driver
    
    def find_per_attribute(self, *, attribute:str, target:str, wait:int|float=0, timeout:int=10) -> WebElement:
        sleep(wait)
        erro:Exception = Exception("")
        for _ in range(timeout*4):
            print(P(f"procurando o botão '{attribute}: {target}'", color='yellow'))
            try:
                for button in self.buttons:
                    if button.get_attribute(attribute) == target:
                        return button
                raise NoSuchElementException(f"botão '{attribute}: {target}' não encontrado")
            except Exception as error:
                erro = error
                sleep(.25)
        raise erro
    
    def find_per_text(self, target:str, *, type:Literal['in', 'equal']='equal', wait:int|float=0, timeout:int=10) -> WebElement:
        sleep(wait)
        erro:Exception = Exception("")
        for _ in range(timeout*4):
            print(P(f"procurando o botão '{target}'", color='yellow'))
            try:
                for button in self.buttons:
                    if type == 'equal':
                        if target == button.text:
                            return button
                    elif type == 'in':
                        if target in button.text:
                            return button
                raise NoSuchElementException(f"botão '{target}' não encontrado")
            except Exception as error:
                erro = error
                sleep(.25)
        raise erro
