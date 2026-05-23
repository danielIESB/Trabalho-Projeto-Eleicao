# =============================================================================
# PROJETO TSE — LIMPEZA E IMPORTAÇÃO DE DADOS ELEITORAIS
# =============================================================================
# Este script realiza a limpeza dos dados do TSE e importa diretamente
# para o banco de dados PostgreSQL, sem geração de arquivos CSV intermediários.
#
# Eleições contempladas: 2010, 2014, 2018, 2022
# Banco de dados: Railway (PostgreSQL)
# Schema: tse
#
# ORDEM DE PROCESSAMENTO:
# 1. municipio, eleicao, partido       — tabelas base (sem dependências)
# 2. candidatura                       — processada ANTES de pessoa para gerar
#                                        o conjunto de títulos válidos
# 3. pessoa                            — filtrada pelos títulos da candidatura
# 4. candidatura (importação)          — importada após pessoa (FK obedecida)
# 5. vaga, resultado, bem, despesa     — dependem de candidatura
# =============================================================================

# %%
# ==========================================
# IMPORTAÇÕES E INSTALAÇÃO DE DEPENDÊNCIAS
# ==========================================
import subprocess
import sys
import os
from pathlib import Path

# Garante que as dependências estão instaladas no ambiente correto
subprocess.run([sys.executable, '-m', 'pip', 'install',
                'sqlalchemy', 'psycopg2-binary', 'python-dotenv'], check=False)

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine

# Carrega variáveis do .env (não versionado)
load_dotenv()

# %%
# ==========================================
# CONFIGURAÇÕES GLOBAIS
# ==========================================

# Anos de eleição a serem considerados no projeto
ANOS_PRINCIPAIS = [2010, 2014, 2018, 2022]

# Diretórios dos arquivos de entrada (configure no .env ou defina abaixo)
_DIR_TSE    = Path(os.getenv('DIR_TSE', r'C:\Users\Daniel\Downloads\tse'))
DIR_DESPESA = Path(os.getenv('DIR_DESPESA', _DIR_TSE / 'despesas'))
DIR_RECEITA = Path(os.getenv('DIR_RECEITA', _DIR_TSE / 'receitas'))

# %%
# ==========================================
# CONEXÃO COM O BANCO DE DADOS
# ==========================================

HOST    = os.getenv('PG_HOST', 'localhost')
PORTA   = int(os.getenv('PG_PORT', '5432'))
BANCO   = os.getenv('PG_DATABASE', 'railway')
USUARIO = os.getenv('PG_USER', 'postgres')
SENHA   = os.environ['PG_PASSWORD']
SCHEMA  = 'tse'

engine = create_engine(
    f'postgresql+psycopg2://{USUARIO}:{SENHA}@{HOST}:{PORTA}/{BANCO}',
    connect_args={'sslmode': 'prefer'}
)

# Testa a conexão antes de prosseguir
with engine.connect() as conn:
    print("Conexão estabelecida com sucesso!")

# %%
# ==========================================
# FUNÇÃO DE IMPORTAÇÃO PARA O BANCO
# ==========================================
# Centraliza a lógica de inserção para evitar repetição de código.
# Recebe o DataFrame já limpo, o nome da tabela e o tamanho do chunk.
# Usa method='multi' para inserção em lote, mais eficiente que row-by-row.

def importar_para_banco(df, tabela, chunksize=1000):
    """
    Importa um DataFrame diretamente para o banco de dados.

    Parâmetros:
        df       : DataFrame pandas já limpo e pronto para inserção
        tabela   : Nome da tabela de destino no schema 'tse'
        chunksize: Número de linhas por lote de inserção (padrão: 1000)
    """
    print(f"\nImportando {tabela}...")
    df.to_sql(
        name=tabela,
        con=engine,
        schema=SCHEMA,
        if_exists='append',   # Adiciona aos dados existentes sem sobrescrever
        index=False,          # Não inclui o índice do DataFrame como coluna
        method='multi',       # Inserção em lote (mais performático)
        chunksize=chunksize
    )
    print(f"  -> {len(df):,} registros inseridos em tse.{tabela} ✅")


# %%
# ==========================================
# LEITURA DOS ARQUIVOS FONTE
# ==========================================

# Base principal de candidatos — fonte de todas as tabelas dimensão
df = pd.read_csv(_DIR_TSE / 'Candidatos.csv', low_memory=False)

