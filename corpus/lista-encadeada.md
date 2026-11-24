---
titulo: Lista encadeada em C
linguagem: C
topicos:
  - lista encadeada
  - ponteiros
  - struct
  - alocacao dinamica
---

# Lista encadeada em C

## O que é uma lista encadeada em C

Uma lista encadeada em C é uma sequência de nós, em que cada nó guarda um valor e o endereço do próximo nó. O último nó aponta para `NULL`, que marca o fim da lista. O programa guarda só um ponteiro para o primeiro nó, chamado de cabeça da lista. Uma lista vazia é simplesmente uma cabeça valendo `NULL`.

```c
struct No {
    int valor;
    struct No *proximo;   /* endereço do próximo nó, ou NULL no último */
};
```

Ao contrário de um vetor, os nós não ficam lado a lado na memória: cada um é criado separadamente com `malloc`, quando é preciso. Por isso a lista pode crescer e diminuir durante a execução, um nó de cada vez, sem um tamanho máximo definido antes. O preço é que cada nó gasta memória a mais com o ponteiro `proximo`.

## Como inserir no início de uma lista encadeada em C

Inserir no início de uma lista encadeada em C é a operação mais simples: cria-se um nó novo com `malloc`, o `proximo` dele aponta para a cabeça atual, e o nó novo passa a ser a cabeça. A função devolve a nova cabeça, e quem chama precisa guardar esse valor.

```c
struct No *inserir_inicio(struct No *cabeca, int valor) {
    struct No *novo = malloc(sizeof(struct No));
    if (novo == NULL) {
        return cabeca;   /* sem memória: a lista fica como estava */
    }
    novo->valor = valor;
    novo->proximo = cabeca;
    return novo;
}
```

O uso fica `lista = inserir_inicio(lista, 5);`. Esquecer de atribuir o retorno é um erro comum: o nó é criado, mas a lista continua apontando para a cabeça antiga. O operador `->` acessa um campo através de um ponteiro: `novo->valor` é o mesmo que `(*novo).valor`. Essa inserção não depende do tamanho da lista, porque nenhum nó existente precisa ser percorrido ou movido.

## Como percorrer e imprimir uma lista encadeada em C

Para percorrer uma lista encadeada em C, usa-se um ponteiro auxiliar que começa na cabeça e avança pelo campo `proximo` até chegar em `NULL`:

```c
void imprimir(struct No *cabeca) {
    for (struct No *atual = cabeca; atual != NULL; atual = atual->proximo) {
        printf("%d ", atual->valor);
    }
    printf("\n");
}
```

A condição `atual != NULL` para o laço depois do último nó. Um erro comum é testar `atual->proximo != NULL`, o que pula o último elemento. Outro é acessar `atual->valor` quando `atual` já é `NULL`, o que é comportamento indefinido. Também é erro avançar a variável que guarda a cabeça da lista no `main`, em vez de um ponteiro auxiliar: o começo da lista se perde, e os nós ficam inacessíveis. Para chegar ao elemento de posição `i`, é preciso percorrer os `i` nós anteriores, porque não há acesso direto como em `v[i]`.

## Diferença entre lista encadeada e vetor em C

Vetor e lista encadeada em C guardam sequências de valores, mas com custos diferentes. No vetor, os elementos ficam lado a lado na memória, e `v[i]` acessa qualquer posição direto, sem percorrer as anteriores. Em compensação, o tamanho é fixo, e inserir no começo exige deslocar todos os elementos uma posição.

Na lista encadeada, inserir ou remover no início não move nenhum elemento: basta trocar ponteiros. A lista também cresce um nó por vez, sem tamanho máximo definido antes. O preço é que, para chegar ao elemento de posição `i`, é preciso percorrer os nós anteriores, e cada nó gasta memória extra com o ponteiro para o próximo.

Uma regra prática: se o programa acessa muito por posição e o tamanho é conhecido, o vetor é mais simples e mais rápido. Se o programa insere e remove muito no começo, ou não sabe quantos elementos terá, a lista encadeada é uma boa escolha. Pilhas e filas podem ser feitas das duas formas.

## Como liberar a memória de uma lista encadeada em C

Cada nó de uma lista encadeada em C foi criado com `malloc`, então cada um precisa do seu `free`. Liberar só a cabeça não basta: os outros nós continuam alocados e ficam inacessíveis, o que é vazamento de memória. O cuidado é guardar o endereço do próximo nó antes de liberar o atual:

```c
void liberar(struct No *cabeca) {
    struct No *atual = cabeca;
    while (atual != NULL) {
        struct No *proximo = atual->proximo;   /* guarda antes do free */
        free(atual);
        atual = proximo;
    }
}
```

Escrever `free(atual); atual = atual->proximo;` é um erro: depois do `free`, a memória do nó não pertence mais ao programa, e ler `atual->proximo` é comportamento indefinido. Depois de chamar `liberar(lista)`, coloque `lista = NULL` no código que chamou, para não usar a lista já liberada.
