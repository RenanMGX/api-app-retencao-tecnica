from typing import Dict
from Entities.dependencies.credenciais import Credential
from Entities.dependencies.functions import P
from Entities.extract_request import APISharePoint
import sys
from Entities.dependencies.logs import Logs
import traceback
from Entities.zendesk import APIZendesk

def test():
    print("testado")

class Execute:
    def __init__(self) -> None:
        #sharepoint
        crd_sharepoint:dict = Credential('Microsoft-RPA').load()
        self.__sharePoint:APISharePoint = APISharePoint(
            url="https://patrimar.sharepoint.com/sites/controle",
            lista="RetencaoTecnica",
            email=crd_sharepoint.get('email'),
            password=crd_sharepoint.get('password')
        )
        
        #zendesk
        crd_zendesk:dict = Credential('API_ZENDESK').load()
        self.__zendesk:APIZendesk = APIZendesk(
            user=crd_zendesk['user'],
            password=crd_zendesk['password']
        )
    
    def start(self):
        self.criar_chamado_etapa_1()
        self.consultar_chamado_etapa_2()
        print(P("Finalizando Script", color='white'))
        
    def criar_chamado_etapa_1(self):
        print(P("listando solicitação para abrir chamado"))
        self.__sharePoint.consultar(with_attachment=True)
        df = self.__sharePoint.df
        try:
            df = df[~df['NumChamadoZendesk'].notnull()]
        except KeyError:
            pass
        if df.empty:
            print(P("Nenhum chamado para Criar", color='cyan'))
            return
        
        for row, value in df.iterrows():
            descri = f"""
            teste chamado do TI para aplicativo de retenção tecnica\n
            CNPJ: {value['CnpjFormatado']}\n
            Nome Empreiteiro: {value['NomeEmpreiteiro']}\n
            """
            response:dict = self.__zendesk.add(marca='juridico', titulo='TESTE TI', descri=descri, attachment_path=value['Attachment_Path'])
            if response.get('status_code') == 201:
                ticket:str = response.get('response').get('ticket').get('id') #type: ignore
                print(f"numero do chamado: {ticket}") ######
                self.__sharePoint.alterar(int(value['Id']), coluna='NumChamadoZendesk', valor=str(ticket))
        
    def consultar_chamado_etapa_2(self):
        print(P("listando solicitação para consultar retorno do Juridico"))
        self.__sharePoint.consultar()
        df = self.__sharePoint.df
        try:
            df = df[df['NumChamadoZendesk'].notnull()]
        except KeyError:
            pass
        if df.empty:
            print(P("nenhum chamado para consultar no Juridico", color='cyan'))
            return
        
        for row, value in df.iterrows():
            print(P(f"verificando chamado '{value['NumChamadoZendesk']}' da solicitaçao no app '{value['Id']}'"))
            response = self.__zendesk.get(str(value['NumChamadoZendesk']))
            if response.get('status_code') == 200:
                
                fields = {x['id']:x['value'] for x in response.get('response').get('ticket').get('fields')} #type: ignore
                custom_fields = {x['id']:x['value'] for x in response.get('response').get('ticket').get('custom_fields')}#type: ignore 
                
                if (fields.get(25245062103831) == "sim_pend_consultivo") and (custom_fields.get(25245062103831)  == "sim_pend_consultivo"):
                    self.__sharePoint.alterar(int(value['Id']), coluna='AprovacaoJuridico', valor='Aprovado')
                    print(P("a solicitação foi aceita", color='green'))
                elif (fields.get(25245062103831) == "não_pend_consultivo") and (custom_fields.get(25245062103831)  == "não_pend_consultivo"):
                    self.__sharePoint.alterar(int(value['Id']), coluna='AprovacaoJuridico', valor='Rejeitado')
                    print(P("a solicitação foi Rejeitada", color='red'))
                else:
                    print(P("ainda sem resposta", color='yellow'))
                    continue
                
            print(P("Verificação de chamado encerrada"))
        
    def test(self):
        self.__sharePoint.alterar(304, coluna='NumChamadoZendesk', valor="52308")

if __name__ == "__main__":
    execute = Execute()
    valid_argvs:Dict[str, object] = {
        "start" : execute.start,
        "teste" : execute.test
    }
    
    def informativo():
        print("informe apenas os argumentos validos:")
        for arg in list(valid_argvs.keys()):
            print(P(arg))
    
    argv = sys.argv
    if len(argv) > 1:
        if argv[1] in valid_argvs:
            print(P("Iniciando Automação", color='blue'))
            try:
                valid_argvs[argv[1]]() # type: ignore
                Logs().register(status='Concluido', description="automação executou com exito!", csv_register=False)
            except Exception as error:
                print(P("um erro ocorreu durante a execução do script", color='red'))
                print(P((type(error),error),color='red'))
                Logs().register(status='Error', description="um erro aconteceu durante a execução da automação", exception=traceback.format_exc())
            
        else:
            print(P("argumento invalido", color='red'))
            informativo()
    else:
        informativo()