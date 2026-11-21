# CLAUDE.md: assistente-aed

Contexto para o Claude Code trabalhar neste repositório. Leia inteiro antes de começar qualquer tarefa.

## O projeto
Assistente que responde dúvidas de iniciantes em **Algoritmos e Estruturas de Dados (AED)** usando RAG. As respostas vêm de notas em Markdown da pasta `corpus/`, baseadas nas dúvidas mais comuns em monitorias da disciplina.

Fluxo:
1. **Ingestão:** a nota é dividida em chunks (pedaços) pelas seções `##`.
2. **Embeddings:** cada chunk vira um vetor.
3. **Armazenamento:** os vetores são gravados no PostgreSQL com pgvector.
4. **Busca:** a pergunta vira um vetor, e o banco devolve os chunks mais próximos.
5. **Resposta:** o LLM recebe a pergunta e os trechos e responde citando a fonte.

## Como trabalhar neste projeto
- **Responda sempre em português.**
- **Código simples e didático.** Cada parte do projeto precisa poder ser explicada com clareza. Por isso:
  - Evite abstrações que o projeto não precisa.
  - Explique as escolhas importantes (por que essa biblioteca, por que esse formato) em poucas linhas, depois de cada etapa.
  - Avance em passos pequenos, fáceis de revisar.
- **Nunca invente resultados nem métricas.** Só entram no README números que foram medidos rodando o código de verdade.
- Antes de uma mudança grande ou difícil de desfazer, pergunte.

## Ambiente
- Windows 11 com PowerShell. A RAM é de 8 GB e é o recurso mais escasso. GPU NVIDIA com 6 GB de VRAM.
- Python 3.14 num venv em `.venv` (ativar com `.venv\Scripts\Activate.ps1`).
- **Postgres 16 + pgvector 0.8.7** no Docker Compose (serviço `db`, imagem `pgvector/pgvector:pg16`). Configuração vem do `.env`, e o modelo de variáveis está em `.env.example`.
  - Subir: `docker compose up -d`. Parar: `docker compose down`.
  - **Nunca rode `docker compose down -v` sem perguntar:** isso apaga o banco.
  - O `sql/init.sql` só roda quando o volume está vazio. Como o volume já existe, mudanças no `init.sql` são aplicadas à mão, sem apagar nada (o script é idempotente por causa do `IF NOT EXISTS`): `Get-Content sql/init.sql | docker compose exec -T db psql -U rag -d aed`. O PowerShell não aceita `<` para redirecionar a entrada, por isso o `Get-Content` com pipe.
  - **Porta 5433:** neste computador, um PostgreSQL 18 instalado no Windows (serviço `postgresql-x64-18`) já ocupa a porta 5432. Por isso o `.env` usa `POSTGRES_PORT=5433`, e o Compose publica o banco do Docker em `5433:5432`. O `.env.example` continua com 5432, o padrão.
- **Smart App Control ligado:** o Windows bloqueia DLLs nativas sem reputação. Já aconteceu com o `psycopg[binary]` e com executáveis de teste do gcc (esses rodam no WSL). Ao instalar uma dependência com código nativo (como o `torch` na etapa 5), teste o `import` no venv logo em seguida.
- **Ollama** roda direto no Windows, fora do Docker, para usar a GPU. Modelo: `qwen2.5:3b`, que roda 100% na GPU, com contexto de 4096 tokens. API em `http://localhost:11434`.
- Durante o desenvolvimento, a API roda no venv. Ela só entra num container na etapa 9.
- O CI (GitHub Actions) roda em Ubuntu.

## Convenções de código
- **Funcionar em Windows e Linux:**
  - Caminhos com `pathlib`.
  - Toda configuração vem de variáveis de ambiente, lidas com `pydantic-settings`. Nada de endereço, porta ou nome de modelo fixo no código.
  - O `.gitattributes` mantém os arquivos em LF.
