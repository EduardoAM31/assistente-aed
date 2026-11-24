---
titulo: Complexidade de algoritmos e notação Big-O
linguagem: C
topicos:
  - complexidade
  - big-o
  - eficiencia
  - algoritmos
---

# Complexidade de algoritmos e notação Big-O

## O que é a notação Big-O na análise de algoritmos

A notação Big-O descreve como o tempo de um algoritmo cresce quando o tamanho da entrada, chamado de `n`, aumenta. Ela não mede segundos, porque os segundos dependem do computador. Ela mede o ritmo de crescimento: um algoritmo O(n) leva cerca do dobro do tempo quando `n` dobra, e um algoritmo O(n²) leva cerca de quatro vezes mais.

Para chegar ao Big-O, conta-se quantas operações o algoritmo faz em função de `n` e ficam só o termo que cresce mais rápido, sem as constantes. Um algoritmo que faz `3n + 5` operações é O(n), e um que faz `n²/2 + n` é O(n²). Com `n` grande, as constantes e os termos menores quase não fazem diferença.

Normalmente, o Big-O se refere ao pior caso, que é a maior quantidade de trabalho para uma entrada de tamanho `n`. A mesma ideia também serve para medir o uso de memória.

## Exemplos de O(1), O(n) e O(n²) em C

Três padrões de código em C aparecem o tempo todo na análise de complexidade:

```c
int v[5] = {1, 2, 3, 2, 1};
int n = 5, soma = 0, repetidos = 0;

int x = v[2];                       /* O(1): não depende de n */

for (int i = 0; i < n; i++) {       /* O(n): uma volta por elemento */
    soma += v[i];
}

for (int i = 0; i < n; i++) {       /* O(n²): n voltas para cada i */
    for (int j = 0; j < n; j++) {
        if (i != j && v[i] == v[j]) {
            repetidos++;
        }
    }
}
```

Acessar `v[2]` é O(1), ou tempo constante: leva o mesmo tempo com 5 ou com 5 milhões de elementos. Somar o vetor com um laço é O(n), porque o laço dá uma volta por elemento. Os dois laços aninhados são O(n²), porque o laço de dentro dá `n` voltas para cada uma das `n` voltas do laço de fora, num total de `n × n` comparações.

## O(log n): por que a busca binária é tão rápida

Um algoritmo é O(log n) quando corta o problema pela metade a cada passo. O número de passos é a quantidade de vezes que dá para dividir `n` por 2 até sobrar 1, que é o logaritmo de `n` na base 2.

| n | log₂ n (aproximado) |
|---|---|
| 1.000 | 10 |
| 1.000.000 | 20 |
| 1.000.000.000 | 30 |

O exemplo clássico é a busca binária num vetor ordenado: ela compara o valor procurado com o elemento do meio e descarta a metade em que ele não pode estar. Com um bilhão de elementos, bastam cerca de 30 comparações, enquanto uma busca linear poderia precisar de um bilhão.

No código em C, um sinal de O(log n) é uma variável que é dividida por 2 a cada volta, como em `while (n > 1) { n = n / 2; }`. Esse laço dá cerca de log₂ n voltas, e não `n`.

## Como comparar O(n), O(n log n) e O(n²) na prática

A diferença entre as complexidades aparece quando `n` cresce. Esta tabela mostra a quantidade aproximada de operações em cada caso:

| n | O(n) | O(n log n) | O(n²) |
|---|---|---|---|
| 10 | 10 | 33 | 100 |
| 1.000 | 1.000 | 10 mil | 1 milhão |
| 1.000.000 | 1 milhão | 20 milhões | 1 trilhão |

Com 10 elementos, qualquer algoritmo serve. Com um milhão, a diferença decide se o programa termina em menos de um segundo ou leva horas.

É por isso que os algoritmos de ordenação simples, como bubble sort, selection sort e insertion sort, que são O(n²), só servem para vetores pequenos. Algoritmos como o merge sort, que é O(n log n), ordenam um milhão de elementos com cerca de 20 milhões de operações, em vez de um trilhão. A constante escondida pelo Big-O também importa, mas, para `n` grande, a complexidade quase sempre pesa mais.

## Erros comuns ao calcular a complexidade em C

Alguns enganos são frequentes ao calcular a complexidade de um código em C:

- **Somar laços seguidos como se fossem aninhados:** dois laços de `n` voltas, um depois do outro, fazem `n + n = 2n` voltas, o que é O(n), e não O(n²). Só laços um dentro do outro multiplicam.
- **Esquecer que os tamanhos podem ser diferentes:** um laço de `n` voltas com outro de `m` voltas dentro é O(n × m), e não O(n²).
- **Ignorar o custo das funções chamadas dentro do laço:** em `for (int i = 0; i < strlen(s); i++)`, o `strlen` percorre a string inteira em cada teste da condição. Com uma string de tamanho `n`, isso pode virar O(n²). O certo é calcular o tamanho uma vez, antes do laço.
- **Achar que todo laço é O(n):** um laço em que a variável dobra ou cai pela metade a cada volta é O(log n).
