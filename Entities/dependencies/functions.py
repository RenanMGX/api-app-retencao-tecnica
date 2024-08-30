import xlwings as xw
from xlwings.main import Book
from time import sleep
from datetime import datetime
import re
import os
from colorama import Fore
from typing import Literal
import asyncio

class Functions:
    @staticmethod
    def fechar_excel(path:str, *, timeout:int=1, wait:int=0) -> bool:
        if wait > 0:
            sleep(wait)
        try:
            achou:bool = False
            for _ in range(timeout):
                for app in xw.apps:
                    for open_app in app.books:
                        open_app:Book
                        if open_app.name in path:
                            open_app.close()
                            if len(xw.apps) <= 0:
                                app.kill()                        
                            achou = True
                        if not re.search(r'Pasta[0-9]+', open_app.name) is None:
                            open_app.close()
                            if len(xw.apps) <= 0:
                                app.kill()                        
                sleep(1)
            if achou:
                return True
            return False
        except:
            return False
    
    @staticmethod
    def excel_open() -> list:
        open_excel:list = []
        for app in xw.apps:
            for open_app in app.books:
                open_app:Book
                open_excel.append(open_app.name)
        return open_excel
    
    @staticmethod    
    def tratar_caminho(path:str) -> str:
        if (path.endswith("\\")) or (path.endswith("/")):
            path = path[0:-1]
        return path
    
def _print(*args, end="\n", ):
    if not end.endswith("\n"):
        end += "\n"
    value = ""
    for arg in args:
        value += f"{arg} " 
    
    print(datetime.now().strftime(f"[%d/%m/%Y - %H:%M:%S] - {value}"), end=end)

class P:
    @property
    def date(self) -> str:
        return datetime.now().strftime("[%d/%m/%Y - %H:%M:%S] ")
    
    @property
    def color(self) -> str:
        if self.__color == 'white':
            return Fore.WHITE
        elif self.__color == 'blue':
            return Fore.BLUE
        elif self.__color == 'green':
            return Fore.GREEN
        elif self.__color == 'red':
            return Fore.RED
        elif self.__color =='cyan':
            return Fore.CYAN
        elif self.__color == 'yellow':
            return Fore.YELLOW
        elif self.__color == 'magenta':
            return Fore.MAGENTA
        else:
            return Fore.RESET
    
    def __init__(self, value: object, *, color:Literal['white', 'red', 'blue', 'green', 'cyan', 'yellow', 'magenta', 'nenhum'] = "nenhum") -> None:
        if not isinstance(value, str):
            value = str(value)
        self.__value:str = value
        self.__color:str = color
        
    def __str__(self) -> str:
        return f"{self.date}{self.color + self.__value + Fore.RESET}"

 
if __name__ == "__main__":
    
    pass
    