- **Nomes de funções, variáveis e rotas em português**, como `gerar_resposta`, `POST /documentos` e `POST /perguntas`. Use type hints.
- **O provedor do LLM fica atrás da interface `gerar_resposta(pergunta, contexto)`** (`app/geracao/base.py`). Ollama e Hugging Face são implementações dessa interface, e o provedor é escolhido pelo `.env`.
- **Banco:** driver `pg8000`, escrito só em Python, porque o Smart App Control bloqueia as DLLs do `psycopg[binary]`. Usamos a interface `pg8000.native` (parâmetros nomeados, como `:nome_arquivo`) e **SQL escrito à mão, sem ORM**. O `pgvector` tem suporte ao pg8000.
- **Testes com pytest.** Os testes não podem baixar modelos nem depender do Ollama: use um embedder e um LLM falsos (fakes). Os testes de integração usam o Postgres (no CI, como service container).
- **Dependências:** coloque em `requirements.txt` só o que for usado, com versões fixadas.
- **Commits:** pequenos, com mensagem em português que diga o que mudou. Nunca versionar `.env` nem `.venv`.

## Estrutura planejada
```
app/        main.py, config.py, db.py, schemas.py, notas.py, chunking.py, embeddings.py, busca.py
app/geracao/  base.py (interface), ollama.py, huggingface.py
corpus/     notas .md
avaliacao/  perguntas_rascunho.md, perguntas.jsonl, baseline_sem_rag.md, avaliar.py
sql/        init.sql
tests/
.github/workflows/testes.yml
docker-compose.yml, Dockerfile, requirements.txt, .env.example, .gitattributes, README.md
```

## Corpus (`corpus/`)
- Cerca de 25 notas, uma por dúvida comum de iniciantes.
- **Linguagem:** a disciplina usava C++ e depois passou para C, então os exemplos são em C. As notas de `map` e `set` usam C++ (`std::map`, `std::set`), porque C não tem essas estruturas na biblioteca padrão.
- **Formato de cada nota:**
  - Arquivo `corpus/<nome-em-kebab-case>.md`, sem acentos no nome.
  - Cabeçalho YAML com `titulo`, `linguagem` (`C` ou `C++`) e `topicos` (lista).
  - Um título `#` e de 3 a 5 seções `##`.
  - **Cada seção precisa fazer sentido sozinha**, com 60 a 200 palavras e uma ideia por seção. A busca devolve seções soltas, então não escreva "como vimos acima". Repita o assunto no título da seção, por exemplo "Por que o for que percorre um vetor começa em 0" em vez de "Por que começa em 0".
  - **Exemplos de código curtos e corretos.** Compile os exemplos em C com `gcc -Wall` (e os de C++ com `g++`) antes de colocar na nota, quando houver compilador disponível. Se não houver, avise.
- **Precisão técnica é prioridade.** Uma nota errada ensina o erro ao modelo. Cuidados conhecidos:
  - Em C, a indentação não muda o funcionamento do programa, ao contrário de Python. A nota explica legibilidade e o erro do `if` sem chaves com duas linhas indentadas.
  - O índice começa em 0 porque é o deslocamento a partir do início do vetor: `v[i]` é o mesmo que `*(v + i)`.
  - Acesso fora dos limites é comportamento indefinido.
- A nota-modelo é `corpus/indice-zero.md`: siga o mesmo formato.
- **Toda nota passa por revisão manual antes do commit.** Entregue as notas em lotes pequenos para facilitar a revisão.
- **Lista de notas:**
  - Parte 1, básico de C: `if-else`, `switch-case`, `laco-for`, `laco-while`, `for-vs-while`, `indentacao-e-chaves`, `vetores`, `indice-zero`, `erros-com-vetores`, `strings`, `funcoes`, `ponteiros`, `matrizes`.
  - Parte 2, estruturas e algoritmos: `alocacao-dinamica`, `lista-encadeada`, `pilha`, `fila`, `pilha-vs-fila`, `map` (C++), `set` (C++), `map-vs-set`, `busca-linear-e-binaria`, `ordenacao-simples`, `recursao`, `complexidade-big-o`.
  - Os temas vizinhos (for × while, pilha × fila, map × set) estão na lista de propósito, para a busca ter concorrência.

