-- ========================================================
-- SCRIPT SQL PARA O SISTEMA DE PIZZARIA (MODELO FÍSICO)
-- SGBD: Compatível com SQLite, MySQL e PostgreSQL
-- ========================================================
-- Criação da tabela Login
CREATE TABLE login (
    id_cliente INTEGER PRIMARY KEY,
    nome_usuario VARCHAR(100) NOT NULL UNIQUE,
    senha VARCHAR(255) NOT NULL,
    FOREIGN KEY (id_cliente) REFERENCES cliente(id_cliente) ON DELETE CASCADE
);

-- Criação da tabela Cliente
CREATE TABLE cliente (
    id_cliente INTEGER PRIMARY KEY AUTOINCREMENT,
    cpf VARCHAR(11) NOT NULL UNIQUE,
    nome_completo VARCHAR(150) NOT NULL,
    data_nascimento DATE,
    email VARCHAR(100),
    telefone VARCHAR(20),
    sexo VARCHAR(10),
    data_cadastro DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Criação da tabela Endereço (Relacionamento 1:1 com Cliente)
CREATE TABLE endereco (
    id_endereco INTEGER PRIMARY KEY AUTOINCREMENT,
    id_cliente INTEGER NOT NULL UNIQUE,
    rua VARCHAR(50) NOT NULL,
    numero INTEGER NOT NULL,
    bairro VARCHAR(100) NOT NULL,
    cidade VARCHAR(100) NOT NULL,
    cep VARCHAR(10) NOT NULL,
    complemento VARCHAR(50),
    FOREIGN KEY (id_cliente) REFERENCES cliente(id_cliente) ON DELETE CASCADE
);

-- Criação da tabela Pedido (Relacionamento 1:N com Cliente)
CREATE TABLE pedido (
    id_pedido INTEGER PRIMARY KEY AUTOINCREMENT,
    id_cliente INTEGER NOT NULL,
    data_hora_pedido DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    valor_total DECIMAL(10, 2) NOT NULL,
    tipo_pagamento VARCHAR(50) NOT NULL, 
    FOREIGN KEY (id_cliente) REFERENCES cliente(id_cliente)
);

-- Criação da tabela Produto
CREATE TABLE produto (
    id_produto INTEGER PRIMARY KEY AUTOINCREMENT,
    foto_produto_caminho VARCHAR(255),
    nome VARCHAR(100) NOT NULL,
    descricao TEXT,
    preco DECIMAL(10, 2) NOT NULL
);

-- Criação da tabela associativa Pedido_Produto (Relacionamento N:M entre Pedido e Produto)
CREATE TABLE pedido_produto (
    id_pedido INTEGER NOT NULL,
    id_produto INTEGER NOT NULL,
    quantidade INTEGER NOT NULL CHECK (quantidade > 0),
    preco_unitario_momento DECIMAL(10, 2) NOT NULL,
    -- data_hora_pedido POSTERIORMENTE INCLUIR
    PRIMARY KEY (id_pedido, id_produto),
    FOREIGN KEY (id_pedido) REFERENCES pedido(id_pedido) ON DELETE CASCADE,
    FOREIGN KEY (id_produto) REFERENCES produto(id_produto)
);

-- Criação da tabela Feedback (Relacionamento 1:0,1 com Pedido)
CREATE TABLE feedback (
    id_feedback INTEGER PRIMARY KEY AUTOINCREMENT,
    id_pedido INTEGER NOT NULL UNIQUE,
    nota INTEGER NOT NULL CHECK (nota BETWEEN 1 AND 5),
    comentario TEXT,
    data_hora_feedback DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    sentimento_associado VARCHAR(50),
    FOREIGN KEY (id_pedido) REFERENCES pedido(id_pedido) ON DELETE CASCADE
);