# Base auxiliar de cruzamento TSE x IBGE para municípios
df_municipio = pd.read_csv(
    'https://raw.githubusercontent.com/danielIESB/Trabalho-Projeto-Eleicao/331f19fb7362f45847f748289f2079447ccf82ee/municipio_tse_ibge.csv',
    sep=';',
    encoding='latin1'
)

# Base de vagas por eleição/cargo
df_vaga = pd.read_csv(
    'https://raw.githubusercontent.com/danielIESB/Trabalho-Projeto-Eleicao/refs/heads/main/Vagas.csv',
    low_memory=False
)

print(f"Total de registros carregados: {len(df):,}")
print(f"Colunas disponíveis: {df.columns.tolist()}")

# %%
# ==========================================
# FILTRO — APENAS CANDIDATURAS DEFERIDAS
# ==========================================
# Mantemos apenas candidatos com situação 'deferido' ou 'deferido com recurso',
# pois são os que efetivamente participaram das eleições.

df_deferido = df[
    (df['situacao'] == 'deferido') |
    (df['situacao'] == 'deferido com recurso')
].copy()

df_deferido.reset_index(drop=True, inplace=True)

print(f"Total de registros no arquivo original : {len(df):,}")
print(f"Total de registros deferidos           : {len(df_deferido):,}")
print(f"Registros removidos (não deferidos)    : {len(df) - len(df_deferido):,}")
print(f"\nDistribuição por situação:")
print(df_deferido['situacao'].value_counts())

# %%
# ==========================================
# TABELA: MUNICIPIO
# ==========================================
# Extrai os municípios únicos presentes nas candidaturas e cruza com a
# tabela de referência TSE x IBGE para obter os campos necessários.

# Municípios únicos nas candidaturas deferidas
municipios_candidatos = df_deferido[['id_municipio']].drop_duplicates().dropna().copy()
municipios_candidatos['id_municipio'] = (
    municipios_candidatos['id_municipio'].astype(float).astype(int).astype(str)
)

# Prepara a base de referência para cruzamento
df_municipio['CD_MUNICIPIO_IBGE'] = (
    df_municipio['CD_MUNICIPIO_IBGE'].astype(float).astype(int).astype(str)
)

# Cruzamento para trazer nome e UF de cada município
df_municipio_limpo = pd.merge(
    municipios_candidatos,
    df_municipio[['CD_MUNICIPIO_IBGE', 'CD_MUNICIPIO_TSE', 'NM_MUNICIPIO_TSE', 'SG_UF']],
    left_on='id_municipio',
    right_on='CD_MUNICIPIO_IBGE',
    how='inner'
).rename(columns={
    'CD_MUNICIPIO_TSE' : 'cd_municipio_tse',
    'NM_MUNICIPIO_TSE' : 'nm_municipio_tse',
    'SG_UF'            : 'sg_uf'
}).drop(columns=['CD_MUNICIPIO_IBGE'])

# Validação
print("--- DIAGNÓSTICO (MUNICIPIO) ---")
print(f"Municípios únicos nas candidaturas  : {len(municipios_candidatos):,}")
print(f"Municípios encontrados no cruzamento: {len(df_municipio_limpo):,}")
print(f"Municípios não encontrados          : {len(municipios_candidatos) - len(df_municipio_limpo):,}")
print(f"Nulos em id_municipio               : {df_municipio_limpo['id_municipio'].isnull().sum()}")
print(f"Duplicados em id_municipio          : {df_municipio_limpo['id_municipio'].duplicated().sum()}")

# Importa direto no banco
importar_para_banco(df_municipio_limpo, 'municipio')

# %%
# ==========================================
# TABELA: ELEICAO
# ==========================================
# Extrai os dados de eleição e filtra apenas os anos principais definidos
# em ANOS_PRINCIPAIS. Usa groupby para resolver duplicatas de data_eleicao.

mapeamento = {
    "id_eleicao"   : "id_eleicao",
    "ano"          : "ano",
    "tipo_eleicao" : "tipo_eleicao",
    "data_eleicao" : "data_eleicao"
}

df_eleicao = (
    df_deferido[list(mapeamento.keys())]
    .rename(columns=mapeamento)
    .drop_duplicates()
    .copy()
)
df_eleicao.reset_index(drop=True, inplace=True)

# Filtra apenas os anos definidos no projeto
df_eleicao = df_eleicao[df_eleicao['ano'].isin(ANOS_PRINCIPAIS)].copy()
print(f"Eleições após filtro de anos principais: {len(df_eleicao)}")

