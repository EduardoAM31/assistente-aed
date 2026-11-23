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
app/geracao/  __init__.py, base.py (interface e prompt), ollama.py, huggingface.py (depois)
corpus/     notas .md
avaliacao/  perguntas_rascunho.md, perguntas.jsonl, baseline_sem_rag.md, avaliar.py
sql/        init.sql
scripts/    contar_tokens.py
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

## Etapa atual: 6 (geração)
Objetivo (do roteiro): a interface `gerar_resposta(pergunta, contexto)`, o provedor Ollama, o prompt com trechos numerados e citação, e o `POST /perguntas`.

**O que a etapa 5 deixou pronto:**
- `app/embeddings.py`:
  - `carregar_modelo(nome, dispositivo)` carrega o modelo uma vez só, com `lru_cache`. O `torch` só é importado nessa hora.
  - `conferir_dimensao`, `gerar_vetores(modelo, textos, prefixo)` e `vetor_para_texto`.
  - As funções recebem o modelo e o prefixo por parâmetro, para os testes usarem um modelo falso.
- `app/busca.py`: `gerar_embeddings_dos_chunks(refazer)` e `buscar(pergunta, k) -> list[dict]`, com `nome_arquivo`, `titulo`, `secao`, `distancia` e `texto`. É a função que o `POST /perguntas` vai usar para montar o contexto.
- `POST /embeddings` (com `?refazer=true`) e `GET /busca?pergunta=...&k=...`. O `k` precisa ser pelo menos 1, e sem ele vale o `BUSCA_K`. Pergunta vazia e `k=0` dão 422.
- `.env`: `EMBEDDING_MODELO`, `EMBEDDING_PREFIXO_DOCUMENTO`, `EMBEDDING_PREFIXO_PERGUNTA`, `EMBEDDING_DISPOSITIVO=cpu` e `BUSCA_K=3`. **Um prefixo com espaço no fim precisa de aspas no `.env`** (`"passage: "`). Sem aspas, o espaço some (testado).
- No banco: 13 notas e 155 chunks (60/10), todos com vetor do MiniLM.

**Observações da etapa 5:**
- Reenviar uma nota apaga os vetores dela, então `POST /embeddings` precisa rodar de novo. Ao trocar de modelo, use `?refazer=true`, senão vetores de modelos diferentes se misturam.
- Tempo medido nesta máquina (CPU), incluindo o carregamento do modelo: `POST /embeddings` dos 155 chunks levou cerca de 14 s com o MiniLM e 17 s com o e5. Sem nada a fazer, 0,3 s.
- Nas buscas de teste, os 3 resultados muitas vezes vêm da mesma seção (janelas vizinhas, com overlap). Para o recall@3 isso não muda nada, mas no contexto do LLM vira trecho repetido.
- As distâncias do e5 ficam bem menores que as do MiniLM: nas mesmas perguntas de teste, de 0,08 a 0,12 contra 0,27 a 0,52. Distâncias não são comparáveis entre modelos, então não use um limiar fixo de distância sem medir.

