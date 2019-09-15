#!/usr/bin/python3

# seu código aqui
import socket
import select


# Cria um socket 
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# Habita a opção SO_REUSEADDR
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
# Designa a porta 7000 ao socket e o permite escutá-la
s.bind(('', 7000))
s.listen(5)
# Cria uma lista para sockets
sockets_lista = [s]
# Cria uma lista(dicionário) para demais conexões de outros clientes
#dicionario = {}
# Socket aceita o pedido de cone
#conexao, endereco = s.accept() 
dicionario = {conexao:False}

# Buffering 
def recvline(conexao):
    buffer = ""
    while True:        
        data = conexao.recv(1) 
        buffer+= data.decode()
        if data == b"\n":
            return buffer
        if not data:
            return

while True:
    
    leitura_sockets, escrita_sockets, error_sockets, = select.select(sockets_lista, [], [])

    for socket_notificado in leitura_sockets:

        if socket_notificado == s:
            conexao, endereco = s.accept()
            sockets_lista.append(conexao)                       
        else:
            try:
                data = recvline(conexao)
                if not data: break       # stop if client stopped
                data = data.split()
                if data[0] == "/nick":
                    if data[1:data.__len__()].count(':') > 0 or data[1:data.__len__()].count(' ')>0:
                        conexao.send(b"/error\n")
                    else:
                        if dicionario[conexao] == False:
                            dicionario[conexao] = data[1:data.__len__()]
                            mensagem = "/joined " + ''.join(dicionario[conexao]) + "\n"
                            conexao.send(mensagem.encode())
                        else:
                            mensagem = "/renamed " + ''.join(dicionario[conexao]) + " "+ ''.join(data[1:data.__len__()]) +"\n"
                            conexao.send(mensagem.encode())
                            dicionario[conexao] = data[1:data.__len__()]
                else:
                    if dicionario[conexao] == False:
                            conexao.send(b"/error\n")
                    else:
                            mensagem = ''.join(dicionario[conexao]) + ": "+ ''.join(data) +"\n"
                            conexao.send(mensagem.encode())
            except:
                continue 
conexao.close() 