# Resolve duplicatas de id_eleicao mantendo o primeiro registro de cada grupo
df_eleicao_combinado = df_eleicao.groupby('id_eleicao').first().reset_index()

# Diagnóstico
print("--- DIAGNÓSTICO INICIAL (ELEIÇÃO) ---")
print(f"Nulos em id_eleicao      : {df_eleicao['id_eleicao'].isnull().sum()}")
print(f"Duplicados em id_eleicao : {df_eleicao['id_eleicao'].duplicated().sum()}")
print(f"Total de linhas          : {len(df_eleicao)}\n")

# Limpeza
df_eleicao_limpo = df_eleicao_combinado.dropna(subset=['id_eleicao']).copy()
df_eleicao_limpo['id_eleicao'] = (
    df_eleicao_limpo['id_eleicao'].astype(str).str.split('.').str[0].str.strip()
)

# Validação final
print("--- APÓS A LIMPEZA ---")
print(f"Nulos restantes     : {df_eleicao_limpo['id_eleicao'].isnull().sum()} (Esperado: 0)")
print(f"Duplicados restantes: {df_eleicao_limpo['id_eleicao'].duplicated().sum()} (Esperado: 0)")
print(f"Total de eleições   : {len(df_eleicao_limpo)}")
print(f"Anos presentes      : {sorted(df_eleicao_limpo['ano'].unique())}\n")

# Importa direto no banco
importar_para_banco(df_eleicao_limpo, 'eleicao')

# %%
# ==========================================
# TABELA: PARTIDO
# ==========================================
# Extrai partidos únicos por número. A sigla pode variar ao longo do tempo
# (fusões, extinções), por isso usamos drop_duplicates na chave primária.

mapeamento = {
    "numero_partido" : "numero_partido",
    "sigla_partido"  : "sigla_partido"
}

df_partido = (
    df_deferido[list(mapeamento.keys())]
    .rename(columns=mapeamento)
    .drop_duplicates(subset=['numero_partido'], keep='first')
    .copy()
)
df_partido.reset_index(drop=True, inplace=True)

# Diagnóstico
print("--- DIAGNÓSTICO INICIAL (PARTIDO) ---")
print(f"Nulos em numero_partido     : {df_partido['numero_partido'].isnull().sum()}")
print(f"Duplicados em numero_partido: {df_partido['numero_partido'].duplicated().sum()}")
print(f"Total de linhas             : {len(df_partido)}\n")

# Limpeza
df_partido_limpo = df_partido.dropna(subset=['numero_partido']).copy()
df_partido_limpo['numero_partido'] = (
    df_partido_limpo['numero_partido'].astype(str).str.split('.').str[0].str.strip()
)

# Validação final
print("--- APÓS A LIMPEZA ---")
print(f"Nulos restantes     : {df_partido_limpo['numero_partido'].isnull().sum()} (Esperado: 0)")
print(f"Duplicados restantes: {df_partido_limpo['numero_partido'].duplicated().sum()} (Esperado: 0)")
print(f"Total de partidos   : {len(df_partido_limpo)}\n")

# Importa direto no banco
importar_para_banco(df_partido_limpo, 'partido')

# %%
# ==========================================
# TABELA: CANDIDATURA — LIMPEZA (sem importar ainda)
# ==========================================
# Processamos candidatura ANTES de pessoa para gerar o conjunto de
# títulos eleitorais válidos, usado para filtrar pessoa.
# A importação no banco ocorre APÓS a tabela pessoa ser importada.

mapeamento = {
    "sequencial"       : "sequencial_candidato",
    "titulo_eleitoral" : "titulo_eleitoral",
    "id_eleicao"       : "id_eleicao",
    "numero_partido"   : "numero_partido",
    "id_municipio"     : "id_municipio",
    "sigla_uf"         : "sigla_uf",
    "cargo"            : "cargo",
    "numero"           : "numero_urna",
    "nome_urna"        : "nome_urna",
    "situacao"         : "situacao"
}

df_candidatos = df_deferido[list(mapeamento.keys())].rename(columns=mapeamento).copy()

# Normaliza id_eleicao para comparação com o conjunto de eleições válidas
eleicoes_validas = set(df_eleicao_limpo['id_eleicao'].astype(str))
df_candidatos['id_eleicao'] = (
    df_candidatos['id_eleicao'].astype(str).str.split('.').str[0].str.strip()
)

