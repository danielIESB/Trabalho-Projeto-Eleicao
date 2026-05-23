-- =============================================================================
-- PROJETO TSE — DDL DO BANCO DE DADOS
-- =============================================================================
-- Schema: tse
-- Banco  : PostgreSQL (Railway)
-- Eleições contempladas: 2010, 2014, 2018, 2022
--
-- ORDEM DE CRIAÇÃO (respeita dependências de FK):
--   1. municipio, eleicao, partido   — tabelas base
--   2. pessoa                        — depende de nada
--   3. candidatura                   — depende de pessoa, eleicao, partido
--   4. vaga                          — depende de eleicao, municipio
--   5. bem_patrimonial               — depende de candidatura
--   6. receita                       — depende de candidatura
--   7. despesa                       — depende de candidatura
--   8. resultado_candidatura_uf      — depende de candidatura
-- =============================================================================

DROP SCHEMA IF EXISTS "tse" CASCADE;
CREATE SCHEMA "tse";

-- -----------------------------------------------------------------------------
-- MUNICIPIO
-- Municípios brasileiros com cruzamento entre códigos TSE e IBGE.
-- -----------------------------------------------------------------------------
CREATE TABLE "tse".municipio (
    id_municipio     VARCHAR(10)  PRIMARY KEY,
    cd_municipio_tse VARCHAR(10),
    nm_municipio_tse VARCHAR(100) NOT NULL,
    sg_uf            VARCHAR(2)   NOT NULL
);

-- -----------------------------------------------------------------------------
-- ELEICAO
-- Eleições por ano e tipo (ordinária, suplementar, etc.).
-- -----------------------------------------------------------------------------
CREATE TABLE "tse".eleicao (
    id_eleicao   VARCHAR(20)  PRIMARY KEY,
    ano          INT          NOT NULL,
    tipo_eleicao VARCHAR(100),
    data_eleicao DATE
);

-- -----------------------------------------------------------------------------
-- PARTIDO
-- Partidos políticos identificados pelo número de urna.
-- A sigla pode variar ao longo do tempo (fusões, extinções).
-- -----------------------------------------------------------------------------
CREATE TABLE "tse".partido (
    numero_partido VARCHAR(10) PRIMARY KEY,
    sigla_partido  VARCHAR(20)
);

-- -----------------------------------------------------------------------------
-- PESSOA
-- Dados pessoais dos candidatos, deduplicados por título eleitoral.
-- -----------------------------------------------------------------------------
CREATE TABLE "tse".pessoa (
    titulo_eleitoral VARCHAR(20)  PRIMARY KEY,
    cpf              VARCHAR(20),
    nome             VARCHAR(255) NOT NULL,
    data_nascimento  DATE,
    genero           VARCHAR(50),
    raca             VARCHAR(50)
);

-- -----------------------------------------------------------------------------
-- CANDIDATURA
-- Candidaturas deferidas por eleição e cargo.
-- Chave primária composta: (titulo_eleitoral, id_eleicao).
-- id_municipio é NULL para cargos estaduais/federais.
-- -----------------------------------------------------------------------------
CREATE TABLE "tse".candidatura (
    sequencial_candidato VARCHAR(50),
    titulo_eleitoral     VARCHAR(20)  NOT NULL,
    id_eleicao           VARCHAR(20)  NOT NULL,
    numero_partido       VARCHAR(10)  NOT NULL,
    id_municipio         VARCHAR(10),
    sigla_uf             VARCHAR(2),
    cargo                VARCHAR(100) NOT NULL,
    numero_urna          VARCHAR(20),
    nome_urna            VARCHAR(255),
    situacao             VARCHAR(100),
    CONSTRAINT pk_candidatura PRIMARY KEY (titulo_eleitoral, id_eleicao),
    FOREIGN KEY (titulo_eleitoral) REFERENCES "tse".pessoa(titulo_eleitoral),
    FOREIGN KEY (id_eleicao)       REFERENCES "tse".eleicao(id_eleicao),
    FOREIGN KEY (numero_partido)   REFERENCES "tse".partido(numero_partido)
);

