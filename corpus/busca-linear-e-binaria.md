---
titulo: Busca linear e busca binária em C
linguagem: C
topicos:
  - busca linear
  - busca binaria
  - vetores
  - complexidade
---

# Busca linear e busca binária em C

## Como funciona a busca linear em C

A busca linear em C procura um valor olhando os elementos do vetor um por um, do primeiro ao último, até encontrar o valor ou chegar ao fim. Ela funciona em qualquer vetor, ordenado ou não.

```c
int busca_linear(const int v[], int n, int x) {
    for (int i = 0; i < n; i++) {
        if (v[i] == x) {
            return i;   /* achou: devolve a posição */
        }
    }
    return -1;          /* não achou */
}
```

A função devolve a posição do primeiro elemento igual a `x`, ou -1 se ele não estiver no vetor. O -1 funciona como sinal de "não achou" porque nenhum índice válido é negativo. No pior caso, quando o valor está na última posição ou não está no vetor, a busca linear faz `n` comparações. Por isso se diz que ela é O(n): se o vetor dobra de tamanho, o pior caso também dobra.

## Como funciona a busca binária em C

A busca binária em C só funciona num vetor ordenado. Ela compara o valor procurado com o elemento do meio. Se for igual, achou. Se o valor procurado for maior, ele só pode estar na metade da direita. Se for menor, só pode estar na metade da esquerda. A cada passo, metade do que sobrou é descartada.

```c
int busca_binaria(const int v[], int n, int x) {
    int inicio = 0, fim = n - 1;
    while (inicio <= fim) {
        int meio = inicio + (fim - inicio) / 2;
        if (v[meio] == x) {
            return meio;
        } else if (v[meio] < x) {
            inicio = meio + 1;   /* x só pode estar à direita */
        } else {
            fim = meio - 1;      /* x só pode estar à esquerda */
        }
    }
    return -1;   /* o intervalo ficou vazio: não achou */
}
```

`inicio` e `fim` marcam o trecho do vetor onde o valor ainda pode estar. Quando `inicio` passa de `fim`, o trecho ficou vazio, e o valor não está no vetor.

## Por que a busca binária em C precisa do vetor ordenado

A busca binária em C descarta metade do vetor a cada passo, supondo que tudo à esquerda do meio é menor e tudo à direita é maior. Num vetor desordenado, essa suposição é falsa, e a busca pode jogar fora justamente a metade em que o valor está. O programa não dá nenhum erro: ele só devolve uma resposta errada.

Por exemplo, no vetor desordenado `{9, 1, 5}`, a busca binária pelo 9 olha o meio (o 1), conclui que o 9 só pode estar à direita, depois olha o 5, e termina devolvendo -1, embora o 9 esteja na posição 0.

Ordenar o vetor custa mais do que uma única busca linear. Por isso a busca binária compensa quando o vetor já está ordenado ou quando muitas buscas vão ser feitas no mesmo vetor. Para uma busca só, num vetor desordenado, a busca linear é a escolha certa.

## Diferença de velocidade entre busca linear e binária em C

No pior caso, a busca linear em C compara o valor procurado com todos os `n` elementos. A busca binária corta o trecho pela metade a cada comparação com o meio, então precisa de cerca de log₂ n passos: a quantidade de vezes que dá para dividir `n` por 2 até sobrar um elemento.

| Tamanho do vetor | Busca linear (pior caso) | Busca binária (pior caso) |
|---|---|---|
| 1.000 | 1.000 | 10 |
| 1.000.000 | 1.000.000 | 20 |

Por isso se diz que a busca linear é O(n) e a busca binária é O(log n). Com um milhão de elementos, a busca binária olha no máximo 20 posições. A diferença cresce junto com o vetor: cada vez que o tamanho dobra, a busca linear dobra o trabalho, e a busca binária precisa de só mais um passo.

## Erros comuns na busca binária em C

Alguns erros na busca binária em C fazem o programa errar a resposta ou nunca terminar:

- **Usar `inicio < fim` em vez de `inicio <= fim`:** quando sobra um único elemento, `inicio` é igual a `fim`, e o laço para antes de olhar esse elemento.
- **Escrever `inicio = meio` em vez de `inicio = meio + 1`:** o meio já foi conferido, e mantê-lo no trecho pode deixar o intervalo do mesmo tamanho para sempre, num laço infinito. O mesmo vale para `fim = meio` no lugar de `fim = meio - 1`.
- **Calcular o meio como `(inicio + fim) / 2` em vetores enormes:** a soma pode passar do maior `int`, o que é comportamento indefinido. A forma `inicio + (fim - inicio) / 2` dá o mesmo resultado sem esse risco.
- **Usar num vetor desordenado:** a busca termina, mas pode devolver -1 para um valor que está no vetor.
