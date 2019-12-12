import asyncio
import random
from mytcputils import *
import math
import time


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
        
        pseudohdr = str2addr(src_addr) + str2addr(dst_addr) + struct.pack('!HH', 0x0006, len(segment))
        if calc_checksum(pseudohdr + segment) != 0:
            print('descartando segmento com checksum incorreto')
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
        self.ack_no = random.randint(0, 0xffff)
        self.nextseqnum = self.ack_no
        self.sendbase = self.ack_no
        self.timer = None
        self.buffer = {}
        self.sample_rtt = 0
        self.estimated_rtt = 0
        self.dev_rtt = 0
        self.flag=0
        self.timeout_interval = 1
        self.timeBuffer = {}
        self.winsize = 1
        # Enviando SYN+ACK para aceitar conexão
        self.servidor.rede.enviar( fix_checksum(make_header(self.servidor.porta, self.id_conexao[1], self.ack_no,seq_no, FLAGS_SYN|FLAGS_ACK),self.id_conexao[2],self.id_conexao[0]),self.id_conexao[0])
        self.ack_no+=1    
        #self.timer = asyncio.get_event_loop().call_later(1, self._exemplo_timer)  # um timer pode ser criado assim; esta linha é só um exemplo e pode ser removida
        #self.timer.cancel()   # é possível cancelar o timer chamando esse método; esta linha é só um exemplo e pode ser removida

    def _rdt_rcv(self, seq_no, ack_no, flags, payload):
        # TODO: trate aqui o recebimento de segmentos provenientes da camada de rede.
        # Chame self.callback(self, dados) para passar dados para a camada de aplicação após
        # garantir que eles não sejam duplicados e que tenham sido recebidos em ordem.
        if ack_no == self.seqnum and len(payload) !=0:
            self.seqnum+= len(payload)
            self.servidor.rede.enviar( fix_checksum(make_header(self.servidor.porta, self.id_conexao[1], seq_no,self.seqnum, FLAGS_ACK),self.id_conexao[2],self.id_conexao[0]),self.id_conexao[0])
            self.callback(self,payload)            
            if seq_no>self.sendbase:
                self.sendbase = seq_no
            if seq_no == self.ack_no and self.flag==1:
                self.winsize+=1
                self.transmit()
        else:                        
            if seq_no>self.sendbase:
                self.sendbase = seq_no
                if seq_no<self.nextseqnum:
                    if self.timer != None:
                        self.timer.cancel()
                        self.timer = None
                    self.timer = asyncio.get_event_loop().call_later(self.timeout_interval, self.retransmit)
                elif self.timer!=None:
                    self.timer.cancel()
                    self.timer = None
                if self.flag==1:
                    if self.timeBuffer[seq_no]!= False:
                        self.sample_rtt = time.time() - self.timeBuffer[seq_no]
                        if self.estimated_rtt==0:
                            self.estimated_rtt=self.sample_rtt
                            self.dev_rtt=self.sample_rtt/2
                            self.timeout_interval =  self.estimated_rtt + 4*self.dev_rtt 
                        else:
                            self.dev_rtt =(0.75)*self.dev_rtt+ 0.25*abs(self.sample_rtt-self.estimated_rtt)
                            
                            self.estimated_rtt = (0.825)*self.estimated_rtt + 0.125*self.sample_rtt
                            self.timeout_interval = self.estimated_rtt + 4*self.dev_rtt 
                            
            if seq_no == self.ack_no and self.flag==1:
                self.winsize+=1 
                if self.timer!=None:
                    self.timer.cancel()
                    self.timer = None
                if seq_no<self.nextseqnum:
                    self.transmit()
        # Os métodos abaixo fazem parte da API

    def registrar_recebedor(self, callback):
        """
        Usado pela camada de aplicação para registrar uma função para ser chamada
        sempre que dados forem corretamente recebidos
        """
        self.callback = callback

    def transmit(self):
        for i in range(self.winsize):    
            if self.sendbase+i*MSS in self.buffer:
                self.timeBuffer[self.sendbase+(i+1)*MSS] = time.time()
                self.servidor.rede.enviar(fix_checksum(make_header(self.servidor.porta, self.id_conexao[1],
                             self.ack_no,self.seqnum, FLAGS_ACK)+self.buffer[self.sendbase+i*MSS],
                    self.id_conexao[2],self.id_conexao[0]),self.id_conexao[2])                
                self.ack_no += MSS 
            else:
                break      
        if self.timer ==None: 
            self.timer = asyncio.get_event_loop().call_later(self.timeout_interval, self.retransmit)
            
    
    def enviar(self, dados):
        """
        Usado pela camada de aplicação para enviar dados
        """
        # TO++DO: implemente aqui o envio de dados.
        # Chame self.servidor.rede.enviar(segmento, dest_addr) para enviar o segmento
        # que você construir para a camada de rede.
    
        tam = len(dados)
        i=0
        self.flag=1
        while True: 
            inic = i*MSS
            fim = (i+1)*MSS
            fim = fim
            self.buffer[self.sendbase+i*MSS] = dados[inic:fim]
            if tam<=MSS:
                break
            i+=1
            tam-=MSS        
        self.nextseqnum+= len(dados)
        self.transmit()
        pass
    
    def retransmit(self):      
        dados = self.buffer[self.sendbase]
        self.timeBuffer[self.sendbase+MSS] = False
        self.servidor.rede.enviar(fix_checksum(make_header(self.servidor.porta, self.id_conexao[1],
                         self.sendbase,self.seqnum, FLAGS_ACK)+dados,
                self.id_conexao[2],self.id_conexao[0]),self.id_conexao[2])   
        self.timer.cancel()
        self.timer = None
        self.timer = asyncio.get_event_loop().call_later(self.timeout_interval, self.retransmit)  
        self.winsize = self.winsize//2
        
        
    def fechar(self):
        """
        Usado pela camada de aplicação para fechar a conexão
        """
        self.servidor.rede.enviar( fix_checksum(make_header(self.servidor.porta, self.id_conexao[1], self.ack_no,self.nextseqnum, FLAGS_FIN),self.id_conexao[2],self.id_conexao[0]),self.id_conexao[0])
            
        # TODO: implemente aqui o fechamento de conexão
        pass