# Mantém apenas candidaturas das eleições dos anos principais
df_candidatos = df_candidatos[df_candidatos['id_eleicao'].isin(eleicoes_validas)].copy()
print(f"Candidaturas após filtro de eleições principais: {len(df_candidatos):,}")

# Diagnóstico
print("--- DIAGNÓSTICO INICIAL (CANDIDATURA) ---")
print(f"Nulos em titulo_eleitoral   : {df_candidatos['titulo_eleitoral'].isnull().sum():,}")
print(f"Duplicados (titulo+eleicao) : {df_candidatos.duplicated(subset=['titulo_eleitoral', 'id_eleicao']).sum():,}")
print(f"Total de linhas             : {len(df_candidatos):,}\n")

# Limpeza
df_candidatos_limpo = df_candidatos.dropna(subset=['titulo_eleitoral', 'id_eleicao']).copy()

# Corrige sufixo ".0" em todas as colunas numéricas
for coluna in ['sequencial_candidato', 'titulo_eleitoral', 'id_eleicao',
               'numero_partido', 'id_municipio', 'numero_urna']:
    df_candidatos_limpo[coluna] = (
        df_candidatos_limpo[coluna]
        .apply(lambda x: str(int(x)) if pd.notna(x) and str(x).replace('.','').isdigit()
               else str(x).split('.')[0].strip())
    )

# id_municipio é NULL para cargos sem vínculo municipal (deputados, senadores, etc.)
df_candidatos_limpo['id_municipio'] = df_candidatos_limpo['id_municipio'].replace('nan', None)

# Validação final
print("--- APÓS A LIMPEZA ---")
print(f"Nulos restantes     : {df_candidatos_limpo['titulo_eleitoral'].isnull().sum()} (Esperado: 0)")
print(f"Duplicados restantes: {df_candidatos_limpo.duplicated(subset=['titulo_eleitoral', 'id_eleicao']).sum()} (Esperado: 0)")
print(f"Total de candidaturas únicas: {len(df_candidatos_limpo):,}")
print(f"\n** Importação no banco será feita APÓS a tabela pessoa **")

# %%
# ==========================================
# TABELA: PESSOA
# ==========================================
# Um candidato pode ter concorrido em múltiplas eleições, gerando
# linhas duplicadas por titulo_eleitoral. Usamos groupby para consolidar,
# complementando a raça com o primeiro valor não nulo disponível.
#
# FILTRO CRÍTICO: filtramos apenas pessoas cujo título eleitoral aparece
# em df_candidatos_limpo, reduzindo de ~1.75M para ~127K registros
# e evitando estouro de disco no banco gratuito.

mapeamento = {
    "titulo_eleitoral" : "titulo_eleitoral",
    "cpf"              : "cpf",
    "nome"             : "nome",
    "data_nascimento"  : "data_nascimento",
    "genero"           : "genero",
    "raca"             : "raca"
}

df_pessoa = df_deferido[list(mapeamento.keys())].rename(columns=mapeamento).copy()

# Conjunto de títulos eleitorais válidos (apenas candidatos das eleições principais)
titulos_validos = set(df_candidatos_limpo['titulo_eleitoral'])

# Filtra antes do groupby para reduzir volume de dados
df_pessoa = df_pessoa[df_pessoa['titulo_eleitoral'].astype(str).apply(
    lambda x: str(int(float(x))) if x.replace('.','').isdigit() else x.split('.')[0].strip()
).isin(titulos_validos)].copy()

print(f"Pessoas após filtro de candidatura: {len(df_pessoa):,}")

# Combina duplicatas pegando o primeiro valor válido por título
df_pessoa_combinado = df_pessoa.groupby('titulo_eleitoral').first().reset_index()

# Estratégia especial para 'raca': substitui pelo primeiro valor não nulo
# pois o groupby().first() pode pegar uma linha com raca = NaN
df_raca = (
    df_pessoa[df_pessoa['raca'].notna()]
    .groupby('titulo_eleitoral')['raca']
    .first()
    .reset_index()
)
df_pessoa_combinado = df_pessoa_combinado.drop(columns=['raca']).merge(
    df_raca, on='titulo_eleitoral', how='left'
)

# Diagnóstico
print("--- DIAGNÓSTICO INICIAL (PESSOA) ---")
print(f"Nulos em titulo_eleitoral     : {df_pessoa['titulo_eleitoral'].isnull().sum():,}")
print(f"Duplicados em titulo_eleitoral: {df_pessoa['titulo_eleitoral'].duplicated().sum():,}")
print(f"Total de linhas               : {len(df_pessoa):,}\n")