-- -----------------------------------------------------------------------------
-- VAGA
-- Vagas disponíveis por eleição, UF e cargo.
-- id_municipio é NULL para vagas estaduais/federais.
-- -----------------------------------------------------------------------------
CREATE TABLE "tse".vaga (
    id_vaga      SERIAL       PRIMARY KEY,
    id_eleicao   VARCHAR(20)  NOT NULL,
    sigla_uf     VARCHAR(2),
    id_municipio VARCHAR(10),
    cargo        VARCHAR(100) NOT NULL,
    vagas        INT,
    FOREIGN KEY (id_eleicao)   REFERENCES "tse".eleicao(id_eleicao),
    FOREIGN KEY (id_municipio) REFERENCES "tse".municipio(id_municipio)
);

-- -----------------------------------------------------------------------------
-- BEM_PATRIMONIAL
-- Bens declarados pelos candidatos no momento da candidatura.
-- valor_item pode ser NULL (bens sem avaliação monetária).
-- -----------------------------------------------------------------------------
CREATE TABLE "tse".bem_patrimonial (
    id_bem           SERIAL        PRIMARY KEY,
    titulo_eleitoral VARCHAR(20)   NOT NULL,
    id_eleicao       VARCHAR(20)   NOT NULL,
    tipo_item        VARCHAR(150),
    descricao_item   TEXT,
    valor_item       DECIMAL(15,2),
    FOREIGN KEY (titulo_eleitoral, id_eleicao)
        REFERENCES "tse".candidatura(titulo_eleitoral, id_eleicao)
);

-- -----------------------------------------------------------------------------
-- RECEITA
-- Receitas de campanha por candidato, incluindo dados do doador.
-- sigla_uf_doador truncado em 2 caracteres; NULL quando não informado.
-- -----------------------------------------------------------------------------
CREATE TABLE "tse".receita (
    id_receita        SERIAL        PRIMARY KEY,
    ano               INT,
    titulo_eleitoral  VARCHAR(20)   NOT NULL,
    id_eleicao        VARCHAR(20)   NOT NULL,
    valor             DECIMAL(15,2),
    fonte_receita     VARCHAR(150),
    natureza_receita  VARCHAR(150),
    descricao_receita TEXT,
    nome_doador       VARCHAR(255),
    tipo_doador_orig  VARCHAR(100),
    sigla_uf_doador   VARCHAR(2),
    FOREIGN KEY (titulo_eleitoral, id_eleicao)
        REFERENCES "tse".candidatura(titulo_eleitoral, id_eleicao)
);

-- -----------------------------------------------------------------------------
-- DESPESA
-- Despesas de campanha por candidato.
-- tipo_despesa e descricao_despesa padronizados em maiúsculas no ETL.
-- -----------------------------------------------------------------------------
CREATE TABLE "tse".despesa (
    id_despesa        SERIAL        PRIMARY KEY,
    ano               INT,
    titulo_eleitoral  VARCHAR(20)   NOT NULL,
    id_eleicao        VARCHAR(20)   NOT NULL,
    valor             DECIMAL(15,2),
    tipo_despesa      VARCHAR(150),
    descricao_despesa TEXT,
    FOREIGN KEY (titulo_eleitoral, id_eleicao)
        REFERENCES "tse".candidatura(titulo_eleitoral, id_eleicao)
);

-- -----------------------------------------------------------------------------
-- RESULTADO_CANDIDATURA_UF
-- Votos agregados por candidato, eleição e UF.
-- Chave primária composta: (titulo_eleitoral, id_eleicao, sigla_uf).
-- -----------------------------------------------------------------------------
CREATE TABLE "tse".resultado_candidatura_uf (
    titulo_eleitoral VARCHAR(20) NOT NULL,
    id_eleicao       VARCHAR(20) NOT NULL,
    sigla_uf         VARCHAR(2)  NOT NULL,
    votos            INT,
    CONSTRAINT pk_resultado PRIMARY KEY (titulo_eleitoral, id_eleicao, sigla_uf),
    FOREIGN KEY (titulo_eleitoral, id_eleicao)
        REFERENCES "tse".candidatura(titulo_eleitoral, id_eleicao)
);