## Avaliação (`avaliacao/`): regras importantes
- **As perguntas de avaliação serão feitas manualmente, não pelo Claude.**
  - Não crie, complete nem reescreva `perguntas_rascunho.md` ou `perguntas.jsonl`.
  - **Não leia a pasta `avaliacao/` enquanto escreve ou edita notas do corpus.** Se as notas forem escritas com o vocabulário das perguntas, a busca fica fácil e o recall@3 sai inflado.
  - Se pedirem notas novas e o `avaliacao/perguntas_rascunho.md` ainda não existir, lembre que as perguntas devem ser escritas antes.
- **Métrica principal: recall@3 da busca.** Cada pergunta é rotulada com a **nota e a seção** corretas, não com o id do chunk, porque os ids mudam quando muda o tamanho do chunk. Conta acerto quando algum dos 3 primeiros chunks vem da seção correta.
- **Experimentos:** 2 modelos de embedding (por exemplo, `paraphrase-multilingual-MiniLM-L12-v2` e `multilingual-e5-small`) × 2 ou 3 tamanhos de chunk. A tabela de resultados vai no README.
- **Prefixos dos modelos de embedding:** o `multilingual-e5-small` exige `passage: ` no começo de cada chunk e `query: ` no começo de cada pergunta. O `paraphrase-multilingual-MiniLM-L12-v2` não usa prefixo. Esses prefixos e o prefixo com os títulos que o chunking coloca em todo chunk (`# <nota>` e `## <seção>`) contam no limite de tokens do modelo, mesmo não contando no limite de palavras do chunking.
- **Baseline sem RAG:** o `qwen2.5:3b` respondeu sozinho, sem contexto, à pergunta "Por que o índice de vetores em C começa em 0?". A resposta foi longa e com erros factuais: disse que os arrays de C são "tipados dinamicamente", que C++ conta a partir de 1 e que C deixa escolher o índice inicial. A resposta será colocada manualmente em `avaliacao/baseline_sem_rag.md`, para comparar com a resposta com RAG no README.

## Estilo das respostas do assistente
As respostas devem ser **curtas e diretas**, para iniciantes. Para isso:
- O prompt manda responder em poucas frases, com no máximo um exemplo curto de código, usando só os trechos recebidos e citando a fonte (nota e seção).
- Se os trechos não respondem a pergunta, o modelo deve dizer que não sabe.
- No Ollama: `num_predict` para limitar o tamanho da resposta e `temperature` baixa.

## Etapa atual: 5 (embeddings e busca)
Objetivo (do roteiro): gerar o embedding de cada chunk, buscar os top-k chunks mais próximos da pergunta por distância de cosseno (`<=>`) e criar uma rota de depuração da busca.

**O que a etapa 4 deixou pronto:**
- `app/chunking.py`: `dividir_em_chunks(corpo, titulo_nota, max_palavras, overlap_palavras) -> list[Chunk]`, uma função pura. `Chunk` tem `secao` e `texto`.
- Cada `texto` começa com o prefixo `# <título da nota>\n## <título da seção>\n\n`. Quando uma seção é quebrada, as janelas são recortadas do texto original, então as quebras de linha dos exemplos de código são mantidas.
- `CHUNK_MAX_PALAVRAS` e `CHUNK_OVERLAP_PALAVRAS` vêm do `.env` (hoje 150 e 25). O valor 0 significa "sem limite".
- O `POST /documentos` grava os chunks na mesma transação do documento, apagando antes os chunks antigos da nota. A resposta e o `GET /documentos` mostram `quantidade_chunks`.
- Quando a última janela de uma seção traria no máximo `overlap_palavras` palavras novas, a janela anterior é estendida até o fim da seção. Por isso um chunk pode ter até `max_palavras + overlap_palavras` palavras (sem contar o prefixo).
- Medido nas 13 notas: **110 chunks com 80/15, 53 com 150/25 e 53 sem limite** (53 seções). Contando os exemplos de código, as seções têm de 110 a 167 palavras. O maior chunk tem 93 palavras com 80/15 e 167 com 150/25.
- **Atenção para a etapa 11:** neste corpus, **150/25 gera exatamente os mesmos chunks que "sem limite"**. A maior seção tem 167 palavras, menos que 150 + 25, então toda seção acima de 150 é estendida em vez de quebrada. Para o experimento ter 3 configurações diferentes, o limite do meio precisa ser menor (por exemplo, 120/20). Essa escolha é manual.
- No banco hoje: 13 notas e 63 chunks, gravados com a regra antiga, sem a extensão da última janela. Reenvie as notas para ficar com os 53 da regra atual. Todos os chunks estão com `embedding` vazio.

