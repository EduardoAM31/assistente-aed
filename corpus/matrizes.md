---
titulo: Matrizes em C
linguagem: C
topicos:
  - matrizes
  - vetores
  - lacos aninhados
---

# Matrizes em C

## O que é uma matriz em C e como declarar

Uma matriz em C é um vetor de duas dimensões, organizado em linhas e colunas. Na declaração, o primeiro número é a quantidade de linhas, e o segundo é a quantidade de colunas:

```c
#include <stdio.h>

int main(void) {
    int m[2][3] = {
        {1, 2, 3},   /* linha 0 */
        {4, 5, 6}    /* linha 1 */
    };
    printf("%d\n", m[1][2]);   /* linha 1, coluna 2: 6 */
    return 0;
}
```

Cada elemento é acessado com dois índices, `m[linha][coluna]`, e os dois começam em 0. Numa matriz `int m[2][3]`, as linhas vão de 0 a 1 e as colunas vão de 0 a 2. Acessar fora desses limites é comportamento indefinido, como nos vetores. Um erro comum é escrever `m[1, 2]`, como em outras linguagens: em C, a vírgula dentro dos colchetes não separa os índices, e o resultado é outra coisa. O `gcc -Wall` avisa sobre isso.

## Como percorrer uma matriz em C com dois for

Para percorrer todos os elementos de uma matriz em C, usam-se dois laços `for`, um dentro do outro (laços aninhados). O laço de fora percorre as linhas, e o de dentro percorre as colunas:

```c
#include <stdio.h>
#define LIN 2
#define COL 3

int main(void) {
    int m[LIN][COL] = {{1, 2, 3}, {4, 5, 6}};
    for (int i = 0; i < LIN; i++) {
        for (int j = 0; j < COL; j++) {
            printf("%d ", m[i][j]);
        }
        printf("\n");   /* fim de uma linha */
    }
    return 0;
}
```

Para cada valor de `i`, o laço de dentro roda inteiro, com `j` indo de 0 a 2. Por isso o programa mostra a matriz linha por linha. O `printf("\n")` fica fora do laço de dentro e dentro do de fora: ele roda uma vez por linha. Erros comuns são usar a mesma variável nos dois laços e trocar os limites, usando `LIN` para as colunas.

## Como uma matriz em C fica guardada na memória

Na memória, uma matriz em C é guardada como um único bloco contínuo, uma linha depois da outra. Numa matriz `int m[2][3]`, os seis elementos ficam nesta ordem: `m[0][0]`, `m[0][1]`, `m[0][2]`, `m[1][0]`, `m[1][1]`, `m[1][2]`. Ou seja, `m[1][0]` fica logo depois de `m[0][2]`.

Essa organização tem duas consequências práticas. A primeira é que uma matriz `int m[2][3]` é, na verdade, um vetor de 2 elementos em que cada elemento é um vetor de 3 inteiros. Por isso `m[1]` representa a linha 1 inteira. A segunda é que percorrer a matriz linha por linha, com o laço das linhas por fora e o das colunas por dentro, acessa a memória em sequência, o que costuma ser mais rápido do que percorrer coluna por coluna em matrizes grandes.

## Como passar uma matriz para uma função em C

Para passar uma matriz para uma função em C, o parâmetro precisa informar o número de colunas. O número de linhas pode ficar vazio e ser passado como outro parâmetro:

```c
#include <stdio.h>
#define COL 3

void mostrar(int m[][COL], int linhas) {
    for (int i = 0; i < linhas; i++) {
        for (int j = 0; j < COL; j++) {
            printf("%d ", m[i][j]);
        }
        printf("\n");
    }
}

int main(void) {
    int m[2][COL] = {{1, 2, 3}, {4, 5, 6}};
    mostrar(m, 2);
    return 0;
}
```

O número de colunas é obrigatório porque, para achar `m[i][j]`, o compilador calcula quantos elementos pular: `i` linhas inteiras mais `j`. Sem saber o tamanho de cada linha, essa conta não é possível. Como acontece com vetores, a função recebe o endereço da matriz, e não uma cópia, então alterações feitas dentro dela mudam a matriz original. Na chamada, usa-se só o nome: `mostrar(m, 2)`.
