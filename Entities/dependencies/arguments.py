import sys
from typing import Dict, List
from Entities.dependencies.logs import Logs, traceback
from typing import Literal

class Arguments:
    def __init__(self, valid_arguments:Dict[str, object], log_status:Literal['Error', 'Concluido', 'Report', 'Test', None]='Concluido') -> None:
        """
        Inicializa a classe Arguments.

        :param valid_arguments: Dicionário de argumentos válidos e suas funções associadas.
        :param log_status: Status do log a ser registrado.
        """
        self.__valid_arguments = valid_arguments
        self.__argv:list = sys.argv
        self.__status:Literal['Error', 'Concluido', 'Report', 'Test', None] = log_status
        
        self.__start()
    
    def __start(self):
        """
        Inicia o processamento dos argumentos passados via linha de comando.
        """

        if len(self.__argv) > 1:
            selected_argv = self.__argv[1]
            if selected_argv in self.__valid_arguments:
                try:
                    if len(self.__argv) == 3:
                        self.__valid_arguments[selected_argv](self.__argv[2]) #type: ignore
                    elif len(self.__argv) > 3:
                        self.__valid_arguments[selected_argv](self.__argv[2:]) #type: ignore
                    else:
                        self.__valid_arguments[selected_argv]() #type: ignore
                    if self.__status:
                        Logs().register(status=self.__status, description="Automação concluida com sucesso!")
                except Exception as error:
                    print(type(error), str(error))
                    Logs().register(status='Error', description=str(error), exception=traceback.format_exc())
            else:
                print("argumento não existe!")
                self.__listar_argvs()
        else:
            self.__listar_argvs()
            
    def __listar_argvs(self):
        """
        Lista os argumentos válidos permitidos.
        """
        print("são permitido apenas os seguintes argumentos: ")
        for key, value in self.__valid_arguments.items():
            print(key)

def teste(args):
    """
    Função de teste para exibir os argumentos passados.

    :param args: Argumentos passados.
    """
    print(args)
    
if __name__ == "__main__":
    Arguments(valid_arguments={
        "teste": teste
    })