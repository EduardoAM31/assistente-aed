---
titulo: Ordenação simples em C (bubble, selection e insertion sort)
linguagem: C
topicos:
  - ordenacao
  - bubble sort
  - selection sort
  - insertion sort
---

# Ordenação simples em C (bubble, selection e insertion sort)

## Como trocar dois valores de lugar ao ordenar em C

Quase todo algoritmo de ordenação em C precisa trocar dois elementos do vetor de lugar. A troca exige uma variável auxiliar, que guarda um dos valores enquanto o outro é copiado:

```c
int v[2] = {7, 3};
int temp = v[0];   /* guarda o 7 */
v[0] = v[1];       /* v[0] passa a ser 3 */
v[1] = temp;       /* v[1] recebe o 7 guardado */
```

O erro comum é tentar trocar sem a variável auxiliar, com `v[0] = v[1]; v[1] = v[0];`. A primeira atribuição apaga o 7, e a segunda copia de volta o valor que já está em `v[0]`: no fim, as duas posições ficam com 3. A troca também pode ficar numa função, mas aí a função precisa receber ponteiros (`void trocar(int *a, int *b)`), porque uma função que recebe os valores só altera as cópias.

## Bubble sort em C: trocar vizinhos fora de ordem

O bubble sort em C percorre o vetor comparando cada elemento com o vizinho da direita e trocando os dois quando estão fora de ordem. Depois de cada passada, o maior elemento que ainda faltava chega ao fim, como uma bolha que sobe.

```c
void bubble_sort(int v[], int n) {
    for (int passada = 0; passada < n - 1; passada++) {
        int trocou = 0;
        for (int i = 0; i < n - 1 - passada; i++) {
            if (v[i] > v[i + 1]) {
                int temp = v[i];
                v[i] = v[i + 1];
                v[i + 1] = temp;
                trocou = 1;
            }
        }
        if (!trocou) {
            break;   /* nenhuma troca: o vetor já está ordenado */
        }
    }
}
```

O laço de dentro vai até `n - 1 - passada` porque os últimos elementos já estão no lugar certo. A variável `trocou` encerra a ordenação mais cedo quando uma passada inteira não troca nada. Sem esse cuidado, o bubble sort continua comparando mesmo com o vetor já ordenado.

## Selection sort em C: escolher o menor que falta

O selection sort em C procura o menor elemento do vetor e o coloca na posição 0. Depois procura o menor entre os que sobraram e o coloca na posição 1, e assim por diante, até a penúltima posição.

```c
void selection_sort(int v[], int n) {
    for (int i = 0; i < n - 1; i++) {
        int menor = i;
        for (int j = i + 1; j < n; j++) {
            if (v[j] < v[menor]) {
                menor = j;   /* guarda a posição, não o valor */
            }
        }
        int temp = v[i];
        v[i] = v[menor];
        v[menor] = temp;
    }
}
```

A variável `menor` guarda a posição do menor elemento encontrado, e não o valor, porque a troca precisa saber de onde ele veio. O selection sort faz no máximo `n - 1` trocas, uma por posição, o que é bom quando trocar elementos custa caro. Em compensação, ele sempre compara todos os pares que restam, mesmo com o vetor já ordenado.

## Insertion sort em C: inserir cada elemento no lugar certo

O insertion sort em C funciona como organizar cartas na mão. A parte da esquerda do vetor já está ordenada. Cada novo elemento é guardado numa variável, e os maiores que ele, à esquerda, são empurrados uma posição para a direita até abrir o lugar certo.

```c
void insertion_sort(int v[], int n) {
    for (int i = 1; i < n; i++) {
        int atual = v[i];
        int j = i - 1;
        while (j >= 0 && v[j] > atual) {
            v[j + 1] = v[j];   /* empurra para a direita */
            j--;
        }
        v[j + 1] = atual;
    }
}
```

A condição `j >= 0` vem antes de `v[j] > atual`: como o `&&` para na primeira parte falsa, `v[-1]` nunca é lido. O insertion sort é rápido em vetores quase ordenados, porque cada elemento anda pouco. Num vetor já ordenado, o `while` nem entra, e o algoritmo só percorre o vetor uma vez.

## Comparação entre bubble, selection e insertion sort em C

Os três algoritmos simples de ordenação em C são O(n²) no pior caso: com o dobro de elementos, o trabalho fica cerca de quatro vezes maior. Eles diferem no melhor caso e na estabilidade:

| Algoritmo | Vetor já ordenado | Estável |
|---|---|---|
| Bubble sort (com `trocou`) | O(n) | Sim |
| Selection sort | O(n²) | Não |
| Insertion sort | O(n) | Sim |

Um algoritmo é estável quando mantém a ordem original entre elementos iguais, o que importa ao ordenar registros por um campo. O selection sort não é estável porque a troca pode passar um elemento por cima de outro igual a ele.

Para vetores grandes, algoritmos O(n log n), como o merge sort, são muito mais rápidos. Em programas reais, a biblioteca `<stdlib.h>` tem a função `qsort`, que ordena qualquer vetor a partir de uma função de comparação.
