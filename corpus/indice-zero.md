---
titulo: Por que o índice de vetores em C começa em 0
linguagem: C
topicos:
  - vetores
  - indices
  - ponteiros
---

# Por que o índice de vetores em C começa em 0

## O índice de um vetor em C é um deslocamento a partir do início

Em C, o índice de um vetor não é a posição do elemento contada como no dia a dia (primeiro, segundo, terceiro). Ele é um deslocamento: quantos elementos é preciso andar a partir do início do vetor para chegar ao elemento desejado. O primeiro elemento está exatamente no início, então o deslocamento até ele é zero. Por isso o primeiro elemento é `v[0]`, o segundo é `v[1]`, e assim por diante.

Os elementos de um vetor ficam lado a lado na memória. Se um vetor de `int` começa num certo endereço e cada `int` ocupa 4 bytes (o tamanho mais comum, mas não garantido pela linguagem), `v[0]` está no início, `v[1]` está 4 bytes depois e `v[2]` está 8 bytes depois. O índice diz quantos elementos pular, e o compilador multiplica esse número pelo tamanho do tipo.

## Em C, v[i] é o mesmo que *(v + i)

Em C, a expressão `v[i]` é definida pela própria linguagem como `*(v + i)`. Na maioria das expressões, o nome do vetor `v` é convertido num ponteiro para o primeiro elemento. Somar `i` a esse ponteiro avança `i` elementos (não `i` bytes), e o `*` pega o valor que está nesse lugar.

Com essa definição, o índice 0 aparece naturalmente: `v[0]` é `*(v + 0)`, ou seja, o próprio início do vetor. Se o primeiro índice fosse 1, todo acesso precisaria subtrair 1 antes de calcular o endereço.

```c
#include <stdio.h>

int main(void) {
    int v[3] = {10, 20, 30};
    printf("%d %d\n", v[0], *(v + 0));  /* 10 10 */
    printf("%d %d\n", v[2], *(v + 2));  /* 30 30 */
    return 0;
}
```

## O último índice válido de um vetor em C é o tamanho menos 1

Como o índice de um vetor em C começa em 0, um vetor declarado com `N` elementos tem índices de `0` até `N - 1`. Um vetor `int v[5]` tem exatamente cinco elementos: `v[0]`, `v[1]`, `v[2]`, `v[3]` e `v[4]`. O elemento `v[5]` não existe.

Acessar `v[5]` nesse vetor é acesso fora dos limites, e em C isso é comportamento indefinido: o programa pode mostrar um valor qualquer, alterar outra variável, travar ou até parecer funcionar. O compilador não é obrigado a avisar, e o programa não confere os índices enquanto roda. Por isso o erro pode passar despercebido nos testes e aparecer só depois.

Uma forma simples de lembrar: o número que aparece na declaração (`int v[5]`) é a quantidade de elementos, não o maior índice.

## Como percorrer um vetor em C com um for que começa em 0

O jeito mais comum de percorrer um vetor em C é um `for` que começa em 0 e para antes do tamanho, usando `<` na condição:

```c
#include <stdio.h>

int main(void) {
    int v[5] = {3, 1, 4, 1, 5};
    for (int i = 0; i < 5; i++) {
        printf("v[%d] = %d\n", i, v[i]);
    }
    return 0;
}
```

A variável `i` assume os valores 0, 1, 2, 3 e 4, que são exatamente os índices válidos de um vetor de 5 elementos. A condição `i < 5` faz o laço parar quando `i` chega a 5, sem acessar `v[5]`.

Um erro comum é escrever `i <= 5`. Nesse caso o laço roda uma vez a mais e acessa `v[5]`, que fica fora do vetor. Outro erro é começar em `i = 1`, o que pula o primeiro elemento, `v[0]`.