# Limpeza
df_pessoa_limpo = df_pessoa_combinado.dropna(subset=['titulo_eleitoral']).copy()

# Corrige notação científica (ex: 1.07e+11 → '107458400000')
df_pessoa_limpo['titulo_eleitoral'] = (
    df_pessoa_limpo['titulo_eleitoral']
    .apply(lambda x: str(int(float(x))) if pd.notna(x) else None)
)

# Validação final
print("--- APÓS A LIMPEZA ---")
print(f"Nulos restantes     : {df_pessoa_limpo['titulo_eleitoral'].isnull().sum()} (Esperado: 0)")
print(f"Duplicados restantes: {df_pessoa_limpo['titulo_eleitoral'].duplicated().sum()} (Esperado: 0)")
print(f"Total de pessoas    : {len(df_pessoa_limpo):,}\n")

# Importa direto no banco
importar_para_banco(df_pessoa_limpo, 'pessoa')

# %%
# ==========================================
# TABELA: CANDIDATURA — IMPORTAÇÃO
# ==========================================
# Agora que pessoa já está no banco, podemos importar candidatura
# respeitando a FK (titulo_eleitoral → pessoa).

# Verificação de amarração com tabelas dependentes
titulos_sem_pessoa = set(df_candidatos_limpo['titulo_eleitoral']) - set(df_pessoa_limpo['titulo_eleitoral'])
eleicoes_sem_ref   = set(df_candidatos_limpo['id_eleicao']) - set(df_eleicao_limpo['id_eleicao'])
partidos_sem_ref   = set(df_candidatos_limpo['numero_partido']) - set(df_partido_limpo['numero_partido'])

print(f"Títulos sem correspondência em pessoa  : {len(titulos_sem_pessoa)} (Esperado: 0)")
print(f"Eleições sem correspondência em eleicao: {len(eleicoes_sem_ref)} (Esperado: 0)")
print(f"Partidos sem correspondência em partido: {len(partidos_sem_ref)} (Esperado: 0)\n")

# Importa direto no banco
importar_para_banco(df_candidatos_limpo, 'candidatura')

# %%
# ==========================================
# TABELA: VAGA
# ==========================================
# Extrai vagas por eleição/UF/município/cargo.
# A chave composta é (id_eleicao, sigla_uf, id_municipio, cargo).
# id_municipio pode ser NULL para vagas estaduais/federais.

mapeamento = {
    "id_eleicao"   : "id_eleicao",
    "sigla_uf"     : "sigla_uf",
    "id_municipio" : "id_municipio",
    "cargo"        : "cargo",
    "vagas"        : "vagas"
}

df_vaga_mapped = df_vaga[list(mapeamento.keys())].rename(columns=mapeamento).copy()

# Diagnóstico
print("--- DIAGNÓSTICO INICIAL (VAGA) ---")
print(f"Nulos em id_eleicao                    : {df_vaga_mapped['id_eleicao'].isnull().sum():,}")
print(f"Duplicados (eleicao+uf+municipio+cargo): {df_vaga_mapped.duplicated(subset=['id_eleicao', 'sigla_uf', 'id_municipio', 'cargo']).sum():,}")
print(f"Total de linhas                        : {len(df_vaga_mapped):,}\n")

# Limpeza
df_vaga_limpo = df_vaga_mapped.dropna(subset=['id_eleicao', 'cargo']).copy()

# Corrige sufixo ".0"
for coluna in ['id_eleicao', 'id_municipio']:
    df_vaga_limpo[coluna] = (
        df_vaga_limpo[coluna].astype(str).str.split('.').str[0].str.strip()
    )

# NULL para vagas sem município específico (estaduais/federais)
df_vaga_limpo['id_municipio'] = df_vaga_limpo['id_municipio'].replace('nan', None)

# Remove eleições fora do escopo do projeto
eleicoes_sem_ref = set(df_vaga_limpo['id_eleicao']) - set(df_eleicao_limpo['id_eleicao'])
df_vaga_limpo = df_vaga_limpo[~df_vaga_limpo['id_eleicao'].isin(eleicoes_sem_ref)].copy()
print(f"Eleições removidas por não corresponder ao banco: {len(eleicoes_sem_ref)}")

