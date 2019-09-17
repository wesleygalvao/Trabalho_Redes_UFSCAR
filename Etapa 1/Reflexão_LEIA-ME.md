# Reflexão

## 1 Questões de segurança

- O servidor não é capaz de verificar os usuários por autenticação, o que permite que qualquer dispositivo ou sessão de terminal que tenha acesso ao servidor possa acessá-lo. 
- O servidor não possui limite de clientes conectados e concede acesso indiscriminadamente, o que pode ocasionar numa sobrecarga do mesmo e possibilidade de ataque DDoS.
- As mensagens não são criptografadas, dando a possibilidade de leitura das mesmas caso forem interceptadas por alguma pessoa ou aplicativo mal intencionado.
  
   
---

## 2 Questões práticas

- O servidor é capaz de permitir múltiplas conexões simultâneas de sockets(clientes), porém não há tratamento de exceção para eventuais condições excepcionais causadas pelos sockets. Isso se dá por conta da função `select.select()` possuir o terceiro argumento vazio nesta implementação, sem qualquer tratamento. 

```python
leitura_sockets, _, _ = select.select(sockets_lista, [], [])
```
