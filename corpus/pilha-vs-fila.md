---
titulo: Diferença entre pilha e fila em C
linguagem: C
topicos:
  - pilha
  - fila
  - LIFO
  - FIFO
  - comparacao
---

# Diferença entre pilha e fila em C

## A diferença entre pilha e fila em C está na ordem de saída

Pilha e fila em C guardam uma sequência de elementos, e a diferença entre elas é qual elemento sai primeiro. Na pilha, sai o último que entrou: é a regra LIFO (last in, first out), como numa pilha de pratos. Na fila, sai o primeiro que entrou: é a regra FIFO (first in, first out), como na fila de um banco.

Se os valores 1, 2 e 3 entram nessa ordem, a pilha devolve 3, 2 e 1, enquanto a fila devolve 1, 2 e 3. A pilha inverte a ordem de chegada, e a fila mantém essa ordem. Nas duas estruturas, só um elemento pode sair de cada vez, e não dá para retirar um elemento do meio sem tirar antes os que estão na frente dele.

## Onde o elemento entra e sai na pilha e na fila em C

Na pilha em C, o elemento entra e sai pela mesma ponta, o topo. Por isso basta um controle: um índice `topo`, numa pilha com vetor, ou o ponteiro para o primeiro nó, numa pilha com lista encadeada.

Na fila em C, o elemento entra por uma ponta, o fim, e sai pela outra, o início. Por isso a fila precisa de dois controles: os índices de início e de fim (ou o início e a quantidade), numa fila com vetor, ou os ponteiros para o primeiro e para o último nó, numa fila com lista encadeada.

Essa diferença explica um detalhe de implementação. Numa pilha com vetor, as posições livres estão sempre no fim do vetor e são reaproveitadas naturalmente. Numa fila com vetor, as posições do começo ficam livres conforme os elementos saem, e só são reaproveitadas se a fila for circular, com o índice voltando para 0 depois da última posição.

## Quando usar pilha e quando usar fila em C

Use uma pilha em C quando o elemento mais recente deve ser tratado primeiro. Exemplos: desfazer a última ação de um editor, voltar para a página anterior de um navegador, conferir se os parênteses de uma expressão estão balanceados, inverter uma sequência e percorrer um caminho até o fim antes de voltar (busca em profundidade).

Use uma fila em C quando quem chegou primeiro deve ser atendido primeiro. Exemplos: a fila de impressão, o atendimento de pedidos na ordem de chegada, as teclas digitadas esperando para ser lidas e a busca em largura, que visita os vizinhos mais próximos antes dos mais distantes.

Uma regra prática para escolher: se a pergunta é "o que foi feito por último?", a estrutura é uma pilha. Se a pergunta é "quem está esperando há mais tempo?", a estrutura é uma fila.

## Exemplo em C: inverter a ordem com pilha e manter com fila

Este programa coloca 1, 2 e 3 numa pilha e numa fila feitas com vetores, e depois tira tudo das duas:

```c
#include <stdio.h>

int main(void) {
    int pilha[3], topo = 0;
    int fila[3], inicio = 0, fim = 0;
    for (int i = 1; i <= 3; i++) {
        pilha[topo++] = i;   /* empilhar */
        fila[fim++] = i;     /* enfileirar */
    }
    while (topo > 0) {
        printf("%d ", pilha[--topo]);    /* 3 2 1 */
    }
    printf("\n");
    while (inicio < fim) {
        printf("%d ", fila[inicio++]);   /* 1 2 3 */
    }
    printf("\n");
    return 0;
}
```

Em `pilha[topo++] = i`, o valor é guardado na posição `topo` e só depois `topo` aumenta. Em `pilha[--topo]`, `topo` diminui primeiro e depois a posição é lida, o que pega o último elemento guardado. A pilha sai em ordem inversa (3 2 1), e a fila sai na ordem de entrada (1 2 3).