# Validação final
print("--- APÓS A LIMPEZA ---")
print(f"Nulos restantes     : {df_vaga_limpo['id_eleicao'].isnull().sum()} (Esperado: 0)")
print(f"Duplicados restantes: {df_vaga_limpo.duplicated(subset=['id_eleicao', 'sigla_uf', 'id_municipio', 'cargo']).sum()} (Esperado: 0)")
print(f"Total de vagas      : {len(df_vaga_limpo):,}\n")

# Importa direto no banco
importar_para_banco(df_vaga_limpo, 'vaga')

# %%
# ==========================================
# TABELA: RESULTADO_CANDIDATURA_UF
# ==========================================
# Lê o arquivo de resultados, filtra pelos pares válidos de candidatura
# e agrega os votos por (titulo_eleitoral, id_eleicao, sigla_uf).

df_resultado = pd.read_csv(
    _DIR_TSE / 'Resultados_Candidato.csv',
    low_memory=False
)

print(f"Total de registros no arquivo: {len(df_resultado):,}")

# Normaliza as chaves para comparação
df_resultado['titulo_eleitoral_candidato'] = (
    df_resultado['titulo_eleitoral_candidato'].astype(str).str.split('.').str[0].str.strip()
)
df_resultado['id_eleicao'] = (
    df_resultado['id_eleicao'].astype(str).str.split('.').str[0].str.strip()
)

# Conjunto de pares válidos baseado na tabela candidatura já carregada
pares_validos = set(zip(
    df_candidatos_limpo['titulo_eleitoral'],
    df_candidatos_limpo['id_eleicao']
))
print(f"Pares válidos em candidatura: {len(pares_validos):,}")

# Filtra apenas registros com par (titulo, eleicao) existente na candidatura
df_resultado['_par'] = list(zip(
    df_resultado['titulo_eleitoral_candidato'],
    df_resultado['id_eleicao']
))
df_resultado_filtrado = df_resultado[df_resultado['_par'].isin(pares_validos)].drop(columns=['_par']).copy()
df_resultado_filtrado = df_resultado_filtrado.dropna(subset=['sigla_uf']).copy()
print(f"Registros após filtro: {len(df_resultado_filtrado):,}")

# Agrega votos por (titulo, eleicao, uf) — reduz granularidade de município para UF
df_resultado_uf = (
    df_resultado_filtrado
    .groupby(['titulo_eleitoral_candidato', 'id_eleicao', 'sigla_uf'], as_index=False)
    .agg(votos=('votos', 'sum'))
    .rename(columns={'titulo_eleitoral_candidato': 'titulo_eleitoral'})
)

# Validação
duplicados = df_resultado_uf.duplicated(subset=['titulo_eleitoral', 'id_eleicao', 'sigla_uf']).sum()
print(f"\n--- APÓS AGRUPAMENTO ---")
print(f"Total de registros          : {len(df_resultado_uf):,}")
print(f"Duplicatas na chave composta: {duplicados} (Esperado: 0)")
print(f"Nulos em titulo_eleitoral   : {df_resultado_uf['titulo_eleitoral'].isnull().sum()}")
print(f"Nulos em sigla_uf           : {df_resultado_uf['sigla_uf'].isnull().sum()}\n")

# Importa direto no banco
importar_para_banco(df_resultado_uf, 'resultado_candidatura_uf')

# %%
# ==========================================
# TABELA: BEM_PATRIMONIAL
# ==========================================
# Lê o arquivo de bens declarados pelos candidatos e filtra pelos
# pares válidos de candidatura. Valor pode ser NULL (bem sem avaliação).

df_bens = pd.read_csv(
    _DIR_TSE / 'Bens_Candidatos.csv',
    low_memory=False
)

print(f"Total de registros no arquivo: {len(df_bens):,}")

mapeamento = {
    'titulo_eleitoral_candidato' : 'titulo_eleitoral',
    'id_eleicao'                 : 'id_eleicao',
    'tipo_item'                  : 'tipo_item',
    'descricao_item'             : 'descricao_item',
    'valor_item'                 : 'valor_item'
}

df_bens_mapped = df_bens[list(mapeamento.keys())].rename(columns=mapeamento).copy()

# Corrige sufixo ".0" e notação científica nas chaves
for coluna in ['titulo_eleitoral', 'id_eleicao']:
    df_bens_mapped[coluna] = (
        df_bens_mapped[coluna]
        .apply(lambda x: str(int(float(x))) if pd.notna(x) and str(x).replace('.','').isdigit()
               else str(x).split('.')[0].strip())
    )

