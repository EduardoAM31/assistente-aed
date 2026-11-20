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
  - O `sql/init.sql` só roda quando o volume está vazio.
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
- **Baseline sem RAG:** o `qwen2.5:3b` respondeu sozinho, sem contexto, à pergunta "Por que o índice de vetores em C começa em 0?". A resposta foi longa e com erros factuais: disse que os arrays de C são "tipados dinamicamente", que C++ conta a partir de 1 e que C deixa escolher o índice inicial. A resposta será colocada manualmente em `avaliacao/baseline_sem_rag.md`, para comparar com a resposta com RAG no README.

## Estilo das respostas do assistente
As respostas devem ser **curtas e diretas**, para iniciantes. Para isso:
- O prompt manda responder em poucas frases, com no máximo um exemplo curto de código, usando só os trechos recebidos e citando a fonte (nota e seção).
- Se os trechos não respondem a pergunta, o modelo deve dizer que não sabe.
- No Ollama: `num_predict` para limitar o tamanho da resposta e `temperature` baixa.

## Etapa atual: 3 (API e banco)
Objetivo: a API sobe, conecta no banco e recebe uma nota pelo `POST /documentos`, que salva o texto e os metadados. Embeddings e chunks ficam para as etapas 4 e 5.

**Dependências** (`requirements.txt`, com as versões que forem instaladas, fixadas com `==`): `fastapi`, `uvicorn[standard]`, `python-multipart` (upload de arquivo), `psycopg[binary]` (psycopg 3), `pydantic-settings`, `pyyaml` (frontmatter), `pytest` e `httpx` (o `TestClient` do FastAPI usa o httpx).

**Banco: acrescentar ao `sql/init.sql`**, mantendo o `CREATE EXTENSION`:
```sql
CREATE TABLE IF NOT EXISTS documentos (
    id           SERIAL PRIMARY KEY,
    nome_arquivo TEXT NOT NULL UNIQUE,
    titulo       TEXT NOT NULL,
    linguagem    TEXT NOT NULL,
    conteudo     TEXT NOT NULL,
    criado_em    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS chunks (
    id           SERIAL PRIMARY KEY,
    documento_id INTEGER NOT NULL REFERENCES documentos(id) ON DELETE CASCADE,
    ordem        INTEGER NOT NULL,
    secao        TEXT NOT NULL,
    texto        TEXT NOT NULL,
    embedding    vector(384),
    UNIQUE (documento_id, ordem)
);
```
- `secao` guarda o título da seção `##`, que é o rótulo usado na avaliação.
- `ON DELETE CASCADE`: ao reenviar ou apagar uma nota, os chunks antigos saem junto.
- `vector(384)` é a dimensão do `paraphrase-multilingual-MiniLM-L12-v2`. Se o modelo de embedding mudar na etapa 11, a dimensão muda junto.
- O índice HNSW fica para a etapa 5. Com uns 100 chunks, a busca exata já é rápida.
- **O volume do banco já existe, então o `init.sql` não roda sozinho de novo.** Aplique sem apagar nada (o script é idempotente por causa do `IF NOT EXISTS`), no PowerShell:
  `Get-Content sql/init.sql | docker compose exec -T db psql -U rag -d aed`
  O PowerShell não aceita `<` para redirecionar a entrada, por isso o `Get-Content` com pipe.

**Configuração:** acrescentar `POSTGRES_HOST=localhost` ao `.env.example` (e ao `.env`). Na etapa 9, dentro do Docker, o valor passa a ser `db`. O `app/config.py` tem uma classe `Settings` (pydantic-settings) que lê o `.env` e monta a URL de conexão.

**Arquivos da etapa:**
- `app/__init__.py` (vazio).
- `app/config.py`: `Settings` e uma instância única para o resto do código.
- `app/db.py`: conexão com psycopg 3 e as funções de SQL. **SQL escrito à mão, sem ORM**: são duas tabelas, e o SQL explícito é mais fácil de explicar.
- `app/notas.py`: `ler_nota(texto) -> (metadados, corpo)`, que separa e valida o frontmatter YAML. Exige `titulo` e `linguagem` (`C` ou `C++`), e levanta erro com mensagem clara se faltar algo.
- `app/schemas.py`: modelos Pydantic das respostas (por exemplo, `DocumentoSaida` com `id`, `nome_arquivo`, `titulo`, `linguagem`).
- `app/main.py` com as rotas:
  - `GET /saude`: responde se a API está no ar e se o banco responde.
  - `POST /documentos`: recebe um arquivo `.md` por upload (multipart). Valida a extensão, o UTF-8 e o frontmatter (erro 422 com mensagem clara se algo estiver errado). Grava em `documentos`. Se já existir uma nota com o mesmo `nome_arquivo`, atualiza em vez de duplicar (`INSERT ... ON CONFLICT (nome_arquivo) DO UPDATE`), porque as notas serão reenviadas várias vezes nos experimentos. Responde 201 quando cria e 200 quando atualiza.
  - `GET /documentos`: lista as notas gravadas.
- `tests/test_notas.py`: testes unitários do `ler_nota` (nota válida, sem frontmatter, sem `titulo`, `linguagem` inválida). Não dependem do banco. Os testes de integração das rotas ficam para a etapa 8.

**Como rodar:** `uvicorn app.main:app --reload` e abrir `http://localhost:8000/docs` (Swagger), que permite testar o upload pelo navegador.

**Pronto quando:**
- [ ] `GET /saude` responde que o banco está ok.
- [ ] O upload de `corpus/indice-zero.md` pelo `/docs` grava a nota, e enviar a mesma nota de novo atualiza em vez de duplicar.
- [ ] Um arquivo sem frontmatter devolve 422 com mensagem clara.
- [ ] `pytest` passa.
- [ ] No banco, `SELECT id, nome_arquivo, titulo FROM documentos;` mostra a nota.

Ao terminar, marque a etapa 3 no roteiro e troque esta seção pela etapa 4.

## Observação para a etapa 10 (não altera as notas)
Algumas perguntas do rascunho tratam de assuntos que nenhuma nota cobre. Na hora de rotular, elas recebem o rótulo "sem resposta no corpus" e ficam fora do cálculo do recall@3. Elas servem para testar se o assistente admite que não sabe, em vez de inventar. Não escreva notas novas para cobrir essas perguntas: decidir isso é uma escolha manual.

## Roteiro (atualize os checkboxes ao concluir cada etapa)
- [x] 1. Ambiente: Docker Compose com Postgres + pgvector, venv, Ollama testado.
- [x] 2. Corpus, parte 1: perguntas de rascunho (feitas manualmente) e depois as 13 notas de básico de C.
- [ ] 3. API e banco: FastAPI, `config.py` com `.env`, tabelas `documentos` e `chunks` com `vector(384)` no `init.sql`, `POST /documentos`.
- [ ] 4. Chunking: por seção `##`, com tamanho máximo e overlap, e o título da nota no começo de cada chunk. Mais os testes unitários.
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