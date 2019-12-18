#!/usr/bin/env python3
# Este é um exemplo de um programa que faz eco, ou seja, envia de volta para
# o cliente tudo que for recebido em uma conexão.

import asyncio
from camadafisica_zybo import ZyboSerialDriver
from mytcp import Servidor       # copie o arquivo da Etapa 2
from myip import CamadaRede      # copie o arquivo da Etapa 3
from myslip import CamadaEnlace  # copie o arquivo da Etapa 4

# Implementação da camada de aplicação

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



# Integração com as demais camadas

driver = ZyboSerialDriver()
linha_serial = driver.obter_porta(4)
pty = driver.expor_porta_ao_linux(5)
outra_ponta = '192.168.123.1'
nossa_ponta = '192.168.123.2'
porta_tcp = 7000

print('Conecte o RX da porta 4 com o TX da porta 5 e vice-versa.')
print('Para conectar a outra ponta da camada física, execute:')
print()
print('sudo slattach -vLp slip {}'.format(pty.pty_name))
print('sudo ifconfig sl0 {} pointopoint {} mtu 1500'.format(outra_ponta, nossa_ponta))
print()
print('Acesse o serviço com o comando: nc {} {}'.format(nossa_ponta, porta_tcp))
print()

enlace = CamadaEnlace({outra_ponta: linha_serial})
rede = CamadaRede(enlace)
rede.definir_endereco_host(nossa_ponta)
rede.definir_tabela_encaminhamento([
    ('0.0.0.0/0', outra_ponta)
])
servidor = Servidor(rede, porta_tcp)
servidor.registrar_monitor_de_conexoes_aceitas(conexao_aceita)
asyncio.get_event_loop().run_forever()