**Para conferir nesta etapa:**
- O limite de tokens do `paraphrase-multilingual-MiniLM-L12-v2`: rode `modelo.max_seq_length` e registre aqui o valor real. Não confie no número de 128 sem conferir.
- O Smart App Control: teste o `import` do `torch` e do `sentence-transformers` no venv logo depois de instalar.
- Para a etapa 11: o `multilingual-e5-small` espera os prefixos `query:` e `passage:` nos textos.

**A decidir antes de começar:**
- se os embeddings são gerados dentro do `POST /documentos` ou numa rota/script separado;
- se o modelo roda na CPU ou na GPU (RAM de 8 GB e VRAM de 6 GB, dividida com o Ollama);
- o valor padrão de k e o formato da rota de depuração da busca.

## Observação para a etapa 9 (Docker)
O `POSTGRES_PORT` do `.env` serve para duas coisas: a porta publicada pelo Compose e a porta que a API usa para conectar. Dentro do Docker, a API conecta em `db:5432`, então essas duas configurações vão precisar ser separadas.

## Observação para a etapa 10 (não altera as notas)
Algumas perguntas do rascunho tratam de assuntos que nenhuma nota cobre. Na hora de rotular, elas recebem o rótulo "sem resposta no corpus" e ficam fora do cálculo do recall@3. Elas servem para testar se o assistente admite que não sabe, em vez de inventar. Não escreva notas novas para cobrir essas perguntas: decidir isso é uma escolha manual.

## Roteiro (atualize os checkboxes ao concluir cada etapa)
- [x] 1. Ambiente: Docker Compose com Postgres + pgvector, venv, Ollama testado.
- [x] 2. Corpus, parte 1: perguntas de rascunho (feitas manualmente) e depois as 13 notas de básico de C.
- [x] 3. API e banco: FastAPI, `config.py` com `.env`, tabelas `documentos` e `chunks` com `vector(384)` no `init.sql`, `POST /documentos`.
- [x] 4. Chunking: por seção `##`, com tamanho máximo e overlap, e o título da nota no começo de cada chunk. Mais os testes unitários.
- [ ] 5. Embeddings e busca: top-k por distância de cosseno (`<=>`) e uma rota de depuração da busca.
- [ ] 6. Geração: interface `gerar_resposta`, provedor Ollama, prompt com trechos numerados e citação, `POST /perguntas`.
- [ ] 7. Corpus, parte 2: as 12 notas restantes, ingestão completa e teste manual com 10 perguntas.
- [ ] 8. Testes e CI: pytest com fakes e GitHub Actions.
- [ ] 9. Docker: `Dockerfile` da API (torch só para CPU) e Compose completo.
- [ ] 10. Avaliação: `perguntas.jsonl` (feito manualmente) e `avaliar.py` calculando o recall@3.
- [ ] 11. Experimentos: modelo de embedding × tamanho de chunk.
- [ ] 12. README final (diagrama, prints, resultados, limitações, comparação com e sem RAG).

## README
- O README deve ser honesto sobre como o projeto foi feito. Por exemplo: "notas escritas com auxílio de IA e revisadas manualmente, a partir das dúvidas recorrentes das monitorias".
- Sem métricas que não foram medidas.