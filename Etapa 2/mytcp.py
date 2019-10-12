import asyncio
import random
from mytcputils import *
import math


class Servidor:
    def __init__(self, rede, porta):
        self.rede = rede
        self.porta = porta
        self.conexoes = {}
        self.callback = None
        self.rede.registrar_recebedor(self._rdt_rcv)

    def registrar_monitor_de_conexoes_aceitas(self, callback):
        """
        Usado pela camada de aplicação para registrar uma função para ser chamada
        sempre que uma nova conexão for aceita
        """
        self.callback = callback

    def _rdt_rcv(self, src_addr, dst_addr, segment):
        src_port, dst_port, seq_no, ack_no, \
            flags, window_size, checksum, urg_ptr = read_header(segment)

        if dst_port != self.porta:
            # Ignora segmentos que não são destinados à porta do nosso servidor
            return

        payload = segment[4*(flags>>12):]
        id_conexao = (src_addr, src_port, dst_addr, dst_port)

        if (flags & FLAGS_SYN) == FLAGS_SYN:
            # A flag SYN estar setada significa que é um cliente tentando estabelecer uma conexão nova
            # TODO: talvez você precise passar mais coisas para o construtor de conexão
            conexao = self.conexoes[id_conexao] = Conexao(self, id_conexao)
            # TODO: você precisa fazer o handshake aceitando a conexão. Escolha se você achar melhor
            # fazer aqui mesmo ou dentro da classe Conexao.
            # Criado um número de sequência aleatório
            seq_no1 = random.randint(0, 0xffff)
            # Enviando SYN+ACK para aceitar conexão
            self.rede.enviar( fix_checksum(make_header(self.porta, src_port, seq_no1,seq_no+1, FLAGS_SYN|FLAGS_ACK),dst_addr,src_addr),src_addr)
            if self.callback:
                self.callback(conexao)
        elif id_conexao in self.conexoes:
            # Passa para a conexão adequada se ela já estiver estabelecida
            self.conexoes[id_conexao]._rdt_rcv(payload)
        else:
            print('%s:%d -> %s:%d (pacote associado a conexão desconhecida)' %
                  (src_addr, src_port, dst_addr, dst_port))


class Conexao:
    def __init__(self, servidor, id_conexao):
        self.servidor = servidor
        self.id_conexao = id_conexao
        self.callback = None
        #self.timer = asyncio.get_event_loop().call_later(1, self._exemplo_timer)  # um timer pode ser criado assim; esta linha é só um exemplo e pode ser removida
        #self.timer.cancel()   # é possível cancelar o timer chamando esse método; esta linha é só um exemplo e pode ser removida

    def _exemplo_timer(self):
        # Esta função é só um exemplo e pode ser removida
        print('Este é um exemplo de como fazer um timer')

    def _rdt_rcv(self, payload):
        # TODO: trate aqui o recebimento de segmentos provenientes da camada de rede.
        # Chame self.callback(self, dados) para passar dados para a camada de aplicação após
        # garantir que eles não sejam duplicados e que tenham sido recebidos em ordem.
        
        ultimo_recebido = -1
        primeiro_janela = 0
     
        while True:

            try:
                #Compara o checksum original do segmento com o checksum recebido. 
                if self.calc_checksum(payload) == self.checksum:
                    if self.seq_no == ultimo_recebido + 1:
                        print("ACK enviado ao remetente") + str(self.seq_no)
                        #TODO: Enviar ACK de confirmação
                        ultimo_recebido = self.seq_no
                    elif self.seq_no != ultimo_recebido + 1 and self.seq_no > ultimo_recebido + 1:
                        #Verifica se o pacote está fora de ordem
                        if ultimo_recebido >= 0:
                            print("Pacote fora de ordem") + str(ultimo_recebido)
                    #TODO: Verificar se está duplicado
                    else:
                        print("ACK enviado ao remetente") + str(self.seq_no)
                        #TODO: Enviar ACK de confirmação
                #Descarta o pacote se nenhuma condição for atendida        
                else:
                    print("Pacote descartado.")

        print('recebido payload: %r' % payload)

    # Os métodos abaixo fazem parte da API

    def registrar_recebedor(self, callback):
        """
        Usado pela camada de aplicação para registrar uma função para ser chamada
        sempre que dados forem corretamente recebidos
        """
        self.callback = callback

    def enviar(self, dados):
        """
        Usado pela camada de aplicação para enviar dados
        """
        # TODO: implemente aqui o envio de dados.
        # Chame self.servidor.rede.enviar(segmento, dest_addr) para enviar o segmento
        # que você construir para a camada de rede.
        pass

    def fechar(self):
        """
        Usado pela camada de aplicação para fechar a conexão
        """
        # TODO: implemente aqui o fechamento de conexão
        pass
