---
titulo: set em C++ (std::set)
linguagem: C++
topicos:
  - set
  - std::set
  - conjunto
  - C++
---

# set em C++ (std::set)

## O que é um set em C++

Um `set` em C++ (`std::set`, da biblioteca `<set>`) é um conjunto de valores sem repetição, mantidos sempre em ordem. Inserir um valor que já está no `set` não muda nada: cada valor aparece no máximo uma vez. Ele serve para perguntas como "este número já apareceu?" e para eliminar valores repetidos de uma sequência.

Inserir, buscar e remover um valor num `set` leva tempo proporcional a log n, em que n é o número de elementos. Num vetor desordenado, saber se um valor está lá exige olhar elemento por elemento, o que fica lento com muitos dados.

A biblioteca padrão da linguagem C não tem uma estrutura parecida com o `set`: em C, seria preciso implementá-la à mão. Por isso esta nota usa C++, que a disciplina usava antes de passar para C.

## Como inserir e verificar se um elemento está num set em C++

As operações básicas de um `set` em C++ são `insert`, para inserir, `count`, para verificar se um valor está lá, e `erase`, para remover:

```cpp
#include <iostream>
#include <set>

int main() {
    std::set<int> vistos;
    vistos.insert(5);
    vistos.insert(3);
    vistos.insert(5);   // repetido: não muda nada
    std::cout << vistos.size() << "\n";     // 2
    if (vistos.count(3) == 1) {
        std::cout << "3 esta no set\n";
    }
    vistos.erase(3);
    std::cout << vistos.count(3) << "\n";   // 0
    return 0;
}
```

Como os valores não se repetem, `count` só devolve 1 (está no `set`) ou 0 (não está). Também dá para usar `find(valor) != vistos.end()` e, a partir do C++20, `contains(valor)`. O `insert` devolve um par, e o segundo campo (`second`) é `true` quando o valor era novo e `false` quando ele já estava no `set`.

## Como percorrer um set em C++: os elementos saem em ordem

Um `set` em C++ é percorrido com um laço `for` de intervalo, e os elementos saem sempre do menor para o maior, não na ordem em que foram inseridos:

```cpp
#include <iostream>
#include <set>

int main() {
    std::set<int> numeros = {7, 2, 9, 2};
    for (int n : numeros) {
        std::cout << n << " ";   // 2 7 9
    }
    std::cout << "\n";
    return 0;
}
```

O 2 repetido aparece uma vez só, e a ordem é crescente. Para um `std::set<std::string>`, a ordem é alfabética pelos códigos dos caracteres, em que as maiúsculas vêm antes das minúsculas. Os elementos de um `set` não podem ser alterados no lugar, porque isso poderia quebrar a ordem. Para "trocar" um valor, remova o antigo com `erase` e insira o novo com `insert`.

## Exemplo de uso de set em C++: remover valores repetidos

Um uso comum de `set` em C++ é tirar as repetições de uma sequência. Basta construir o `set` a partir dos elementos de um vetor:

```cpp
#include <iostream>
#include <set>
#include <vector>

int main() {
    std::vector<int> notas = {7, 5, 7, 9, 5, 10};
    std::set<int> diferentes(notas.begin(), notas.end());
    std::cout << diferentes.size() << " notas diferentes:";   // 4
    for (int n : diferentes) {
        std::cout << " " << n;   // 5 7 9 10
    }
    std::cout << "\n";
    return 0;
}
```

O construtor recebe o começo e o fim do vetor (`notas.begin()` e `notas.end()`) e insere cada elemento, descartando os repetidos. O resultado já sai em ordem crescente. Se a ordem original de aparição importasse, o `set` não serviria sozinho: seria preciso percorrer o vetor e usar o `set` só para saber quais valores já foram vistos.
