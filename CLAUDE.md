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
- **Smart App Control ligado:** o Windows bloqueia DLLs nativas sem reputação. Já aconteceu com o `psycopg[binary]` e com executáveis de teste do gcc (esses rodam no WSL). Ao instalar uma dependência com código nativo, teste o `import` no venv logo em seguida. Na etapa 5, `torch` 2.15.0 (CPU) e `sentence-transformers` 6.3.0 foram instalados no venv (Python 3.14.0) e importam normalmente.
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
- **Experimentos:** 2 modelos de embedding (`paraphrase-multilingual-MiniLM-L12-v2` e `multilingual-e5-small`) × 3 tamanhos de chunk (máximo de palavras/overlap): **40/8, 60/10 e sem limite**. A tabela de resultados vai no README, com a porcentagem de chunks cortados pelo limite de tokens em cada combinação. Os tamanhos foram escolhidos com a contagem de tokens da etapa 5, feita só nas 13 notas da parte 1. Depois da parte 2 do corpus (etapa 7), refaça a contagem, e outras configurações podem ser testadas. A escolha final é manual.
- **Prefixos dos modelos de embedding:** o `multilingual-e5-small` exige `passage: ` no começo de cada chunk e `query: ` no começo de cada pergunta. O `paraphrase-multilingual-MiniLM-L12-v2` não usa prefixo. Esses prefixos e o prefixo com os títulos que o chunking coloca em todo chunk (`# <nota>` e `## <seção>`) contam no limite de tokens do modelo, mesmo não contando no limite de palavras do chunking.
- **Limites de tokens (medidos):** o MiniLM tem `max_seq_length` = 128 e o e5-small tem 512. Texto além do limite é ignorado no cálculo do vetor, sem erro. Só o vetor é afetado: o texto do chunk continua inteiro no banco e vai inteiro para o LLM.
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
- `CHUNK_MAX_PALAVRAS` e `CHUNK_OVERLAP_PALAVRAS` vêm do `.env`. O valor 0 significa "sem limite".
- O `POST /documentos` grava os chunks na mesma transação do documento, apagando antes os chunks antigos da nota (o novo chunk entra com `embedding` vazio). A resposta e o `GET /documentos` mostram `quantidade_chunks`.
- Quando a última janela de uma seção traria no máximo `overlap_palavras` palavras novas, a janela anterior é estendida até o fim da seção. Por isso um chunk pode ter até `max_palavras + overlap_palavras` palavras (sem contar o prefixo).
- No banco hoje: 13 notas e 63 chunks, gravados com a regra antiga, todos com `embedding` vazio.

**Decisões já tomadas (manuais):**
- **Chunking padrão: 60/10.** O primeiro passo da etapa é trocar `CHUNK_MAX_PALAVRAS=60` e `CHUNK_OVERLAP_PALAVRAS=10` no `.env.example` e no `.env` (antes era 150/25, que neste corpus gera os mesmos chunks de "sem limite"). Reinicie a API (o `.env` só é lido na partida) e reenvie as 13 notas: devem ficar **155 chunks**.
- **Experimento da etapa 11:** 2 modelos × 40/8, 60/10 e sem limite. Mais para frente serão testadas outras opções, principalmente depois da parte 2 do corpus.
- **O modelo de embedding e os prefixos vêm do `.env`**, sem nome de modelo fixo no código: `EMBEDDING_MODELO` (padrão `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`), `EMBEDDING_PREFIXO_DOCUMENTO` e `EMBEDDING_PREFIXO_PERGUNTA` (vazios para o MiniLM; `passage: ` e `query: ` para o `intfloat/multilingual-e5-small`). Trocar de modelo na etapa 11 é só mudar o `.env`.

**Medido nesta etapa (rodando o código, sobre as 13 notas):**
- Chunks: 230 com 40/8, 155 com 60/10 e 53 sem limite (também medidos: 110 com 80/15, 103 com 100/15, 79 com 120/20 e 53 com 150/25).
- Tokens por chunk (o chunk inclui o prefixo `# nota` / `## seção`; no e5, também `passage: `):

| Config | Chunks | MiniLM: mediana / máx. / acima de 128 | e5-small: mediana / máx. / acima de 512 |
|---|---|---|---|
| 40/8 | 230 | 88 / 141 / 3 (1%) | 90 / 143 / 0 |
| 60/10 | 155 | 118 / 179 / 54 (35%) | 120 / 181 / 0 |
| sem limite | 53 | 262 / 321 / 53 (100%) | 264 / 323 / 0 |

- O `max_seq_length` do MiniLM conferido no modelo carregado é 128, e a dimensão é 384 (a mesma de `vector(384)`). O e5-small tem limite de 512 (medido) e dimensão 384 (pela ficha do modelo; confira ao carregá-lo), então a coluna `embedding` deve servir para os dois.
- Os números vieram do `contar_tokens.py`, um script temporário que está na raiz do projeto e **não está versionado**. Como esses números vão para o README, ao fim da etapa pergunte se ele deve ser versionado como `scripts/contar_tokens.py` (e acrescentado à estrutura planejada), para a medição poder ser repetida depois da parte 2 do corpus.

