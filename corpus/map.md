---
titulo: map em C++ (std::map)
linguagem: C++
topicos:
  - map
  - std::map
  - chave e valor
  - C++
---

# map em C++ (std::map)

## O que é um map em C++ e por que não existe em C

Um `map` em C++ (`std::map`, da biblioteca `<map>`) guarda pares de chave e valor, como um dicionário: cada chave aparece no máximo uma vez e está ligada a um valor. Exemplos: o nome de um aluno ligado à sua nota, ou uma palavra ligada a quantas vezes ela aparece num texto. O `map` mantém os pares sempre ordenados pela chave.

Buscar, inserir e remover uma chave num `map` leva tempo proporcional a log n, em que n é o número de elementos. O padrão do C++ exige esse tempo logarítmico, e as implementações costumam usar uma árvore balanceada por dentro.

A biblioteca padrão da linguagem C não tem nada parecido com o `map`. Em C, seria preciso implementar a estrutura à mão, com vetores, listas ou tabelas de espalhamento. Por isso esta nota usa C++, que a disciplina usava antes de passar para C.

## Como inserir e acessar valores num map em C++

O jeito mais simples de usar um `map` em C++ é o operador `[]`, com a chave entre colchetes:

```cpp
#include <iostream>
#include <map>
#include <string>

int main() {
    std::map<std::string, int> idades;   // chave: nome; valor: idade
    idades["Ana"] = 20;     // cria a chave "Ana"
    idades["Bruno"] = 19;
    idades["Ana"] = 21;     // "Ana" já existe: só troca o valor
    std::cout << idades["Ana"] << "\n";     // 21
    std::cout << idades.size() << "\n";     // 2
    return 0;
}
```

Na declaração `std::map<std::string, int>`, o primeiro tipo é o da chave, e o segundo é o do valor. Atribuir a uma chave que não existe cria um par novo. Atribuir a uma chave que já existe troca o valor antigo, sem criar outro par, porque as chaves não se repetem. Por isso `size()` devolve 2, mesmo depois de três atribuições.

## Cuidado com o operador [] do map em C++: ele cria a chave

O operador `[]` do `map` em C++ cria a chave quando ela não existe, mesmo quando o código só queria ler. Ler `idades["Carla"]` sem "Carla" no `map` insere "Carla" com o valor padrão do tipo, que é 0 para `int`, e o `map` cresce sem que ninguém tenha pedido.

```cpp
#include <iostream>
#include <map>
#include <string>

int main() {
    std::map<std::string, int> idades;
    idades["Ana"] = 20;
    if (idades["Carla"] == 0) {   // ERRADO para testar: cria "Carla"
        std::cout << idades.size() << "\n";   // 2
    }
    if (idades.count("Bruno") == 0) {   // certo: só consulta
        std::cout << "Bruno nao esta no map\n";
    }
    return 0;
}
```

Para saber se uma chave existe sem criá-la, use `count(chave)`, que devolve 1 ou 0, ou `find(chave) != idades.end()`. A partir do C++20, também existe `contains(chave)`. Para ler um valor que precisa existir, `at(chave)` devolve o valor e lança a exceção `std::out_of_range` se a chave não estiver lá.

## Como percorrer um map em C++ em ordem de chave

Um `map` em C++ é percorrido com um laço `for` de intervalo. Cada elemento é um par: `first` é a chave e `second` é o valor.

```cpp
#include <iostream>
#include <map>
#include <string>

int main() {
    std::map<std::string, int> idades = {{"Carlos", 22}, {"Ana", 20}, {"Bruno", 19}};
    for (const auto& par : idades) {
        std::cout << par.first << ": " << par.second << "\n";
    }
    return 0;
}
```

O programa mostra Ana, Bruno e Carlos nessa ordem, embora os pares tenham sido escritos em outra ordem: o `map` sempre percorre as chaves da menor para a maior. Para `std::string`, isso é a ordem alfabética pelos códigos dos caracteres, em que as maiúsculas vêm antes das minúsculas. O `const auto&` evita copiar cada par e impede que ele seja alterado por engano dentro do laço.

## Exemplo de uso de map em C++: contar quantas vezes cada palavra aparece

Contar ocorrências é o uso mais comum de um `map` em C++. Aqui, o operador `[]` criar a chave com 0 é justamente o que se quer:

```cpp
#include <iostream>
#include <map>
#include <string>

int main() {
    std::map<std::string, int> contagem;
    std::string palavra;
    while (std::cin >> palavra) {
        contagem[palavra]++;   // na primeira vez, cria com 0 e soma 1
    }
    for (const auto& par : contagem) {
        std::cout << par.first << " " << par.second << "\n";
    }
    return 0;
}
```

Com a entrada `a b a c b a`, o programa mostra `a 3`, `b 2` e `c 1`, em ordem alfabética. Cada palavra nova entra no `map` com 0 e é somada logo em seguida, e cada palavra repetida só tem o contador aumentado. Sem um `map`, seria preciso procurar a palavra num vetor a cada leitura, o que fica lento com textos grandes.
