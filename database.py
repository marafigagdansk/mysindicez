"""
database.py - Módulo de banco de dados do MySíndice Z
Gerencia a criação das tabelas e operações CRUD no SQLite.
"""

import sqlite3
import os
from datetime import datetime

# Obter diretório seguro (cross-platform, compativel com Android Flet)
def get_safe_data_dir():
    """Retorna um diretório seguro para gravação, compatível com Windows, macOS, Linux e Android Flet."""
    
    # Lista de possíveis bases para o diretório de dados do app
    potential_bases = [
        os.environ.get("FLET_USER_DATA_DIR"),  # Geralmente definido pelo Flet no Android
        os.environ.get("APPDATA"),              # Windows
        os.environ.get("XDG_DATA_HOME"),         # Linux
        os.path.expanduser("~") if os.name != "nt" else None,
        os.path.join(os.path.expanduser("~"), "AppData", "Roaming") if os.name == "nt" else None,
        os.getcwd(),                             # Último recurso: pasta atual
    ]

    for base in potential_bases:
        if not base:
            continue
            
        app_dir = os.path.join(base, "MySindiceZ")
        
        try:
            # Tenta criar a pasta se não existir
            os.makedirs(app_dir, exist_ok=True)
            
            # Teste de escrita: garante que realmente temos permissão na pasta
            test_file = os.path.join(app_dir, ".write_test")
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)
            
            # Se chegamos aqui, o diretório é válido e gravável!
            return app_dir
        except:
            # Se falhar nesse diretório, tenta o próximo da lista
            continue

    # Caso extremo: tenta na pasta onde o script está rodando
    try:
        app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "MySindiceZ_data"))
        os.makedirs(app_dir, exist_ok=True)
        return app_dir
    except:
        return "." # Fallback final: diretório atual

# Caminho do banco de dados (pasta de dados do app detectada em tempo de execução)
DB_PATH = os.path.join(get_safe_data_dir(), "condominio.db")


def get_connection():
    """Retorna uma conexão com o banco de dados SQLite."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Permite acessar colunas pelo nome
    conn.execute("PRAGMA foreign_keys = ON")  # Habilita chaves estrangeiras
    return conn


def inicializar_banco():
    """
    Cria todas as tabelas necessárias caso não existam.
    Deve ser chamada na inicialização do app.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Tabela de Configurações (saldo inicial e metadados do condomínio)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS configuracoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chave TEXT UNIQUE NOT NULL,
            valor TEXT NOT NULL,
            atualizado_em TEXT NOT NULL
        )
    """)

    # Tabela de Moradores
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS moradores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            unidade TEXT NOT NULL,
            ativo INTEGER NOT NULL DEFAULT 1,
            criado_em TEXT NOT NULL
        )
    """)

    # Tabela de Transações (Entradas e Saídas)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL CHECK(tipo IN ('entrada', 'saida')),
            valor REAL NOT NULL,
            descricao TEXT,
            data TEXT NOT NULL,
            morador_id INTEGER,
            comprovante_path TEXT,
            criado_em TEXT NOT NULL,
            FOREIGN KEY (morador_id) REFERENCES moradores(id)
        )
    """)

    conn.commit()
    conn.close()
    print("[OK] Banco de dados inicializado com sucesso!")


def limpar_banco_de_dados():
    """Limpa todas as tabelas (transações, moradores, configurações) e recria o banco limpo."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = OFF")
    cursor.execute("DROP TABLE IF EXISTS transacoes")
    cursor.execute("DROP TABLE IF EXISTS moradores")
    cursor.execute("DROP TABLE IF EXISTS configuracoes")
    conn.commit()
    conn.close()
    inicializar_banco()
    print("[OK] Banco de dados limpo com sucesso!")


# ========================================================
# CRUD - Configurações
# ========================================================

def salvar_configuracao(chave: str, valor: str):
    """Salva ou atualiza uma configuração (ex: saldo_inicial)."""
    conn = get_connection()
    agora = datetime.now().isoformat()
    conn.execute("""
        INSERT INTO configuracoes (chave, valor, atualizado_em)
        VALUES (?, ?, ?)
        ON CONFLICT(chave) DO UPDATE SET
            valor = excluded.valor,
            atualizado_em = excluded.atualizado_em
    """, (chave, valor, agora))
    conn.commit()
    conn.close()


