from myiputils import *
import random

class CamadaRede:
    def __init__(self, enlace):
        """
        Inicia a camada de rede. Recebe como argumento uma implementação
        de camada de enlace capaz de localizar os next_hop (por exemplo,
        Ethernet com ARP).
        """
        self.callback = None
        self.enlace = enlace
        self.enlace.registrar_recebedor(self.__raw_recv)
        self.meu_endereco = None
        self.tabela = []

    def __raw_recv(self, datagrama):
        dscp, ecn, identification, flags, frag_offset, ttl, proto, \
           src_addr, dst_addr, payload = read_ipv4_header(datagrama)
        if dst_addr == self.meu_endereco:
            # atua como host
            if proto == IPPROTO_TCP and self.callback:
                self.callback(src_addr, dst_addr, payload)
        else:
            # atua como roteador
            next_hop = self._next_hop(dst_addr)
            # TODO: Trate corretamente o campo TTL do datagrama
            self.enlace.enviar(datagrama, next_hop)

    def _next_hop(self, dest_addr):
        # TODO: Use a tabela de encaminhamento para determinar o próximo salto
        # (next_hop) a partir do endereço de destino do datagrama (dest_addr).
        # Retorne o next_hop para o dest_addr fornecido.
        dest_addr = dest_addr.split('.')
        dest = ''
        for i in range(4):
            dest+= '{0:08b}'.format(int(dest_addr[i]))
            
        encaminha = -1
        maxPrefixo = -1
        for i in range(len(self.tabela)):
            endereco = self.tabela[i][0].split('/')
            num = endereco[1]
            endereco = endereco[0]
            endereco = endereco.split('.')
            end = ''
            for j in range(4):
                end+= '{0:08b}'.format(int(endereco[j]))
            maxPrefix=0
            for k in range(int(num)):
                if dest[k] == end[k]:
                    maxPrefix+=1
                else:
                    break
            if maxPrefix==int(num) and maxPrefix>maxPrefixo:
                
                maxPrefixo = maxPrefix
                encaminha = i
        
        if encaminha==-1:
            return None
        else:
            next_hop = self.tabela[encaminha][1]   
            return next_hop
        pass

    def definir_endereco_host(self, meu_endereco):
        """
        Define qual o endereço IPv4 (string no formato x.y.z.w) deste host.
        Se recebermos datagramas destinados a outros endereços em vez desse,
        atuaremos como roteador em vez de atuar como host.
        """
        self.meu_endereco = meu_endereco

    def definir_tabela_encaminhamento(self, tabela):
        """
        Define a tabela de encaminhamento no formato
        [(cidr0, next_hop0), (cidr1, next_hop1), ...]

        Onde os CIDR são fornecidos no formato 'x.y.z.w/n', e os
        next_hop são fornecidos no formato 'x.y.z.w'.
        """
        self.tabela = tabela
        # TODO: Guarde a tabela de encaminhamento. Se julgar conveniente,
        # converta-a em uma estrutura de dados mais eficiente.
        pass

    def registrar_recebedor(self, callback):
        """
        Registra uma função para ser chamada quando dados vierem da camada de rede
        """
        self.callback = callback

    def enviar(self, segmento, dest_addr):
        """
        Envia segmento para dest_addr, onde dest_addr é um endereço IPv4
        (string no formato x.y.z.w).
        """
        # TODO: Assumindo que a camada superior é o protocolo TCP, monte o
        # datagrama com o cabeçalho IP, contendo como payload o segmento.
        def twos_comp(val, bits):
            """compute the 2's complement of int value val
            https://stackoverflow.com/questions/1604464/twos-complement-in-python"""
            if (val & (1 << (bits - 1))) != 0: # if sign bit is set e.g., 8bit: 128-255
                val = val - (1 << bits)        # compute negative value
            return val                         # return positive value as is

        def make_ipv4_header(size,src_addr,dest_addr):
            
            # Internet Protocol Version
            ip_version = 4 << 4
            ihl = 5
            vihl = ip_version | ihl

            # Differentiate Servic Field
            dscp = 0 << 2
            ecn  = 0
            dscpecn = dscp | ecn

            # Total Length
            total_length = 20+size

            # Identification
            identification = random.randint(0, 2**16)
                
            # Flags
            flag_rsv = 0
            flag_dtf = 0
            flag_mrf = 0
            frag_offset = 0
            flags = (flag_rsv << 7) + (flag_dtf << 6) + (flag_mrf << 5) + (frag_offset)          

            # Time to Live
            ttl = 64
            # Protocol
            proto = IPPROTO_TCP 
            # Check Sum 
            checksum = 0
            # Source Address
            src_addr = str2addr(src_addr)
            # Destination Address
            dest_addr = str2addr(dest_addr)
            header = struct.pack('!BBHHHBBH', vihl, dscpecn, total_length, identification, 0, 64, proto, checksum) + src_addr + dest_addr
            checksum = calc_checksum(header[:4*ihl])
            header = struct.pack('!BBHHHBBH', vihl, dscpecn, total_length, identification, flags, ttl, proto, checksum) + src_addr + dest_addr
            return header
        
        next_hop = self._next_hop(dest_addr)
        datagrama = make_ipv4_header(len(segmento),self.meu_endereco, dest_addr) + segmento
        self.enlace.enviar(datagrama, next_hop)
