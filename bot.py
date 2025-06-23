"""
WARNING:

Please make sure you install the bot dependencies with `pip install --upgrade -r requirements.txt`
in order to get all the dependencies on your Python environment.

Also, if you are using PyCharm or another IDE, make sure that you use the SAME Python interpreter
as your IDE.

If you get an error like:
```
ModuleNotFoundError: No module named 'botcity'
```

This means that you are likely using a different Python interpreter than the one used to install the dependencies.
To fix this, you can either:
- Use the same interpreter as your IDE and install your bot with `pip install --upgrade -r requirements.txt`
- Use the same interpreter as the one used to install the bot (`pip install --upgrade -r requirements.txt`)

Please refer to the documentation for more information at
https://documentation.botcity.dev/tutorials/custom-automations/python-custom/
"""

# Import for integration with BotCity Maestro SDK
from botcity.maestro import * #type: ignore
import traceback
from patrimar_dependencies.gemini_ia import ErrorIA
from main import ExecuteAPP

# Disable errors if we are not connected to Maestro
BotMaestroSDK.RAISE_NOT_CONNECTED = False #type: ignore

class Processados:
    @property
    def total_items(self):
        return self.__total_items
    
    def __init__(self, total_processador:int=1):
        self.__total_items = total_processador
        self.processados = 0


class Execute:
    @staticmethod
    def start():
        ExecuteAPP(
            sharepoint_email=maestro.get_credential(label="Microsoft-RPA", key="email"),
            sharepoint_password=maestro.get_credential(label="Microsoft-RPA", key="password"),
            zendesk_user=maestro.get_credential(label="API_ZENDESK", key="user"),
            zendesk_password=maestro.get_credential(label="API_ZENDESK", key="password")       
            ).start_app()
        processados.processados += 1
        

if __name__ == '__main__':
    maestro = BotMaestroSDK.from_sys_args()
    execution = maestro.get_execution()
    print(f"Task ID is: {execution.task_id}")
    print(f"Task Parameters are: {execution.parameters}")

    processados = Processados(1)

    try:
        Execute.start()
        
        maestro.finish_task(
                    task_id=execution.task_id,
                    status=AutomationTaskFinishStatus.SUCCESS,
                    message="Tarefa BotYoutube finalizada com sucesso",
                    total_items=processados.total_items, # Número total de itens processados
                    processed_items=processados.processados, # Número de itens processados com sucesso
                    failed_items=(processados.total_items - processados.processados) # Número de itens processados com falha
        )
        
    except Exception as error:
        ia_response = "Sem Resposta da IA"
        try:
            token = maestro.get_credential(label="GeminiIA-Token-Default", key="token")
            if isinstance(token, str):
                ia_result = ErrorIA.error_message(
                    token=token,
                    message=traceback.format_exc()
                )
                ia_response = ia_result.replace("\n", " ")
        except Exception as e:
            maestro.error(task_id=int(execution.task_id), exception=e)

        maestro.error(task_id=int(execution.task_id), exception=error, tags={"IA Response": ia_response})
        
        maestro.finish_task(
                    task_id=execution.task_id,
                    status=AutomationTaskFinishStatus.FAILED,
                    message="Tarefa Alimentar Dashboard Suprimentos finalizada com sucesso",
                    total_items=processados.total_items, # Número total de itens processados
                    processed_items=processados.processados, # Número de itens processados com sucesso
                    failed_items=(processados.total_items - processados.processados) # Número de itens processados com falha
        )