def obter_configuracao(chave: str, padrao: str = None) -> str:
    """Retorna o valor de uma configuração pela chave."""
    conn = get_connection()
    row = conn.execute(
        "SELECT valor FROM configuracoes WHERE chave = ?", (chave,)
    ).fetchone()
    conn.close()
    return row["valor"] if row else padrao


# ========================================================
# CRUD - Moradores
# ========================================================

def inserir_morador(nome: str, unidade: str) -> int:
    """Insere um novo morador e retorna o ID gerado."""
    conn = get_connection()
    agora = datetime.now().isoformat()
    cursor = conn.execute(
        "INSERT INTO moradores (nome, unidade, criado_em) VALUES (?, ?, ?)",
        (nome, unidade, agora)
    )
    morador_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return morador_id


def listar_moradores(apenas_ativos: bool = True) -> list:
    """Retorna a lista de moradores (por padrão, apenas ativos)."""
    conn = get_connection()
    if apenas_ativos:
        rows = conn.execute(
            "SELECT * FROM moradores WHERE ativo = 1 ORDER BY unidade, nome"
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM moradores ORDER BY unidade, nome"
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def atualizar_morador(morador_id: int, nome: str, unidade: str):
    """Atualiza os dados de um morador existente."""
    conn = get_connection()
    conn.execute(
        "UPDATE moradores SET nome = ?, unidade = ? WHERE id = ?",
        (nome, unidade, morador_id)
    )
    conn.commit()
    conn.close()


def desativar_morador(morador_id: int):
    """Desativa (soft delete) um morador."""
    conn = get_connection()
    conn.execute(
        "UPDATE moradores SET ativo = 0 WHERE id = ?", (morador_id,)
    )
    conn.commit()
    conn.close()


# ========================================================
# CRUD - Transações (Entradas e Saídas)
# ========================================================

def inserir_transacao(
    tipo: str,
    valor: float,
    descricao: str,
    data: str,
    morador_id: int = None,
    comprovante_path: str = None
) -> int:
    """
    Insere uma nova transação.
    tipo: 'entrada' ou 'saida'
    data: formato 'YYYY-MM-DD'
    """
    conn = get_connection()
    agora = datetime.now().isoformat()
    cursor = conn.execute("""
        INSERT INTO transacoes (tipo, valor, descricao, data, morador_id, comprovante_path, criado_em)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (tipo, valor, descricao, data, morador_id, comprovante_path, agora))
    transacao_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return transacao_id


def listar_transacoes(tipo: str = None, mes: int = None, ano: int = None) -> list:
    """
    Lista transações com filtros opcionais.
    tipo: 'entrada', 'saida' ou None (todas)
    mes/ano: filtro por período
    """
    conn = get_connection()
    query = """
        SELECT t.*, m.nome AS morador_nome, m.unidade AS morador_unidade
        FROM transacoes t
        LEFT JOIN moradores m ON t.morador_id = m.id
        WHERE 1=1
    """
    params = []

    if tipo:
        query += " AND t.tipo = ?"
        params.append(tipo)

    if mes and ano:
        # Filtra pelo mês/ano usando substr na data (formato YYYY-MM-DD)
        query += " AND CAST(substr(t.data, 1, 4) AS INTEGER) = ?"
        query += " AND CAST(substr(t.data, 6, 2) AS INTEGER) = ?"
        params.append(ano)
        params.append(mes)
    elif ano:
        query += " AND CAST(substr(t.data, 1, 4) AS INTEGER) = ?"
        params.append(ano)

    query += " ORDER BY t.data DESC, t.id DESC"

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def excluir_transacao(transacao_id: int):
    """Remove uma transação pelo ID."""
    conn = get_connection()
    conn.execute("DELETE FROM transacoes WHERE id = ?", (transacao_id,))
    conn.commit()
    conn.close()


# ========================================================
# Cálculos Financeiros
# ========================================================

def calcular_saldo_atual() -> dict:
    """
    Calcula e retorna o saldo atual do condomínio.
    Retorna: {saldo_inicial, total_entradas, total_saidas, saldo_atual}
    """
    conn = get_connection()

    # Saldo inicial configurado
    saldo_inicial_str = obter_configuracao("saldo_inicial", "0")
    saldo_inicial = float(saldo_inicial_str)

    # Total de entradas
    row_entradas = conn.execute(
        "SELECT COALESCE(SUM(valor), 0) AS total FROM transacoes WHERE tipo = 'entrada'"
    ).fetchone()
    total_entradas = row_entradas["total"]

    # Total de saídas
    row_saidas = conn.execute(
        "SELECT COALESCE(SUM(valor), 0) AS total FROM transacoes WHERE tipo = 'saida'"
    ).fetchone()
    total_saidas = row_saidas["total"]

    conn.close()

    saldo_atual = saldo_inicial + total_entradas - total_saidas

    return {
        "saldo_inicial": saldo_inicial,
        "total_entradas": total_entradas,
        "total_saidas": total_saidas,
        "saldo_atual": saldo_atual
    }


def resumo_mensal(mes: int, ano: int) -> dict:
    """
    Retorna o resumo financeiro de um mês específico.
    Útil para a geração do relatório PDF.
    """
    conn = get_connection()

    # Entradas do mês
    row_ent = conn.execute("""
        SELECT COALESCE(SUM(valor), 0) AS total
        FROM transacoes
        WHERE tipo = 'entrada'
          AND CAST(substr(data, 1, 4) AS INTEGER) = ?
          AND CAST(substr(data, 6, 2) AS INTEGER) = ?
    """, (ano, mes)).fetchone()

    # Saídas do mês
    row_sai = conn.execute("""
        SELECT COALESCE(SUM(valor), 0) AS total
        FROM transacoes
        WHERE tipo = 'saida'
          AND CAST(substr(data, 1, 4) AS INTEGER) = ?
          AND CAST(substr(data, 6, 2) AS INTEGER) = ?
    """, (ano, mes)).fetchone()

    # Listagem detalhada
    entradas = listar_transacoes(tipo="entrada", mes=mes, ano=ano)
    saidas = listar_transacoes(tipo="saida", mes=mes, ano=ano)

    conn.close()

    return {
        "mes": mes,
        "ano": ano,
        "total_entradas": row_ent["total"],
        "total_saidas": row_sai["total"],
        "saldo_mes": row_ent["total"] - row_sai["total"],
        "entradas": entradas,
        "saidas": saidas
    }


# ========================================================
# Execução direta (para testes)
# ========================================================

if __name__ == "__main__":
    print("🔧 Inicializando banco de dados...")
    inicializar_banco()

    # Teste rápido: inserir dados de exemplo
    print("\n📝 Inserindo dados de teste...")

    # Config saldo inicial
    salvar_configuracao("saldo_inicial", "1500.00")
    print(f"   Saldo inicial: R$ {obter_configuracao('saldo_inicial')}")

    # Moradores
    id1 = inserir_morador("João Silva", "101")
    id2 = inserir_morador("Maria Santos", "202")
    id3 = inserir_morador("Pedro Oliveira", "303")
    print(f"   Moradores inseridos: IDs {id1}, {id2}, {id3}")

    # Transações
    inserir_transacao("entrada", 350.00, "Taxa condominial - Abril", "2026-04-05", id1)
    inserir_transacao("entrada", 350.00, "Taxa condominial - Abril", "2026-04-06", id2)
    inserir_transacao("saida", 200.00, "Conta de água", "2026-04-01")
    inserir_transacao("saida", 150.00, "Manutenção elevador", "2026-04-03")
    print("   Transações inseridas com sucesso!")

    # Saldo
    saldo = calcular_saldo_atual()
    print(f"\n💰 Resumo Financeiro:")
    print(f"   Saldo Inicial:    R$ {saldo['saldo_inicial']:.2f}")
    print(f"   Total Entradas:   R$ {saldo['total_entradas']:.2f}")
    print(f"   Total Saídas:     R$ {saldo['total_saidas']:.2f}")
    print(f"   Saldo Atual:      R$ {saldo['saldo_atual']:.2f}")

    # Resumo mensal
    resumo = resumo_mensal(4, 2026)
    print(f"\n📊 Resumo Abril/2026:")
    print(f"   Entradas: R$ {resumo['total_entradas']:.2f} ({len(resumo['entradas'])} lançamentos)")
    print(f"   Saídas:   R$ {resumo['total_saidas']:.2f} ({len(resumo['saidas'])} lançamentos)")
    print(f"   Saldo:    R$ {resumo['saldo_mes']:.2f}")

    # Lista moradores
    print(f"\n👥 Moradores cadastrados:")
    for m in listar_moradores():
        print(f"   [{m['unidade']}] {m['nome']}")

    print("\n✅ Todos os testes passaram!")
