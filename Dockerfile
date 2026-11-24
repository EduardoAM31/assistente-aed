# Imagem da API do assistente de AED.
# Slim e não Alpine: o torch precisa da glibc. O Python é o mesmo do venv e do CI.
FROM python:3.14-slim

# Sem arquivos .pyc, logs na hora, e o cache dos modelos do Hugging Face em /modelos
# (montado como volume no docker-compose.yml, para não baixar de novo a cada container).
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_HOME=/modelos

WORKDIR /codigo

# Dependências antes do código: esta camada só é refeita quando o requirements.txt muda.
# O torch vem do índice CPU, porque o do PyPI, no Linux, traz CUDA e é muito maior.
COPY requirements.txt .
RUN pip install --no-cache-dir torch==2.15.0 --index-url https://download.pytorch.org/whl/cpu \
 && pip install --no-cache-dir -r requirements.txt

# Usuário sem privilégios de root. A pasta /modelos é criada com esse dono, para o
# volume nomeado herdar a permissão na primeira vez em que é montado.
RUN useradd --create-home app \
 && mkdir /modelos \
 && chown app:app /modelos
USER app

COPY app/ app/

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
