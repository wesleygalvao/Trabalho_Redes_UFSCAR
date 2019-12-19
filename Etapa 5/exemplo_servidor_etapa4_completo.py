#!/usr/bin/env python3

# Note que não é mais necessário fazer a gambiarra com o iptables que era feita
# nas etapas anteriores, pois agora nosso código Python vai assumir o controle
# de TODAS as camadas da rede!

# Este é um exemplo de um programa que faz eco, ou seja, envia de volta para
# o cliente tudo que for recebido em uma conexão.

import asyncio
from camadafisica import PTY
from mytcp import Servidor   # copie o arquivo da Etapa 2
from myip import CamadaRede  # copie o arquivo da Etapa 3
from myslip import CamadaEnlace

# Cria uma lista(dicionário) para conexões de outros clientes
lista_apelidos = {}

lista_msgs = {}

# Envia mensagem para todos os usuários conectados
def mensagem_para_todos(mensagem):
    for sock in lista_apelidos:
        sock.enviar(mensagem)

def dados_recebidos(conexao, dados):
    if dados == b'':
        if lista_apelidos[conexao] != False:
            mensagem = "/quit " + ''.join(lista_apelidos[conexao]) + "\n"
            mensagem_para_todos(mensagem.encode())
        del lista_apelidos[conexao]
        del lista_msgs[conexao]
        conexao.fechar()
    else:
        stringdados = dados.decode()
        for i in range (len(stringdados)):
            lista_msgs[conexao] += stringdados[i].encode()
            if stringdados[i] == "\n":
                data = lista_msgs[conexao].decode()
                data = data.split()
                if data!=[] and data[0] == "/nick":
                    print(data.__len__())
                    if data.__len__() == 1:
                        conexao.enviar(b"/error\n")
                    # Verifica se o nick não possui os caracteres ':' ou ' '
                    elif data[1].count(':') > 0 or data.__len__() > 2 or data.__len__() == 1:
                        conexao.enviar(b"/error\n")
                    else:
                        condicional = False
                        for key in lista_apelidos:
                            if lista_apelidos[key] == data[1]:
                                condicional = True
                        if condicional == True:
                            conexao.enviar(b"/error\n")
                        else:
                            # Define um apelido para a conexão, avisando a todos do chat
                            if lista_apelidos[conexao] == False:
                                lista_apelidos[conexao] = data[1]
                                mensagem = "/joined " + ''.join(lista_apelidos[conexao]) + "\n"
                                mensagem_para_todos(mensagem.encode())
                            # Renomeia o apelido para a conexão, avisando a todos do chat
                            else:
                                mensagem = "/renamed " + ''.join(lista_apelidos[conexao]) + " "+ ''.join(data[1:data.__len__()]) +"\n"
                                mensagem_para_todos(mensagem.encode())
                                lista_apelidos[conexao] = data[1]
                else:
                    # Erro caso uma conexão tente enviar uma mensagem sem antes ter definido um apelido para si
                    if lista_apelidos[conexao] == False:
                        conexao.enviar(b"/error\n")
                        # Uma mensagem é enviada a todos no chat
                    else:
                        mensagem = ''.join(lista_apelidos[conexao]) + ":"
                        for index in range (data.__len__()):
                            mensagem = mensagem + " " + ''.join(data[index])
                        mensagem = mensagem + "\n"
                        mensagem_para_todos(mensagem.encode())
                lista_msgs[conexao] = b""


def conexao_aceita(conexao):
    lista_apelidos[conexao]=False
    lista_msgs[conexao] = b""
    print ("Teste")
    conexao.fechar()
    conexao.registrar_recebedor(dados_recebidos)   # usa esse mesmo recebedor para toda conexão aceita


linha_serial = PTY()
outra_ponta = '192.168.123.1'
nossa_ponta = '192.168.123.2'
porta_tcp = 7000

print('Para conectar a outra ponta da camada física, execute:')
print('  sudo slattach -v -p slip {}'.format(linha_serial.pty_name))
print('  sudo ifconfig sl0 {} pointopoint {}'.format(outra_ponta, nossa_ponta))
print()
print('Para acessar o serviço, execute: nc {} 7000'.format(nossa_ponta))
print()

enlace = CamadaEnlace({outra_ponta: linha_serial})
rede = CamadaRede(enlace)
rede.definir_endereco_host(nossa_ponta)
rede.definir_tabela_encaminhamento([
    ('0.0.0.0/0', outra_ponta)
])
servidor = Servidor(rede, 7000)
servidor.registrar_monitor_de_conexoes_aceitas(conexao_aceita)
asyncio.get_event_loop().run_forever()
