class CamadaEnlace:
    def __init__(self, linhas_seriais):
        """
        Inicia uma camada de enlace com um ou mais enlaces, cada um conectado
        a uma linha serial distinta. O argumento linhas_seriais é um dicionário
        no formato {ip_outra_ponta: linha_serial}. O ip_outra_ponta é o IP do
        host ou roteador que se encontra na outra ponta do enlace, escrito como
        uma string no formato 'x.y.z.w'. A linha_serial é um objeto da classe
        PTY (vide camadafisica.py) ou de outra classe que implemente os métodos
        registrar_recebedor e enviar.
        """
        self.enlaces = {}
        # Constrói um Enlace para cada linha serial
        for ip_outra_ponta, linha_serial in linhas_seriais.items():
            enlace = Enlace(linha_serial)
            self.enlaces[ip_outra_ponta] = enlace
            enlace.registrar_recebedor(self.callback)

    def registrar_recebedor(self, callback):
        """
        Registra uma função para ser chamada quando dados vierem da camada de enlace
        """
        self.callback = callback

    def enviar(self, datagrama, next_hop):
        """
        Envia datagrama para next_hop, onde next_hop é um endereço IPv4
        fornecido como string (no formato x.y.z.w). A camada de enlace se
        responsabilizará por encontrar em qual enlace se encontra o next_hop.
        """
        # Encontra o Enlace capaz de alcançar next_hop e envia por ele
        self.enlaces[next_hop].enviar(datagrama)

    def callback(self, datagrama):
        if self.callback:
            self.callback(datagrama)


class Enlace:
    def __init__(self, linha_serial):
        self.linha_serial = linha_serial
        self.linha_serial.registrar_recebedor(self.__raw_recv)
        self.listdatagrama = []
    def registrar_recebedor(self, callback):
        self.callback = callback

    def enviar(self, datagrama):
        # TODO: Preencha aqui com o código para enviar o datagrama pela linha
        # serial, fazendo corretamente a delimitação de quadros e o escape de
        # sequências especiais, de acordo com o protocolo SLIP (RFC 1055).
        strdatagrama = datagrama.decode('ISO-8859-1')
        newstrdatagrama = ''
        escapeparaxc0 = b'\xdb\xdc'
        escapeparaxdb = b'\xdb\xdd'
        for caractere in strdatagrama:
            if caractere.encode('ISO-8859-1') == b'\xc0':
                newstrdatagrama += escapeparaxc0.decode('ISO-8859-1')
            elif caractere.encode('ISO-8859-1') == b'\xdb':
                newstrdatagrama += escapeparaxdb.decode('ISO-8859-1')
            else:
                newstrdatagrama += caractere
        self.linha_serial.enviar(b'\xc0' + newstrdatagrama.encode('ISO-8859-1') + b'\xc0')
        pass

    def __raw_recv(self, dados):
        # TODO: Preencha aqui com o código para receber dados da linha serial.
        # Trate corretamente as sequências de escape. Quando ler um quadro
        # completo, repasse o datagrama contido nesse quadro para a camada
        # superior chamando self.callback. Cuidado pois o argumento dados pode
        # vir quebrado de várias formas diferentes - por exemplo, podem vir
        # apenas pedaços de um quadro, ou um pedaço de quadro seguido de um
        # pedaço de outro, ou vários quadros de uma vez só.
        strdados = dados.decode('ISO-8859-1')
        bytexdb = b'\xdb'
        bytexc0 = b'\xc0'
        strdatagrama = ''
        for caractere in strdados:
            tamanho = len(self.listdatagrama)
            if caractere.encode('ISO-8859-1') == b'\xc0' and tamanho > 0:
                for ele in self.listdatagrama:
                    strdatagrama += ele
                self.callback(strdatagrama.encode('ISO-8859-1'))
                self.listdatagrama.clear()
                strdatagrama = ''
            elif caractere.encode('ISO-8859-1') != b'\xc0':
                if tamanho > 0:
                    if self.listdatagrama[tamanho - 1].encode('ISO-8859-1') == b'\xdb' and caractere.encode('ISO-8859-1') == b'\xdd':
                        self.listdatagrama[tamanho - 1] = bytexdb.decode('ISO-8859-1')
                    elif self.listdatagrama[tamanho - 1].encode('ISO-8859-1') == b'\xdb' and caractere.encode('ISO-8859-1') == b'\xdc':
                        self.listdatagrama[tamanho - 1] = bytexc0.decode('ISO-8859-1')
                    else:
                        self.listdatagrama.append(caractere)
                else:
                    self.listdatagrama.append(caractere)
        pass
