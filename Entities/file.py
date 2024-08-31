import os
from xml.dom import NotFoundErr
import pandas as pd

from Entities.dependencies.functions import P

class File:
    @property
    def df(self) -> pd.DataFrame:
        try:
            return self.__df
        except AttributeError:
            print(P("Execute algum metodos .read() antes", color='red'))
            return pd.DataFrame()
    
    def __init__(self, path:str):
        self.__df:pd.DataFrame
        if os.path.exists(path):        
            if path.endswith('.csv'):
                self.__df = pd.read_csv(path)
            elif path.endswith('.xlsx'):
                self.__df = pd.read_excel(path)
            else:
                raise TypeError("Tipo de arquivo invalido")
        else:
            raise FileNotFoundError(f"o arquivo '{path}' não foi encontrado")