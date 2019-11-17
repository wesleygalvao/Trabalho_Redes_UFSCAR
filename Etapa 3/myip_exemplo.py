from myiputils import *
from mytcputils import *
import sys
 
 
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
           
           
            dec_ttl = ttl - 1
            unpacked = struct.unpack('!BBHHHBBHII', datagrama)
 
            new_datagrama = struct.pack('!BBHHHBBHII',
                unpacked[0],    # IP Version
                unpacked[1],    # Differentiate Service Feild
                unpacked[2],    # Total Length
                unpacked[3],    # Identification
                unpacked[4],    # Flags
                dec_ttl,        # Time to leave
                unpacked[6],    # protocol
                0,              # Checksum
                unpacked[8],    # Source IP
                unpacked[9]     # Destination IP
            )
 
            ckm = calc_checksum(new_datagrama)
 
            new_datagrama = struct.pack('!BBHHHBBHII',
                unpacked[0],    # IP Version
                unpacked[1],    # Differentiate Service Feild
                unpacked[2],    # Total Length
                unpacked[3],    # Identification
                unpacked[4],    # Flags
                dec_ttl,        # Time to leave
                unpacked[6],    # protocol
                ckm,            # Checksum
                unpacked[8],    # Source IP
                unpacked[9]     # Destination IP
            )
 
            error_datagrama = struct.pack('!BBH',
                11,     # Type = 11
                0,      # Code = 0 ou 1 (tempo em transito/reassembly timeout)
                0,      # Header Checksum
            )
 
            error_ckm = calc_checksum(error_datagrama)
           
            error_datagrama = struct.pack('!BBH',
                11,         # Type = 11
                0,          # Code = 0 ou 1 (tempo em transito/reassembly timeout)
                error_ckm,  # Header Checksum
            )
 
            error_datagrama = error_datagrama + datagrama[:28]
 
 
 
            if(dec_ttl != 0):
                self.enlace.enviar(new_datagrama, next_hop)
            elif(dec_ttl == 0):
                #self.enlace.enviar(error_datagrama, next_hop)
                pass
 
    def _next_hop(self, dest_addr):
        # [(cidr0, next_hop0), (cidr1, next_hop1), ...]
        datagrama_ip = ip2bin(dest_addr)
 
        matched = []
 
        for entrada in self.tabela:
            netmask = entrada2netmask(entrada[0])
           
            separado = entrada[0].split('/')
            entrada_ip = separado[0]
            entrada_ip = ip2bin(entrada_ip)
 
            masked_ip = andStr(entrada_ip, netmask)
            masked_datagrama = andStr(datagrama_ip, netmask)
 
            prefix_size = countPrefix(masked_ip)
 
            if(masked_ip == masked_datagrama):
                #matched.append((entrada, masked_ip, masked_datagrama))
                matched.append((entrada, prefix_size))
 
        if(len(matched) == 1):
            return matched[0][0][1]
        elif(len(matched) > 1):
 
            biggest = matched[0]
            for entrada in matched:
                if(entrada[1] > biggest[1]):
                    biggest = entrada
 
            return biggest[0][1]
 
 
        return None
 
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
        next_hop = self._next_hop(dest_addr)
 
        dest_addr = ip2bin(dest_addr)
        dest_addr = int(dest_addr, 2)
 
        src_addr = ip2bin(self.meu_endereco)
        src_addr = int(src_addr, 2)
       
        tamanho = sys.getsizeof(segmento)
 
        # pseudo datagrama
        datagrama = struct.pack('!BBHHHBBHII',
            ((4 << 4) + 5),                         # IP Version
            ((0 << 2) + 0),                         # Differentiate Service Feild
            tamanho + 20,                           # Total Length
            54321,                                  # Identification
            ((0 << 7) + (0 << 6) + (0 << 5) + (0)), # Flags
            255,                                    # Time to leave
            6,                                      # protocol
            0,                                      # Checksum
            src_addr,                               # Source IP
            dest_addr                               # Destination IP
        )
       
 
        ckm = calc_checksum(datagrama)
 
        # datagrama com o checksum correto
        datagrama = struct.pack('!BBHHHBBHII',
            ((4 << 4) + 5),                         # IP Version
            ((0 << 2) + 0),                         # Differentiate Service Feild
            tamanho + 20,                           # Total Length
            54321,                                  # Identification
            ((0 << 7) + (0 << 6) + (0 << 5) + (0)), # Flags
            255,                                    # Time to leave
            6,                                      # protocol
            ckm,                                    # Checksum
            src_addr,                               # Source IP
            dest_addr                               # Destination IP
        )
 
        datagrama = datagrama + bytes(segmento)
 
        self.enlace.enviar(datagrama, next_hop)
 
def ip2bin(ip):
    ip = ip.split('.')
    final = ''
 
    for i in range(len(ip)):
        ip[i] = int(ip[i])
        ip[i] = bin(ip[i])
        ip[i] = ip[i][2:].zfill(8)
 
        final = final + ip[i]
 
    return final
 
def entrada2netmask(cidr):
    separado = cidr.split('/')
    ip = separado[0]
    cidr_num = int(separado[1])
 
    netmask = ''
   
    for i in range(cidr_num):
        netmask = netmask + '1'
 
    for i in range(32 - cidr_num):
        netmask = netmask + '0'
 
    return netmask
 
def andStr(a, b):
    c = ''
 
    a = list(a)
    b = list(b)
 
    for i in range(32):
        if(a[i] == '1' and b[i] == '1'):
            c = c + '1'
        else:
            c = c + '0'
 
    return c
 
def countPrefix(prefix):
    uns = 0
 
    prefix = list(prefix)
    for i in range(32):
        if(prefix[i] == '1'):
            uns = uns + 1
 
    return uns