**Padrões sugeridos para a etapa 6 (confirme com o usuário antes de implementar; ajuste o que os testes mostrarem):**
- **Interface.** `app/geracao/base.py` define a interface `gerar_resposta(pergunta, contexto) -> str`. `contexto` é a lista de chunks que `busca.buscar` devolve (`nome_arquivo`, `titulo`, `secao`, `texto`). Uma `Protocol` com um único método basta: os fakes dos testes só precisam ter esse método. O texto do prompt também fica em `base.py`, numa função `montar_mensagens(pergunta, contexto)` que devolve a lista de mensagens (`system` e `user`), para o Ollama e o Hugging Face usarem o mesmo prompt.
- **Prompt.** Em português, com as regras do "Estilo das respostas do assistente" (poucas frases, no máximo um exemplo curto de código, só os trechos recebidos, "não sei" se os trechos não respondem). Os trechos vão numerados (`[1]`, `[2]`, `[3]`). Ponto de partida, para ajustar testando: "Você é um monitor de Algoritmos e Estruturas de Dados e ajuda iniciantes. Responda em português, em no máximo 4 frases e com no máximo um exemplo curto de código. Use somente os trechos numerados abaixo e cite o número do trecho, como [1]. Se os trechos não responderem a pergunta, diga que não sabe, sem inventar." O texto de cada chunk já começa com `# <nota>` e `## <seção>`, então o título e a seção já aparecem no trecho: não repita isso no prompt, a menos que o teste mostre que ajuda.
- **Quantos trechos.** Os mesmos `BUSCA_K` (3) da busca. Como os 3 primeiros muitas vezes vêm da mesma seção, na resposta da API a lista de fontes tira as repetições de (nota, seção), mantendo a ordem. Juntar janelas vizinhas da mesma seção no contexto do LLM fica como refinamento futuro, não entra agora.
- **Provedor Ollama** (`app/geracao/ollama.py`): `POST {OLLAMA_URL}/api/chat` com `stream: false`, `model` = `LLM_MODEL` e, em `options`, `num_predict`, `temperature` e `num_ctx`. Use o `httpx`, que já está no `requirements.txt` (agora também em código de produção, não só nos testes). Fixe `num_ctx` no `.env` (4096), para o uso de VRAM ser previsível nos 6 GB. A primeira chamada depois de um tempo parado carrega o modelo na GPU e demora, então o timeout vem do `.env` e precisa ser generoso.
- **Variáveis novas no `.env` e no `.env.example`**, lidas em `app/config.py`: `LLM_PROVEDOR=ollama`, `LLM_NUM_PREDICT`, `LLM_TEMPERATURE`, `LLM_TIMEOUT` (segundos) e `OLLAMA_NUM_CTX`. Valores para começar: `num_predict` 256 e `temperature` 0.1. Teste com algumas perguntas e ajuste: a resposta não pode ser cortada no meio, e o Ollama avisa isso com `done_reason: "length"`. Registre aqui os valores finais.
- **Escolha do provedor:** uma função (por exemplo, em `app/geracao/__init__.py`) lê `LLM_PROVEDOR` e devolve o provedor. Só `ollama` é válido por enquanto, e qualquer outro valor dá um erro claro. **O provedor Hugging Face não entra nesta etapa**: a interface fica pronta para ele, e fica para depois.
- **`POST /perguntas`:** corpo JSON `{"pergunta": "..."}`, resposta `{"resposta": "...", "fontes": [{"nome_arquivo", "titulo", "secao"}]}`. Fluxo: `busca.buscar` → provedor → resposta. As `fontes` vêm do código, a partir dos chunks recuperados, e **não** do texto do modelo: um modelo de 3B cita de forma pouco confiável. A lista mostra os trechos consultados, e não prova qual deles o modelo usou. No README, descreva assim.
- **Erros claros:** Ollama fora do ar ou timeout → 503 com mensagem dizendo para conferir se o Ollama está rodando em `OLLAMA_URL`. Nenhum chunk com embedding → 409 pedindo para rodar `POST /embeddings`. Pergunta vazia → 422.
- **Sem limiar de distância.** As distâncias de cada modelo não são comparáveis (ver as observações da etapa 5). O "não sei" fica por conta do prompt, e o quanto ele funciona é medido, não presumido.

**Passos sugeridos (pequenos, um commit por passo, explicando as escolhas no fim de cada um):**
1. Variáveis novas no `.env`/`.env.example` e em `app/config.py`.
2. `app/geracao/base.py`: a interface e `montar_mensagens`, com testes (trechos numerados, instruções presentes, nenhum chunk perdido).
3. `app/geracao/ollama.py`, com testes que trocam o transporte do `httpx` por um falso (`httpx.MockTransport`): conferem o corpo enviado (modelo, `stream: false`, `options`) e os erros. Nenhum teste chama o Ollama de verdade.
4. A função que escolhe o provedor pelo `LLM_PROVEDOR`.
5. Schemas e `POST /perguntas`, com a lista de fontes sem repetições (função pura, com teste).
6. Teste manual no `/docs` com perguntas escolhidas à mão e ajuste de `num_predict` e do prompt. Não precisa ler a pasta `avaliacao/`. Limite os ajustes de prompt a poucas rodadas: o que sobrar de falha entra como limitação no README.
7. Atualizar o `requirements.txt` só se algo novo for usado.

**Pronto quando:**
- [ ] `POST /perguntas` com uma pergunta coberta pelas notas devolve uma resposta curta, em português, e a lista de `fontes` bate com os chunks que `GET /busca` mostra para a mesma pergunta.
- [ ] Com uma pergunta fora do corpus (por exemplo, sobre árvore binária, que nenhuma nota cobre), o assistente diz que não sabe. Se o modelo inventar mesmo assim, registre o caso como limitação, sem esconder.
- [ ] Com o Ollama desligado, a rota responde 503 com mensagem clara, sem derrubar a API.
- [ ] As respostas de teste não saem cortadas (`done_reason` não é `length`) e os valores finais de `num_predict`, `temperature` e `num_ctx` estão registrados nesta seção.
- [ ] A resposta real com RAG para a pergunta do baseline ("Por que o índice de vetores em C começa em 0?") foi guardada, com modelo, parâmetros e data, para a comparação do README na etapa 12. A resposta é a que o código devolveu, sem retoque. Quem salva o arquivo em `avaliacao/` é o usuário.
- [ ] `pytest` passa sem o Ollama e sem baixar modelos.

