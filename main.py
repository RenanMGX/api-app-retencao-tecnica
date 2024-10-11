from getpass import getuser
from typing import Dict, List
from Entities.dependencies.credenciais import Credential
from Entities.dependencies.functions import P
from Entities.extract_request import APISharePoint, pd
import sys
from Entities.dependencies.logs import Logs
import traceback
from Entities.zendesk import APIZendesk
from datetime import datetime
from time import sleep
from PyPDF2 import PdfMerger
import os
import numpy as nb
import shutil


def test():
    print("testado")

class Execute:
    @property
    def tratamento_inicial(self) -> str:
        hora = datetime.now().hour
        if (hora > 6) and (hora < 12):
            return "Bom dia"
        elif (hora > 12) and (hora < 18):
            return "Boa tarde"
        else:
            return "Boa noite"    
        
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
        """
        Método principal que inicia a execução das etapas de criação e consulta de chamados.
        """
        while True:
            print(P("Fazendo nova verificação"))
            
            # Inicia a criação de chamados na etapa 1
            self.criar_chamado_etapa_1()
            
            # Inicia a consulta de chamados na etapa 2
            self.consultar_chamado_etapa_2()
            
            sleep(10) # delay para aguardar o pdf subir para o app
            # Inicia a transferencia dos arquivos pdf punificados para a pasta destino
            self.coletar_arquivos_controle_etapa_3(target_path=r'\\server008\G\ARQ_PATRIMAR\WORK\Notas Fiscais Digitalizadas\RETENÇÃO TÉCNICA')
            
            print(P("Verificação encerrada!"))
            sleep(15*60)
        # Imprime mensagem de finalização do script
        print(P("Finalizando Script", color='white'))
            
    def criar_chamado_etapa_1(self):
        """
        Método para criar chamados no Zendesk a partir de solicitações listadas no SharePoint.
        
        Este método consulta o SharePoint para obter solicitações com anexos, filtra as que ainda não possuem um número de chamado no Zendesk,
        e então cria um chamado no Zendesk para cada solicitação filtrada. Se a criação do chamado for bem-sucedida, o número do chamado é atualizado
        no SharePoint. Em caso de erro, o erro é registrado nos logs.

        Returns:
            None
        """
        # Imprime uma mensagem indicando que a listagem de solicitações para abrir chamados está em andamento
        print(P("listando solicitação para abrir chamado"))
        
        # Consulta o SharePoint para obter dados com anexos
        self.__sharePoint.consultar(with_attachment=True)
        
        # Obtém o DataFrame com os dados do SharePoint
        df = self.__sharePoint.df
        
        try:
            # Filtra as linhas que não possuem um número de chamado no Zendesk
            df = df[~df['NumChamadoZendesk'].notnull()]
        except KeyError:
            # Se a coluna 'NumChamadoZendesk' não existir, ignora o erro
            pass
        
        # Verifica se o DataFrame está vazio após a filtragem
        if df.empty:
            # Imprime uma mensagem indicando que não há chamados para criar
            print(P("Nenhum chamado para Criar", color='cyan'))
            return
        
        # Itera sobre as linhas do DataFrame
        for row, value in df.iterrows():
            # Cria a descrição do chamado
            descri = f"""
            {self.tratamento_inicial}.\n
            Gentileza verificar se o Empreiteiro indicado abaixo e se anexo possuí ações judiciais que o impeçam de receber seu saldo de retenção técnica.\n
            CNPJ: {value['CnpjFormatado']}\n 
            EMPREITEIRO: {value['NomeEmpreiteiro']}\n
            \n
            \n
            este chamado foi aberto automaticamente por nosso sistema robótico.
            """
            
            # Cria um chamado no Zendesk
            response: dict = self.__zendesk.add(
                marca='juridico',
                titulo=f"Liberação de Retenção - EMPREITEIRO {value['NomeEmpreiteiro']}",
                descri=descri,
                ticket_form_id=11062047187479,
                tags=[
                    "controle_obras_255",
                    "parecer_jurídico" 
                    ],
                fields=[
                    {
                        'id':11062650498327,
                        'value':"controle_obras_255"
                    },
                    {
                        'id':11062458183319,
                        'value':"parecer_jurídico"
                    },
                    {
                        'id':11062562491159,
                        'value':f"{value['CodigoEmpreendimento']} - {value['NomeEmpreendimento']}"
                    },
                    {
                        'id':11062574075671,
                        'value':True
                    }
                    
                ],
                attachment_path=value['Attachment_Path']
            )
            
            # Verifica se o chamado foi criado com sucesso
            if response.get('status_code') == 201:
                # Obtém o ID do chamado criado
                ticket: str = response.get('response').get('ticket').get('id')  # type: ignore
                
                # Atualiza o número do chamado no SharePoint
                self.__sharePoint.alterar(int(value['Id']), coluna='NumChamadoZendesk', valor=str(ticket))
                
                # Imprime uma mensagem indicando que o chamado foi criado com sucesso
                print(P(f"chamado criado no zendesk {ticket}", color='green'))
            else:
                # Imprime uma mensagem de erro se a criação do chamado falhar
                print(P("error ao abrir um chamado: ", color='red'))
                print(P(response))
                
                # Registra o erro nos logs
                Logs().register(status='Error', description="erro ao abrir um chamado", exception=str(response))
                    
    def consultar_chamado_etapa_2(self):
        """
        Consulta os chamados no SharePoint e verifica o status no Zendesk.
        Atualiza o status de aprovação no SharePoint com base na resposta do Zendesk.
        """
        print(P("listando solicitação para consultar retorno do Juridico"))
        
        # Consulta os dados no SharePoint
        self.__sharePoint.consultar()
        df = self.__sharePoint.df
        
        try:
            # Filtra os dados para incluir apenas aqueles com número de chamado no Zendesk
            df = df[df['NumChamadoZendesk'].notnull()]
        except KeyError:
            pass
        
        if df.empty:
            print(P("nenhum chamado para consultar no Juridico", color='cyan'))
            return
        
        # Itera sobre cada linha do DataFrame
        for row, value in df.iterrows():
            print(P(f"verificando chamado '{value['NumChamadoZendesk']}' da solicitaçao no app '{value['Id']}'", color='yellow'))
            
            # Consulta o status do chamado no Zendesk
            response: dict = self.__zendesk.get(str(value['NumChamadoZendesk']))
            
            if response.get('status_code') == 200:
                
                ticket: dict = response.get('response').get('ticket')  # type: ignore
                status = ticket.get('status')
                
                # Verifica se o chamado está resolvido ou fechado
                if (status != "solved") and (status != "closed"):
                    print(P("o chamado ainda não está fechado!", color='yellow'))
                    continue
                
                
                # Obtém os campos personalizados do ticket
                fields = {x['id']: x['value'] for x in ticket.get('fields')}  # type: ignore
                custom_fields = {x['id']: x['value'] for x in ticket.get('custom_fields')}  # type: ignore
                
                
                # Atualiza o status de aprovação no SharePoint com base nos campos personalizados
                if (fields.get(25245062103831) == "sim_pend_consultivo") and (custom_fields.get(25245062103831) == "sim_pend_consultivo"):
                    self.__sharePoint.alterar(int(value['Id']), coluna='AprovacaoJuridico', valor='Recusado')
                    print(P("existe pendencias", color='red'))
                elif (fields.get(25245062103831) == "não_pend_consultivo") and (custom_fields.get(25245062103831) == "não_pend_consultivo"):
                    self.__sharePoint.alterar(int(value['Id']), coluna='AprovacaoJuridico', valor='Aprovado')
                    
                    print(P("não existe pendencias", color='green'))
                else:
                    print(P("ainda sem resposta", color='yellow'))
                    continue
                
                comments = self.__zendesk.get(str(value['NumChamadoZendesk']), type='comments').get('response').get('comments')#type: ignore
                if len(comments) > 1:
                    comments = comments[-1].get('body')# type: ignore
                else:
                    comments = "Sem Comentario"
                    
                    
                dateSTR = datetime.fromisoformat(ticket.get('updated_at')).strftime('%m/%d/%Y')# type: ignore
                if not dateSTR:
                    dateSTR = ""
                    
                user = self.__zendesk.get(str(ticket.get('assignee_id')), type='user').get('response').get('user').get('name') #type: ignore
                if not user:
                    user = "Não Identificado"
                
                self.__sharePoint.alterar(int(value['Id']), coluna='ResponsavelJuridico', valor=user)
                self.__sharePoint.alterar(int(value['Id']), coluna='ComentarioJuridico', valor=comments)
                self.__sharePoint.alterar(int(value['Id']), coluna='ConclusaoJuridico', valor=dateSTR)
                
            
            else:
                print(P('não foi encontrada', color='red'))
            
            
            print(P("Verificação de chamado encerrada"))            
        
    def coletar_arquivos_controle_etapa_3(self, target_path:str=f'C:\\Users\\{getuser()}\\Downloads'):
        if not os.path.exists(target_path):
            Logs().register(status='Error', description=f"o caminho '{target_path}' não foi encontrado")
            return
        
        # Consulta os dados no SharePoint
        df:pd.DataFrame = self.__sharePoint.coletar_arquivos_controle().df
        
        if df.empty:
            print(P("sem arquivo do controle para enviar"))
            return
        
        for row, value in df.iterrows():
            if not value['Attachment_Path'] is nb.nan:
                # List of PDF files to merge
                pdf_files:List[str] = value['Attachment_Path']
                
                
                # Create a PdfMerger object
                merger = PdfMerger()

                # Loop through the list and append each PDF to the merger object
                for pdf_file in pdf_files:
                    if pdf_file.endswith('.pdf'):
                        merger.append(pdf_file)
                    else:
                        Logs().register(status='Error', description=f"o arquivo {pdf_file} não é um pdf")     

                # Write out the merged PDF
                if merger.id_count > 0:
                    download_temp:str = os.path.join(os.getcwd(), 'download')
                    if not os.path.exists(download_temp):
                        os.makedirs(download_temp)
                    file_path:str = os.path.join(download_temp, f"{value['Id']}-RetençãoTécnica_{value['CodigoBP']}_{value['CodigoEmpreendimento']}.pdf")
                    
                    merger.write(file_path)
                    shutil.move(file_path, target_path)
                    
                    # Atualiza o número do chamado no SharePoint
                    self.__sharePoint.alterar(int(value['Id']), coluna='RegistroArquivoControle', valor="Copiado")
                else:
                    Logs().register(status='Error', description="a coluna de anexo esta vazia1") 
                merger.close()
            else:    
                Logs().register(status='Error', description="a coluna de anexo esta vazia2")     
        
        
    def test(self):
        print("testado")
        
        #self.coletar_arquivos_controle_etapa_3(target_path=r'\\server008\G\ARQ_PATRIMAR\WORK\Notas Fiscais Digitalizadas\RETENÇÃO TÉCNICA')
        #self.__sharePoint.alterar(304, coluna='NumChamadoZendesk', valor="52308")

if __name__ == "__main__":
    execute = Execute()
    valid_argvs:Dict[str, object] = {
        "start" : execute.start,
        "teste" : execute.test
    }
    
    def informativo():
        """
        Função que imprime os argumentos válidos para a execução do script.
        """
        print("informe apenas os argumentos validos:")
        for arg in list(valid_argvs.keys()):
            print(P(arg))
    
    argv = sys.argv
    if len(argv) > 1:
        if argv[1] in valid_argvs:
            
            
            print(P("Iniciando Automação", color='blue'))
            try:
                # Executa a função correspondente ao argumento fornecid
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
        