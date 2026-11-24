---
titulo: Pilha em C
linguagem: C
topicos:
  - pilha
  - LIFO
  - estruturas de dados
---

# Pilha em C

## O que é uma pilha (LIFO) em C

Uma pilha é uma estrutura de dados em que o último elemento que entra é o primeiro que sai, o que se chama LIFO (last in, first out). Funciona como uma pilha de pratos: só dá para colocar ou tirar o prato de cima. As operações básicas são empilhar (push), que coloca um elemento no topo, desempilhar (pop), que tira o elemento do topo, e consultar o topo sem tirá-lo.

A linguagem C não tem uma pilha pronta na biblioteca padrão. Ela é implementada pelo programador, normalmente com um vetor e um contador do topo, ou com uma lista encadeada em que tudo acontece no início da lista. Pilhas aparecem no "desfazer" dos editores de texto, na verificação de parênteses e na pilha de chamadas de funções do próprio programa.

## Como implementar uma pilha com vetor em C

A forma mais simples de implementar uma pilha em C é usar um vetor e um contador do topo, juntos numa `struct`:

```c
#include <stdio.h>
#define MAX 100

struct Pilha {
    int itens[MAX];
    int topo;   /* quantos itens estão na pilha */
};

void empilhar(struct Pilha *p, int valor) {
    p->itens[p->topo] = valor;
    p->topo++;
}

int desempilhar(struct Pilha *p) {
    p->topo--;
    return p->itens[p->topo];
}

int main(void) {
    struct Pilha p;
    p.topo = 0;
    empilhar(&p, 1);
    empilhar(&p, 2);
    empilhar(&p, 3);
    while (p.topo > 0) {
        printf("%d ", desempilhar(&p));   /* 3 2 1 */
    }
    printf("\n");
    return 0;
}
```

Na pilha com vetor em C, o campo `topo` guarda quantos elementos estão na pilha, que é também a posição livre onde o próximo elemento vai entrar. Empilhar escreve em `itens[topo]` e soma 1. Desempilhar subtrai 1 e devolve `itens[topo]`. As funções recebem um ponteiro para a pilha (`struct Pilha *p`) porque precisam alterar a pilha original, e não uma cópia. O programa mostra 3 2 1: os elementos saem na ordem inversa da entrada. Essa versão ainda não confere se a pilha está cheia ou vazia antes de cada operação.

## Pilha cheia e pilha vazia em C: overflow e underflow

Na pilha com vetor em C, duas situações precisam ser conferidas. Empilhar com a pilha cheia (`topo == MAX`) escreve depois do fim do vetor, o que é acesso fora dos limites e comportamento indefinido. Desempilhar com a pilha vazia (`topo == 0`) deixa `topo` negativo e lê `itens[-1]`, também comportamento indefinido. Esses erros se chamam estouro (overflow) e esvaziamento (underflow) da pilha.

```c
int empilhar(struct Pilha *p, int valor) {
    if (p->topo == MAX) {
        return 0;   /* pilha cheia: não empilha */
    }
    p->itens[p->topo] = valor;
    p->topo++;
    return 1;
}
```

Essa versão de `empilhar` devolve 1 quando consegue empilhar e 0 quando a pilha está cheia, e quem chama decide o que fazer. O `desempilhar` segue a mesma ideia: confere `if (p->topo == 0)` antes de tirar um elemento. Uma pilha feita com lista encadeada não fica cheia, mas a verificação de pilha vazia continua necessária.

## Para que serve uma pilha: parênteses balanceados e chamadas de função em C

Um uso clássico de pilha é conferir se os parênteses de uma expressão estão balanceados, como em `(a[i] + {b})`. Percorre-se o texto: cada abertura (`(`, `[` ou `{`) é empilhada, e cada fechamento desempilha o topo e confere se é do mesmo tipo. Se um fechamento encontra a pilha vazia, se os tipos não combinam ou se sobra algo na pilha no final, a expressão está desbalanceada. Com um só tipo de parêntese, um contador bastaria. A pilha é necessária porque é preciso lembrar qual foi o último símbolo aberto.

O próprio programa em C também usa uma pilha: a pilha de chamadas. Cada função chamada ganha um espaço no topo, com as suas variáveis locais, que é liberado quando ela retorna. Por isso uma recursão sem caso base costuma terminar com um erro de "stack overflow": a pilha de chamadas fica sem espaço.