# Reutiliza os pares válidos da candidatura (já calculados acima)
pares_validos = set(zip(
    df_candidatos_limpo['titulo_eleitoral'],
    df_candidatos_limpo['id_eleicao']
))

df_bens_mapped['_par'] = list(zip(df_bens_mapped['titulo_eleitoral'], df_bens_mapped['id_eleicao']))
df_bens_limpo = df_bens_mapped[df_bens_mapped['_par'].isin(pares_validos)].drop(columns=['_par']).copy()
df_bens_limpo = df_bens_limpo.dropna(subset=['titulo_eleitoral', 'id_eleicao'])

# Diagnóstico
print("--- DIAGNÓSTICO (BEM_PATRIMONIAL) ---")
print(f"Total original             : {len(df_bens_mapped):,}")
print(f"Após filtro de candidatura : {len(df_bens_limpo):,}")
print(f"Nulos em titulo_eleitoral  : {df_bens_limpo['titulo_eleitoral'].isnull().sum()}")
print(f"Nulos em id_eleicao        : {df_bens_limpo['id_eleicao'].isnull().sum()}")
print(f"Nulos em valor_item        : {df_bens_limpo['valor_item'].isnull().sum():,}\n")

# Importa direto no banco
importar_para_banco(df_bens_limpo, 'bem_patrimonial')

# %%
# ==========================================
# TABELA: DESPESA
# ==========================================
# Os arquivos de despesa estão particionados por cargo/região.
# Cada arquivo contém múltiplos anos (2002, 2006, 2010, 2014, 2018, 2022).
#
# ATENÇÃO: arquivos de 2010 não têm id_eleicao preenchido (limitação do TSE).
# O fix abaixo detecta esse caso e preenche automaticamente com '37'
# (único id_eleicao para eleições de 2010).
#
# O filtro de pares_validos descarta automaticamente 2002 e 2006,
# mantendo apenas os anos do projeto: 2010, 2014, 2018 e 2022.

COLUNAS_DESPESA = [
    'titulo_eleitoral_candidato',
    'id_eleicao',
    'ano',
    'tipo_despesa',
    'descricao_despesa',
    'valor_despesa'
]

arquivos_despesa = os.listdir(DIR_DESPESA)

# Reutiliza os pares válidos da candidatura
pares_validos = set(zip(
    df_candidatos_limpo['titulo_eleitoral'],
    df_candidatos_limpo['id_eleicao']
))

total_inserido = 0

for arquivo in arquivos_despesa:
    caminho = os.path.join(DIR_DESPESA, arquivo)
    print(f"\nProcessando {arquivo}...")

    try:
        df_temp = pd.read_csv(
            caminho,
            low_memory=False,
            encoding='utf-8',
            on_bad_lines='skip'
        )
        df_temp = df_temp[COLUNAS_DESPESA].copy()
    except UnicodeDecodeError:
        df_temp = pd.read_csv(
            caminho,
            low_memory=False,
            encoding='latin1',
            on_bad_lines='skip'
        )
        df_temp = df_temp[COLUNAS_DESPESA].copy()
    except Exception as e:
        print(f"  -> Erro na leitura: {e}")
        continue

    # Preenche id_eleicao nulo para registros de 2010
    if df_temp['id_eleicao'].isna().all() and len(df_temp) > 0:
        df_temp['id_eleicao'] = '37'
        print("  -> id_eleicao preenchido com '37' para registros de 2010")

    # Normaliza as chaves
    for coluna in ['titulo_eleitoral_candidato', 'id_eleicao']:
        df_temp[coluna] = df_temp[coluna].apply(
            lambda x: str(int(float(x))) if pd.notna(x) and str(x).replace('.','').isdigit()
            else str(x).split('.')[0].strip()
        )

    # Filtra pelos pares válidos da candidatura
    df_temp['_par'] = list(zip(df_temp['titulo_eleitoral_candidato'], df_temp['id_eleicao']))
    df_temp = df_temp[df_temp['_par'].isin(pares_validos)].drop(columns=['_par']).copy()
    df_temp = df_temp.dropna(subset=['titulo_eleitoral_candidato', 'id_eleicao'])
    df_temp = df_temp[df_temp['titulo_eleitoral_candidato'] != 'nan']

    # Renomeia colunas para o formato do banco
    df_temp = df_temp.rename(columns={
        'titulo_eleitoral_candidato' : 'titulo_eleitoral',
        'valor_despesa'              : 'valor'
    })

    # Padroniza texto — astype(str) converte floats/NaN antes do strip/upper
    for col in ['tipo_despesa', 'descricao_despesa']:
        df_temp[col] = df_temp[col].astype(str).str.strip().str.upper()
        df_temp[col] = df_temp[col].replace('NAN', 'NAO INFORMADO')

    if len(df_temp) == 0:
        print(f"  -> 0 registros após filtro, pulando...")
        continue

    importar_para_banco(df_temp, 'despesa')
    total_inserido += len(df_temp)
    print(f"  -> Total acumulado: {total_inserido:,}")

