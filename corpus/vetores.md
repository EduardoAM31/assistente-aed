---
titulo: Vetores em C
linguagem: C
topicos:
  - vetores
  - declaracao
  - inicializacao
  - sizeof
---

# Vetores em C

## O que é um vetor em C e quando usar

Um vetor em C (também chamado de array) é um conjunto de variáveis do mesmo tipo, guardadas lado a lado na memória e acessadas por um único nome e um índice. Em vez de criar `nota1`, `nota2` e `nota3`, você cria um vetor `notas` e acessa cada nota com `notas[0]`, `notas[1]` e `notas[2]`.

Vetores são úteis quando há vários valores do mesmo tipo que serão tratados da mesma forma, como as notas de uma turma ou as temperaturas de uma semana. Com um vetor, um único laço `for` consegue ler, somar ou mostrar todos os valores, o que seria repetitivo com variáveis separadas.

Todos os elementos de um vetor em C têm o mesmo tipo: um vetor de `int` só guarda inteiros, e um vetor de `double` só guarda números reais.

## Como declarar e inicializar um vetor em C

Para declarar um vetor em C, escreva o tipo, o nome e a quantidade de elementos entre colchetes:

```c
#include <stdio.h>

int main(void) {
    int idades[4];                  /* 4 inteiros, valores indeterminados */
    int primos[5] = {2, 3, 5, 7, 11};
    int parcial[5] = {1, 2};        /* fica {1, 2, 0, 0, 0} */
    int zeros[10] = {0};            /* todos iguais a 0 */
    double pesos[] = {60.5, 72.0};  /* tamanho 2, contado pelo compilador */

    idades[0] = 18;
    printf("%d %d %d %d %.1f\n", idades[0], primos[4], parcial[3], zeros[9], pesos[1]);
    return 0;
}
```

Quando a lista entre chaves tem menos valores que o tamanho, os elementos restantes recebem 0. Se o tamanho for omitido, o compilador conta os valores da lista. Um vetor local declarado sem inicialização, como `idades`, começa com valores indeterminados ("lixo"), então cada elemento precisa receber um valor antes de ser lido.

## Como ler e mostrar os elementos de um vetor em C com for

Para ler ou mostrar todos os elementos de um vetor em C, use um laço `for` em que a variável de controle percorre os índices de 0 até o tamanho menos 1. Não existe um comando que leia ou imprima o vetor inteiro de uma vez: cada elemento é tratado individualmente.

```c
#include <stdio.h>
#define N 3

int main(void) {
    int notas[N];
    for (int i = 0; i < N; i++) {
        scanf("%d", &notas[i]);
    }
    for (int i = 0; i < N; i++) {
        printf("%d\n", notas[i]);
    }
    return 0;
}
```

No `scanf`, cada elemento precisa do `&`, como uma variável comum: `&notas[i]` é o endereço do elemento de índice `i`. Usar uma constante como `N` para o tamanho evita repetir o número em vários lugares: se a quantidade mudar, basta alterar o `#define`.

## O tamanho de um vetor em C é fixo e não fica guardado nele

Em C, o tamanho de um vetor é definido quando ele é criado e não muda depois: um vetor declarado com 5 elementos não cresce para 6. Quando a quantidade de dados não é conhecida antes, uma saída comum é declarar o vetor com um tamanho máximo e guardar numa variável separada quantos elementos estão em uso. Outra saída é a alocação dinâmica, com `malloc`.

O vetor também não guarda o próprio tamanho, e C não tem algo como `v.length`. Enquanto `v` for o próprio vetor, e não um parâmetro de função, dá para calcular a quantidade de elementos com `sizeof`:

```c
int v[8];
size_t n = sizeof(v) / sizeof(v[0]);  /* 8 */
```

`sizeof(v)` dá o total de bytes do vetor, e `sizeof(v[0])` dá os bytes de um elemento. Esse cálculo não funciona dentro de uma função que recebe o vetor como parâmetro, porque lá o parâmetro é um ponteiro, e `sizeof` mede o ponteiro. Por isso funções que recebem vetores costumam receber também o tamanho.
