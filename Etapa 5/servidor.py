#!/usr/bin/python3

import asyncio
from camadarede import CamadaRedeLinux
from mytcp import Servidor



# Cria uma lista(dicionário) para demais conexões de outros clientes
lista_apelidos = {}
# Lista a ser usada no Passo 5 (AINDA NÃO USADA)
lista_msgs = {}

sockets_lista = []
# Envia mensagem para todos os usuários conectados
def mensagem_para_todos(mensagem):
    for sock in lista_apelidos:
        sock.enviar(mensagem)


# Buffering 
# Valores de retorno:
# 1: mensagem terminada com \n pronto para ser tratada
# 2: conexão fechada
# 3: lido um caracterer diferente de \n, não faz nada
def dados_recebidos(conexao, dados):
    if dados == b'':
        #sockets_lista.remove(conexao)
        #if lista_apelidos[conexao] != False:
        #    mensagem = "/quit " + ''.join(lista_apelidos[conexao]) + "\n"
        #    mensagem_para_todos(mensagem.encode())
        #del lista_apelidos[conexao]
        #del lista_msgs[conexao]
        conexao.fechar()
    else:
        stringdados = dados.decode()
        for i in range (len(stringdados)):
            lista_msgs[conexao] += stringdados[i].encode()
            if stringdados[i] == "\n":
                data = lista_msgs[conexao].decode()
                data = data.split()
                if data!=[] and data[0] == "/nick":
                    # Verifica se o nick não possui os caracteres ':' ou ' ' e se já não existe um nick igual pertencente a outra conexão
                    if data[1:data.__len__()].count(':') > 0 or data[1:data.__len__()].count(' ')>0 or data[1:data.__len__()] in lista_apelidos.values():
                        conexao.enviar(b"/error\n")
                    else:
                        # Define um apelido para a conexão, avisando a todos do chat
                        if lista_apelidos[conexao] == False:
                            lista_apelidos[conexao] = data[1:data.__len__()]
                            mensagem = "/joined " + ''.join(lista_apelidos[conexao]) + "\n"
                            mensagem_para_todos(mensagem.encode())
                        # Renomeia o apelido para a conexão, avisando a todos do chat
                        else:
                            mensagem = "/renamed " + ''.join(lista_apelidos[conexao]) + " "+ ''.join(data[1:data.__len__()]) +"\n"
                            mensagem_para_todos(mensagem.encode())
                            lista_apelidos[conexao] = data[1:data.__len__()]
                else:
                    # Erro caso uma conexão tente enviar uma mensagem sem antes ter definido um apelido para si
                    if lista_apelidos[conexao] == False:
                        conexao.enviar(b"/error\n")
                        # Uma mensagem é enviada a todos no chat
                    else:
                        mensagem = ''.join(lista_apelidos[conexao]) + ": "+ ''.join(data) +"\n"
                        mensagem_para_todos(mensagem.encode())
                lista_msgs[conexao] = b""
        

def conexao_aceita(conexao):
    sockets_lista.append(conexao)
    lista_apelidos[conexao]=False
    lista_msgs[conexao] = b""
    print ("Teste")
    conexao.fechar()
    conexao.registrar_recebedor(dados_recebidos)   # usa esse mesmo recebedor para toda conexão aceita
    
rede = CamadaRedeLinux()
s = Servidor(rede, 7000)
s.registrar_monitor_de_conexoes_aceitas(conexao_aceita)
asyncio.get_event_loop().run_forever()