**Padrões sugeridos (confirme antes de implementar):**
- **Embeddings fora do `POST /documentos`.** O upload não carrega torch nem o modelo. Uma rota separada, `POST /embeddings`, calcula os vetores dos chunks que estão com `embedding` vazio e devolve quantos foram gerados. Com `?refazer=true` ela recalcula todos, o que é necessário ao trocar de modelo. Reenviar uma nota apaga os vetores dos chunks dela, então a rota precisa rodar de novo.
- **CPU** (`EMBEDDING_DISPOSITIVO=cpu` no `.env`). O modelo é pequeno e a VRAM de 6 GB fica para o Ollama. Carregue o modelo só na primeira chamada, uma vez, e reaproveite: a RAM é de 8 GB e `/saude` e `POST /documentos` não devem pagar esse custo.
- **k = 3** por padrão (o mesmo do recall@3), configurável por `BUSCA_K` no `.env` e por parâmetro na rota.
- **Rota de depuração:** `GET /busca?pergunta=...&k=3`, devolvendo, para cada chunk, `nome_arquivo`, `titulo`, `secao`, `distancia` e `texto`. Mostre a distância (0 é igual; quanto maior, mais longe), não uma "similaridade" inventada.
- **Vetor no pg8000 sem dependência extra:** envie o vetor como texto `[0.1,0.2,...]` e use `CAST(:vetor AS vector)` no SQL. O operador é `<=>` (cosseno), então não é preciso normalizar os vetores. O índice HNSW continua fora desta etapa.

**Passos sugeridos (pequenos, um commit por passo, explicando as escolhas no fim de cada um):**
1. Trocar o chunking padrão para 60/10 e acrescentar ao `.env.example` e ao `.env` as variáveis novas, lidas em `app/config.py`.
2. `app/embeddings.py`: carrega o modelo uma vez, aplica os prefixos do `.env` e confere que a dimensão do modelo é 384 (erro claro se não for). Use `get_embedding_dimension()`, porque `get_sentence_embedding_dimension()` está obsoleto na versão instalada. As funções precisam aceitar um modelo falso nos testes.
3. Funções de SQL em `app/db.py`: listar chunks sem embedding, gravar embeddings e buscar os k chunks mais próximos.
4. `POST /embeddings`.
5. `app/busca.py` e `GET /busca`, com os schemas em `app/schemas.py`.
6. Testes unitários com modelo falso (prefixos aplicados, formato do vetor, erro de dimensão). Nenhum teste baixa modelo. Os testes de integração das rotas ficam para a etapa 8.
7. `requirements.txt`: acrescente `sentence-transformers==6.3.0` e `torch==2.15.0` (sem o `+cpu`; transformers e numpy vêm como dependências e não são usados diretamente).

Os testes manuais da busca são feitos no `/docs` com perguntas escolhidas à mão. Não é preciso ler a pasta `avaliacao/` nesta etapa.

**Pronto quando:**
- [ ] O chunking padrão é 60/10 e, depois de reenviar as 13 notas, `SELECT count(*) FROM chunks;` mostra 155.
- [ ] `POST /embeddings` gera os vetores, e `SELECT count(*) FROM chunks WHERE embedding IS NULL;` mostra 0.
- [ ] `GET /busca?pergunta=...` devolve 3 chunks com nota, seção, distância e texto, ordenados do mais perto para o mais longe.
- [ ] Trocar `EMBEDDING_MODELO` e os prefixos no `.env` e rodar `POST /embeddings?refazer=true` funciona com o `intfloat/multilingual-e5-small` (a dimensão também é 384).
- [ ] `pytest` passa sem baixar nenhum modelo.

Ao terminar, marque a etapa 5 no roteiro e troque esta seção pela etapa 6.

## Observação para a etapa 9 (Docker)
O `POSTGRES_PORT` do `.env` serve para duas coisas: a porta publicada pelo Compose e a porta que a API usa para conectar. Dentro do Docker, a API conecta em `db:5432`, então essas duas configurações vão precisar ser separadas.

## Observação para as etapas 8 e 9 (torch)
No `requirements.txt` fica `torch==2.15.0`. No Ubuntu, o PyPI instala a versão com CUDA, que é muito maior. No CI e no `Dockerfile`, instale antes o torch pelo índice CPU do PyTorch (`pip install torch==2.15.0 --index-url https://download.pytorch.org/whl/cpu`, conferindo que essa versão existe lá) e só depois o `requirements.txt`. Os testes usam embedder falso, então o CI não deve baixar nenhum modelo.

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