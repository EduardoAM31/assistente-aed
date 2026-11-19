---
titulo: Erros comuns com vetores em C
linguagem: C
topicos:
  - vetores
  - erros
  - comportamento indefinido
  - depuracao
---

# Erros comuns com vetores em C

## Acessar um vetor em C fora dos limites é comportamento indefinido

Em C, um vetor de `N` elementos tem índices válidos de 0 até `N - 1`. Ler ou escrever em qualquer outro índice, como `v[N]` ou `v[-1]`, é acesso fora dos limites, e o padrão da linguagem classifica isso como comportamento indefinido. Isso significa que não há resultado garantido: o programa pode mostrar um número estranho, mudar o valor de outra variável sem motivo aparente, fechar com erro (como "segmentation fault") ou parecer funcionar normalmente.

O pior caso é o último. Um programa com acesso fora dos limites pode passar em todos os testes e falhar depois, em outra máquina ou com outra entrada. C não confere os índices durante a execução, e o compilador só avisa em alguns casos.

Ao ver um valor que "apareceu do nada" ou uma variável que mudou sozinha, vale conferir todos os índices usados nos vetores do programa.

## O erro de usar <= no for que percorre um vetor em C

O erro mais comum com vetores em C é escrever a condição do `for` com `<=` em vez de `<`:

```c
#include <stdio.h>

int main(void) {
    int v[5] = {1, 2, 3, 4, 5};
    int soma = 0;
    for (int i = 0; i <= 5; i++) {  /* ERRADO: acessa v[5] */
        soma += v[i];
    }
    printf("%d\n", soma);
    return 0;
}
```

Com `i <= 5`, o laço roda seis vezes, para `i` igual a 0, 1, 2, 3, 4 e 5. Na última volta ele acessa `v[5]`, que não existe, porque um vetor de 5 elementos vai só até `v[4]`. O resultado é comportamento indefinido, e a soma pode sair errada sem nenhum aviso.

A correção é usar `i < 5`. Uma dica prática: num `for` que percorre um vetor, a condição normalmente é `i < tamanho`, com o mesmo número usado na declaração.

## Usar um vetor em C sem inicializar dá valores imprevisíveis

Um vetor declarado dentro de uma função, sem inicialização, começa com valores indeterminados, muitas vezes chamados de "lixo de memória". Em C, declarar `int v[5];` reserva espaço para cinco inteiros, mas não coloca zero neles.

```c
int contagem[3];          /* valores indeterminados */
int contagem_ok[3] = {0}; /* todos começam em 0 */
```

Um caso comum é usar um vetor como acumulador, por exemplo para contar quantas vezes cada número aparece, e esquecer de zerar antes. O programa soma em cima do lixo e mostra resultados absurdos, que podem mudar a cada execução.

A solução é inicializar na declaração, com `= {0}`, ou atribuir um valor a cada elemento num laço antes de ler. Vetores declarados fora de qualquer função (globais) ou com `static` são a exceção: eles começam com todos os elementos iguais a zero automaticamente.

## Não dá para copiar ou comparar vetores em C com = e ==

Em C, não é possível copiar um vetor inteiro com o operador `=`. Escrever `b = a;`, sendo `a` e `b` vetores, causa erro de compilação. A cópia precisa ser feita elemento por elemento, com um laço, ou com a função `memcpy`, da biblioteca `<string.h>`:

```c
#include <stdio.h>

int main(void) {
    int a[3] = {1, 2, 3};
    int b[3];
    for (int i = 0; i < 3; i++) {
        b[i] = a[i];
    }
    printf("%d %d %d\n", b[0], b[1], b[2]);  /* 1 2 3 */
    return 0;
}
```

Já a comparação `a == b` compila (alguns compiladores dão um aviso), mas não compara o conteúdo: ela compara os endereços de início dos dois vetores, que são sempre diferentes para dois vetores distintos. Para saber se dois vetores têm os mesmos valores, é preciso comparar elemento por elemento num laço.
