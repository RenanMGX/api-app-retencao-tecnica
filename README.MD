# ZenLinker

## Resumo

Este script é responsavel por interligar o app de retenção tecnica desenvolvido pelo power apps ao zendesk
o script consulta uma lista do sharepoint e atravez dela ele cria um chamado no zendesk e depois fica 
verificando a resposta do agente para salvar essas informaçoes de volta na lista para o aplicativo seguir com o fluxo

## Módulos e Arquivos

O script foi desenvolvido em orientação a objetos e dividido em vaior modulos. o arquivo princial é `main.py`
que vai exigir alguns argumentos para a execução como:

- **start** para dar inicio ao script
- **test** para modulos de teste

## Tecnologias Utilizadas

- **python**: Linguagem de programação principal do sistema.
- **Pandas**: Biblioteca para manipulação e análise de dados.
- **Office365-REST-Python-Clien**: Biblioteca para manipulação da lista no sharepoint
- **Requests**: Biblioteca para fazer chamadas API-REST