Ao terminar, marque a etapa 6 no roteiro e troque esta seção pela etapa 7.

## Medições registradas (para o README)
Feitas na etapa 5, sobre as 13 notas da parte 1, rodando o código. Refaça depois da parte 2 do corpus (etapa 7).
- **Chunks:** 230 com 40/8, 155 com 60/10 e 53 sem limite. Também medidos: 110 com 80/15, 103 com 100/15, 79 com 120/20 e 53 com 150/25.
- **Tokens por chunk.** O chunk inclui o prefixo `# nota` / `## seção` e, no e5, também `passage: `.

| Config | Chunks | MiniLM: mediana / máx. / acima de 128 | e5-small: mediana / máx. / acima de 512 |
|---|---|---|---|
| 40/8 | 230 | 88 / 141 / 3 (1%) | 90 / 143 / 0 |
| 60/10 | 155 | 118 / 179 / 54 (35%) | 120 / 181 / 0 |
| sem limite | 53 | 262 / 321 / 53 (100%) | 264 / 323 / 0 |

- **`max_seq_length`:** 128 no MiniLM e 512 no e5-small. **Dimensão 384 nos dois**, conferida ao carregar cada modelo: `get_embedding_dimension()` no código e `vector_dims(embedding)` no banco.
- Os números de tokens vêm do `scripts/contar_tokens.py`, que lê o modelo, o prefixo de documento e o dispositivo do `.env`, como a API. Rode na raiz do projeto com `python -m scripts.contar_tokens`. Para medir o e5 sem mexer no `.env`, defina `EMBEDDING_MODELO` e `EMBEDDING_PREFIXO_DOCUMENTO` como variáveis de ambiente antes de rodar. Rodado de novo depois de ir para `scripts/`, ele reproduziu exatamente a tabela acima.

## Observação para a etapa 9 (Docker)
O `POSTGRES_PORT` do `.env` serve para duas coisas: a porta publicada pelo Compose e a porta que a API usa para conectar. Dentro do Docker, a API conecta em `db:5432`, então essas duas configurações vão precisar ser separadas.

## Observação para a etapa 9 (Ollama)
O Ollama roda no Windows, fora do Docker. Dentro do container, `localhost` é o próprio container, então a API precisa de `OLLAMA_URL=http://host.docker.internal:11434` (Docker Desktop no Windows). No Linux e no CI não há Ollama: os testes usam o LLM falso.

## Observação para as etapas 8 e 9 (torch)
No `requirements.txt` fica `torch==2.15.0`. No Ubuntu, o PyPI instala a versão com CUDA, que é muito maior. No CI e no `Dockerfile`, instale antes o torch pelo índice CPU do PyTorch (`pip install torch==2.15.0 --index-url https://download.pytorch.org/whl/cpu`, conferindo que essa versão existe lá) e só depois o `requirements.txt`. Os testes usam embedder falso, então o CI não deve baixar nenhum modelo.

## Observação para a etapa 10 (não altera as notas)
Algumas perguntas do rascunho tratam de assuntos que nenhuma nota cobre. Na hora de rotular, elas recebem o rótulo "sem resposta no corpus" e ficam fora do cálculo do recall@3. Elas servem para testar se o assistente admite que não sabe, em vez de inventar. Não escreva notas novas para cobrir essas perguntas: decidir isso é uma escolha manual.

## Roteiro (atualize os checkboxes ao concluir cada etapa)
- [x] 1. Ambiente: Docker Compose com Postgres + pgvector, venv, Ollama testado.
- [x] 2. Corpus, parte 1: perguntas de rascunho (feitas manualmente) e depois as 13 notas de básico de C.
- [x] 3. API e banco: FastAPI, `config.py` com `.env`, tabelas `documentos` e `chunks` com `vector(384)` no `init.sql`, `POST /documentos`.
- [x] 4. Chunking: por seção `##`, com tamanho máximo e overlap, e o título da nota no começo de cada chunk. Mais os testes unitários.
- [x] 5. Embeddings e busca: top-k por distância de cosseno (`<=>`) e uma rota de depuração da busca.
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