print(f"\nConcluído! Total inserido em tse.despesa: {total_inserido:,} ✅")

# %%
# ==========================================
# TABELA: RECEITA
# ==========================================

COLUNAS_RECEITA = [
    'titulo_eleitoral_candidato',
    'id_eleicao',
    'ano',
    'fonte_receita',
    'natureza_receita',
    'descricao_receita',
    'valor_receita',
    'nome_doador',
    'tipo_doador_orig',
    'sigla_uf_doador'
]

arquivos_receita = os.listdir(DIR_RECEITA)

pares_validos = set(zip(
    df_candidatos_limpo['titulo_eleitoral'],
    df_candidatos_limpo['id_eleicao']
)) # usado no filtro mais abaixo

total_inserido = 0

for arquivo in arquivos_receita:
    caminho = os.path.join(DIR_RECEITA, arquivo)
    print(f"\nProcessando {arquivo}...")

    try:
        df_temp = pd.read_csv(
            caminho,
            low_memory=False,
            encoding='utf-8',
            on_bad_lines='skip'
        )
        df_temp = df_temp[COLUNAS_RECEITA].copy()
    except UnicodeDecodeError:
        df_temp = pd.read_csv(
            caminho,
            low_memory=False,
            encoding='latin1',
            on_bad_lines='skip'
        )
        df_temp = df_temp[COLUNAS_RECEITA].copy()
    except Exception as e:
        print(f"  -> Erro na leitura: {e}")
        continue

    # Preenche id_eleicao nulo para registros de 2010 (arquivo legado sem id_eleicao)
    if df_temp['id_eleicao'].isna().all() and (df_temp['ano'] == 2010).any():
        df_temp['id_eleicao'] = '37'
        print("  -> id_eleicao preenchido com '37' para registros de 2010")

    # Normaliza chaves
    for coluna in ['titulo_eleitoral_candidato', 'id_eleicao']:
        df_temp[coluna] = df_temp[coluna].apply(
            lambda x: str(int(float(x))) if pd.notna(x) and str(x).replace('.','').isdigit()
            else str(x).split('.')[0].strip()
        )

    # Filtra pelos pares válidos da candidatura
    df_temp['_par'] = list(zip(df_temp['titulo_eleitoral_candidato'], df_temp['id_eleicao']))
    df_temp = df_temp[df_temp['_par'].isin(pares_validos)].drop(columns=['_par']).copy()
    df_temp = df_temp.dropna(subset=['titulo_eleitoral_candidato', 'id_eleicao'])
    df_temp = df_temp[df_temp['titulo_eleitoral_candidato'] != 'nan']

    # Renomeia colunas
    df_temp = df_temp.rename(columns={
        'titulo_eleitoral_candidato' : 'titulo_eleitoral',
        'valor_receita'              : 'valor'
    })

    # Padroniza texto — astype(str) converte floats/NaN antes do strip/upper
    for col in ['descricao_receita', 'fonte_receita', 'natureza_receita', 'nome_doador', 'tipo_doador_orig']:
        df_temp[col] = df_temp[col].astype(str).str.strip().str.upper()
        df_temp[col] = df_temp[col].replace('NAN', 'NAO INFORMADO')

    # Trunca sigla_uf_doador para no máximo 2 caracteres
    df_temp['sigla_uf_doador'] = df_temp['sigla_uf_doador'].astype(str).str[:2]
    df_temp['sigla_uf_doador'] = df_temp['sigla_uf_doador'].replace('NA', None)

    if len(df_temp) == 0:
        print(f"  -> 0 registros após filtro, pulando...")
        continue

    importar_para_banco(df_temp, 'receita')
    total_inserido += len(df_temp)
    print(f"  -> Total acumulado: {total_inserido:,}")

print(f"\nConcluído! Total inserido em tse.receita: {total_inserido:,} ✅")