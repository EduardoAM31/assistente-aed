---
titulo: Fila em C
linguagem: C
topicos:
  - fila
  - FIFO
  - estruturas de dados
---

# Fila em C

## O que é uma fila (FIFO) em C

Uma fila é uma estrutura de dados em que o primeiro elemento que entra é o primeiro que sai, o que se chama FIFO (first in, first out). Funciona como a fila de um banco: quem chega vai para o fim, e quem é atendido sai do começo. As operações básicas são enfileirar, que coloca um elemento no fim, e desenfileirar, que tira o elemento do início.

A linguagem C não tem uma fila pronta na biblioteca padrão: ela é implementada com um vetor ou com uma lista encadeada. Filas aparecem quando as tarefas precisam ser atendidas na ordem em que chegaram, como na fila de impressão, no atendimento de pedidos e na busca em largura em grafos.

## Como implementar uma fila com vetor em C

A versão mais simples de fila com vetor em C usa dois índices: `fim` diz onde entra o próximo elemento, e `inicio` diz qual é o próximo a sair.

```c
#include <stdio.h>
#define MAX 100

struct Fila {
    int itens[MAX];
    int inicio;   /* posição do próximo a sair */
    int fim;      /* posição onde o próximo vai entrar */
};

int main(void) {
    struct Fila f;
    f.inicio = 0;
    f.fim = 0;
    for (int i = 1; i <= 3; i++) {
        f.itens[f.fim] = i;   /* enfileirar */
        f.fim++;
    }
    while (f.inicio < f.fim) {
        printf("%d ", f.itens[f.inicio]);   /* desenfileirar: 1 2 3 */
        f.inicio++;
    }
    printf("\n");
    return 0;
}
```

Enfileirar escreve em `itens[fim]` e avança `fim`. Desenfileirar lê `itens[inicio]` e avança `inicio`. A fila está vazia quando `inicio == fim`, e o programa mostra 1 2 3: os elementos saem na mesma ordem em que entraram. O problema dessa versão é que os dois índices só andam para frente. As posições do começo do vetor, já desenfileiradas, nunca são reaproveitadas, e a fila fica "cheia" quando `fim` chega a `MAX`, mesmo que quase todos os elementos já tenham saído.

## Fila circular em C: reaproveitar o espaço do vetor

Numa fila circular em C, quando a posição chega ao fim do vetor, ela volta para 0. O operador `%` (resto da divisão) faz essa volta: com `MAX` igual a 5, depois da posição 4 vem a posição 0.

```c
#define MAX 5

struct Fila {
    int itens[MAX];
    int inicio;       /* posição do primeiro da fila */
    int quantidade;   /* quantos elementos estão na fila */
};

int enfileirar(struct Fila *f, int valor) {
    if (f->quantidade == MAX) {
        return 0;   /* fila cheia */
    }
    f->itens[(f->inicio + f->quantidade) % MAX] = valor;
    f->quantidade++;
    return 1;
}

int desenfileirar(struct Fila *f, int *valor) {
    if (f->quantidade == 0) {
        return 0;   /* fila vazia */
    }
    *valor = f->itens[f->inicio];
    f->inicio = (f->inicio + 1) % MAX;
    f->quantidade--;
    return 1;
}
```

`(inicio + quantidade) % MAX` é a posição onde o próximo elemento entra. Guardar a `quantidade` deixa os testes simples: a fila está vazia quando `quantidade == 0` e cheia quando `quantidade == MAX`. As duas funções devolvem 1 quando dá certo e 0 quando não dá, e o `desenfileirar` entrega o valor retirado pelo ponteiro `valor`. Assim, todas as posições do vetor são reaproveitadas.

## Fila com lista encadeada em C

Uma fila também pode ser feita com lista encadeada em C, sem tamanho máximo. Desenfileirar acontece no começo da lista, como remover a cabeça. Enfileirar acontece no fim da lista, e aí está o cuidado: se o programa guardar só o ponteiro para o primeiro nó, cada inserção precisa percorrer a lista inteira até o último nó.

A solução é guardar dois ponteiros: `primeiro`, de onde os elementos saem, e `ultimo`, onde eles entram. Para enfileirar, o novo nó é ligado em `ultimo->proximo`, e `ultimo` passa a apontar para ele. Quando a fila está vazia, os dois ponteiros valem `NULL`, e o primeiro elemento enfileirado vira, ao mesmo tempo, o primeiro e o último. Ao desenfileirar o último elemento, os dois ponteiros precisam voltar a `NULL`.
