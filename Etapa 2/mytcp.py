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
            conexao = self.conexoes[id_conexao] = Conexao(self, id_conexao,seq_no+1)
            # TODO: você precisa fazer o handshake aceitando a conexão. Escolha se você achar melhor
            # fazer aqui mesmo ou dentro da classe Conexao.
            # Criado um número de sequência aleatório
            if self.callback:
                self.callback(conexao)
        elif (flags & FLAGS_FIN) == FLAGS_FIN:
            string=b''
            self.conexoes[id_conexao].callback(self,string)
            seq_no1 = random.randint(0, 0xffff)
            self.rede.enviar( fix_checksum(make_header(self.porta, src_port,seq_no1,seq_no+1, FLAGS_ACK),dst_addr,src_addr),dst_addr)
        elif id_conexao in self.conexoes:
            # Passa para a conexão adequada se ela já estiver estabelecida
            self.conexoes[id_conexao]._rdt_rcv(ack_no,seq_no,flags,payload)
        else:
            print('%s:%d -> %s:%d (pacote associado a conexão desconhecida)' %
                  (src_addr, src_port, dst_addr, dst_port))


class Conexao:
    def __init__(self, servidor, id_conexao,seq_no):
        self.servidor = servidor
        self.id_conexao = id_conexao
        self.seqnum = seq_no
        self.callback = None
        self.seq_no1 = random.randint(0, 0xffff)
        self.nextseqnum = seq_no
        self.sendbase = seq_no
        # Enviando SYN+ACK para aceitar conexão
        self.servidor.rede.enviar( fix_checksum(make_header(self.servidor.porta, self.id_conexao[1], self.seq_no1,seq_no, FLAGS_SYN|FLAGS_ACK),self.id_conexao[2],self.id_conexao[0]),self.id_conexao[0])
        self.seq_no1+=1    
        #self.timer = asyncio.get_event_loop().call_later(1, self._exemplo_timer)  # um timer pode ser criado assim; esta linha é só um exemplo e pode ser removida
        #self.timer.cancel()   # é possível cancelar o timer chamando esse método; esta linha é só um exemplo e pode ser removida

    def _exemplo_timer(self):
        # Esta função é só um exemplo e pode ser removida
        print('Este é um exemplo de como fazer um timer')

    def _rdt_rcv(self, seq_no, ack_no, flags, payload):
        # TODO: trate aqui o recebimento de segmentos provenientes da camada de rede.
        # Chame self.callback(self, dados) para passar dados para a camada de aplicação após
        # garantir que eles não sejam duplicados e que tenham sido recebidos em ordem.=
        if ack_no == self.seqnum and len(payload) !=0:
            self.seqnum+= len(payload)
            self.servidor.rede.enviar( fix_checksum(make_header(self.servidor.porta, self.id_conexao[1], seq_no,self.seqnum, FLAGS_ACK),self.id_conexao[2],self.id_conexao[0]),self.id_conexao[0])
            self.callback(self,payload)
        #else: 
         #   print("fim")
          #  self.timer.cancel()
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
    
        tam = len(dados)
        i=0
        while True: 
            self.servidor.rede.enviar(fix_checksum(make_header(self.servidor.porta, self.id_conexao[1],
                         self.seq_no1,self.seqnum, FLAGS_ACK)+dados[i*MSS:(i+1)*MSS],
                self.id_conexao[2],self.id_conexao[0]),self.id_conexao[2])
            self.seq_no1 += MSS 
            if tam<=MSS:
                break
            i+=1
            tam-=MSS        
        self.nextseqnum+= len(dados)
        #print("iniciado")
        #self.timer = asyncio.get_event_loop().call_later(1, self.retransmit(dados))
        pass
    
    def retransmit(self,dados):
        tam = len(dados)
        i=0
            
        
        
    def fechar(self):
        """
        Usado pela camada de aplicação para fechar a conexão
        """
        self.servidor.rede.enviar( fix_checksum(make_header(self.servidor.porta, self.id_conexao[1], self.seq_no1,self.nextseqnum, FLAGS_FIN),self.id_conexao[2],self.id_conexao[0]),self.id_conexao[0])
            
        # TODO: implemente aqui o fechamento de conexão
        pass
