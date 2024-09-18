from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.remote.webelement import WebElement

import os
from time import sleep

class Nav(Chrome):
    @property
    def download_path(self):
        path = "download"
        path = os.path.join(os.getcwd(), path)
        if not os.path.exists(path):
            os.makedirs(path)
        return path
    
    def __init__(self) -> None:
        options = Options()
        #options.add_argument('--incognito')
        prefs:dict = {
            "download.default_directory": self.download_path,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
            }        
        options.add_experimental_option('prefs', prefs)
        super().__init__(options=options)
    
    def find_element(self, by=By.ID, value: str | None = None, *, timeout:int=10, wait:int|float=0) -> WebElement:
        sleep(wait)
        for _ in range(timeout*4):
            result:WebElement
            try:
                result = super().find_element(by, value)
                if result:
                    return result
            except:
                sleep(0.25)
        raise NoSuchElementException(f"'{by}: {value}' não encontrado!")
