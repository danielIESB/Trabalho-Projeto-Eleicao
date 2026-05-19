-- =========================================================================
-- 1. DOMÍNIO GEOGRÁFICO E ELEITORAL (Tabelas Dimensão/Base)
-- =========================================================================

CREATE TABLE "TSE".municipio (
    id_municipio VARCHAR(10) PRIMARY KEY,
    cd_municipio_tse VARCHAR(10),
    nm_municipio_tse VARCHAR(100) NOT NULL,
    sg_uf VARCHAR(2) NOT NULL
);

CREATE TABLE "TSE".zona_eleitoral (
    id_zona SERIAL PRIMARY KEY,
    zona INT NOT NULL,
    id_municipio VARCHAR(10) NOT NULL,
    FOREIGN KEY (id_municipio) REFERENCES "TSE".municipio(id_municipio)
);

CREATE TABLE "TSE".eleicao (
    id_eleicao VARCHAR(20) PRIMARY KEY,
    ano INT NOT NULL,
    tipo_eleicao VARCHAR(100),
    data_eleicao DATE,
    turno INT
);

CREATE TABLE "TSE".partido (
    numero_partido VARCHAR(10) PRIMARY KEY,
    sigla_partido VARCHAR(20)
);

CREATE TABLE "TSE".vaga (
    id_vaga SERIAL PRIMARY KEY,
    id_eleicao VARCHAR(20) NOT NULL,
    id_municipio VARCHAR(10),
    cargo VARCHAR(100) NOT NULL,
    vagas INT,
    FOREIGN KEY (id_eleicao) REFERENCES "TSE".eleicao(id_eleicao),
    FOREIGN KEY (id_municipio) REFERENCES "TSE".municipio(id_municipio)
);


-- =========================================================================
-- 2. DOMÍNIO DO CANDIDATO
-- =========================================================================

CREATE TABLE "TSE".pessoa (
    titulo_eleitoral VARCHAR(20) PRIMARY KEY,
    cpf VARCHAR(20),
    nome VARCHAR(255) NOT NULL,
    data_nascimento DATE,
    genero VARCHAR(50),
    raca VARCHAR(50)
);

CREATE TABLE "TSE".candidatura (
    sequencial_candidato VARCHAR(50) NOT NULL,
    titulo_eleitoral VARCHAR(20) NOT NULL,
    id_eleicao VARCHAR(20) NOT NULL,
    numero_partido VARCHAR(10) NOT NULL,
    id_municipio VARCHAR(10),
    cargo VARCHAR(100) NOT NULL,
    numero_urna VARCHAR(20),
    nome_urna VARCHAR(255),
    situacao VARCHAR(100),
    CONSTRAINT pk_candidatura PRIMARY KEY (titulo_eleitoral, id_eleicao),
    CONSTRAINT uq_sequencial_eleicao UNIQUE (sequencial_candidato, id_eleicao),
    FOREIGN KEY (titulo_eleitoral) REFERENCES "TSE".pessoa(titulo_eleitoral),
    FOREIGN KEY (id_eleicao) REFERENCES "TSE".eleicao(id_eleicao),
    FOREIGN KEY (numero_partido) REFERENCES "TSE".partido(numero_partido),
    FOREIGN KEY (id_municipio) REFERENCES "TSE".municipio(id_municipio)
);

CREATE TABLE "TSE".bem_patrimonial (
    id_bem SERIAL PRIMARY KEY,
    titulo_eleitoral VARCHAR(20) NOT NULL,
    id_eleicao VARCHAR(20) NOT NULL,
    tipo_item VARCHAR(150),
    descricao_item TEXT,
    valor_item DECIMAL(15, 2),
    CONSTRAINT fk_bem_candidatura
        FOREIGN KEY (titulo_eleitoral, id_eleicao)
        REFERENCES "TSE".candidatura(titulo_eleitoral, id_eleicao)
);

-- =========================================================================
-- 3. DOMÍNIO FINANCEIRO (Prestações de Contas)
-- =========================================================================

CREATE TABLE "TSE".cnae (
    cnae_2_subclasse VARCHAR(20) PRIMARY KEY,
    cnae_2_classe VARCHAR(20),
    descricao_cnae VARCHAR(255)
);

CREATE TABLE "TSE".agente_financeiro (
    cpf_cnpj VARCHAR(20) PRIMARY KEY,
    nome VARCHAR(255),
    nome_rf VARCHAR(255),
    cnae_2_subclasse VARCHAR(20),
    FOREIGN KEY (cnae_2_subclasse) REFERENCES "TSE".cnae(cnae_2_subclasse)
);

CREATE TABLE "TSE".receita_despesa (
    sequencial VARCHAR(100) PRIMARY KEY,
    titulo_eleitoral VARCHAR(20) NOT NULL,
    id_eleicao VARCHAR(20) NOT NULL,
    cpf_cnpj_doador VARCHAR(20),
    dthora_transacao TIMESTAMP,
    valor_transacao DECIMAL(15, 2),
    origem VARCHAR(150),
    natureza VARCHAR(150),
    especie VARCHAR(150),
    numero_documento VARCHAR(100),
    descricao_despesa TEXT,
    tipo_transacao VARCHAR(50),
    CONSTRAINT fk_candidato
        FOREIGN KEY (titulo_eleitoral, id_eleicao)
        REFERENCES "TSE".candidatura(titulo_eleitoral, id_eleicao),
    CONSTRAINT fk_agente
        FOREIGN KEY (cpf_cnpj_doador)
        REFERENCES "TSE".agente_financeiro(cpf_cnpj)
);


-- =========================================================================
-- 4. DOMÍNIO DE RESULTADOS (Fatos / Apuração)
-- =========================================================================

CREATE TABLE "TSE".resultado_candidatura_municipio (
    titulo_eleitoral VARCHAR(20) NOT NULL,
    id_eleicao VARCHAR(20) NOT NULL,
    id_municipio VARCHAR(10) NOT NULL,
    votos INT,
    CONSTRAINT fk_resultado_candidatura
        FOREIGN KEY (titulo_eleitoral, id_eleicao)
        REFERENCES "TSE".candidatura(titulo_eleitoral, id_eleicao),
    CONSTRAINT fk_resultado_municipio
        FOREIGN KEY (id_municipio)
        REFERENCES "TSE".municipio(id_municipio)
);