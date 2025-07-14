import sqlite3
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
CORS(app)

# --- Chave de API Simples para Demonstração (NÃO USE EM PRODUÇÃO!) ---
API_KEY_SECRET = "minha_chave_secreta_super_segura_123"

def conectar():
    # Assegure-se de que este caminho está correto para o seu ambiente
    caminho_do_banco = r"C:\Users\994155\Documents\GitHub\APP_SQLITE\SQLiteDatabaseBrowserPortable\appComercio.db"
    conn = sqlite3.connect(caminho_do_banco)
    conn.row_factory = sqlite3.Row
    return conn

def inicializar_banco_de_dados():
    conn = conectar()
    cursor = conn.cursor()

    # --- Tabela Produtos ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            TipoProduto TEXT NOT NULL,
            Tamanho TEXT NOT NULL,
            Genero TEXT NOT NULL,
            Cor TEXT NOT NULL,
            Preco REAL NOT NULL,
            Quantidade INTEGER NOT NULL DEFAULT 0
        )
    """)
    try:
        cursor.execute("ALTER TABLE Produtos ADD COLUMN Quantidade INTEGER DEFAULT 0")
        print("Coluna 'Quantidade' adicionada à tabela 'Produtos'.")
    except sqlite3.OperationalError as e:
        if "duplicate column name: Quantidade" in str(e):
            print("Coluna 'Quantidade' já existe na tabela 'Produtos'.")
        else:
            print(f"Erro ao adicionar coluna 'Quantidade': {e}")

    # --- Tabela CadastroUsuario ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS CadastroUsuario (
        IDCadastroUsuario INTEGER PRIMARY KEY AUTOINCREMENT,
        NomeUsuario TEXT NOT NULL UNIQUE,
        SenhaUsuario TEXT NOT NULL,
        SetorUsuario TEXT NOT NULL,
        IsActive INTEGER DEFAULT 1,
        NomeCompleto TEXT,
        Matricula TEXT UNIQUE
        )
    """)
    try:
        cursor.execute("ALTER TABLE CadastroUsuario ADD COLUMN IsActive INTEGER DEFAULT 1")
        print("Coluna 'IsActive' adicionada à tabela 'CadastroUsuario'.")
    except sqlite3.OperationalError as e:
        if "duplicate column name: IsActive" in str(e):
            print("Coluna 'IsActive' já existe na tabela 'CadastroUsuario'.")
        else:
            print(f"Erro ao adicionar coluna 'IsActive': {e}")

    try:
        cursor.execute("ALTER TABLE CadastroUsuario ADD COLUMN NomeCompleto TEXT")
        print("Coluna 'NomeCompleto' adicionada à tabela 'CadastroUsuario'.")
    except sqlite3.OperationalError as e:
        if "duplicate column name: NomeCompleto" in str(e):
            print("Coluna 'NomeCompleto' já existe na tabela 'CadastroUsuario'.")
        else:
            print(f"Erro ao adicionar coluna 'NomeCompleto': {e}")

    try:
        cursor.execute("ALTER TABLE CadastroUsuario ADD COLUMN Matricula TEXT UNIQUE")
        print("Coluna 'Matricula' adicionada à tabela 'CadastroUsuario'.")
    except sqlite3.OperationalError as e:
        if "duplicate column name: Matricula" in str(e):
            print("Coluna 'Matricula' já existe na tabela 'CadastroUsuario'.")
        else:
            print(f"Erro ao adicionar coluna 'Matricula': {e}")

    # --- POPULAR DADOS INICIAIS SE AS TABELAS ESTIVEREM VAZIAS ---

    # Popular Tabela CadastroUsuario
    cursor.execute("SELECT COUNT(*) FROM CadastroUsuario")
    if cursor.fetchone()[0] == 0:
        print("Populando tabela 'CadastroUsuario' com dados iniciais...")
        usuarios_iniciais = [
            ("admin", generate_password_hash("admin123"), "Administrativo", 1, "Administrador Geral", "00001"),
            ("joao", generate_password_hash("joao123"), "Vendas", 1, "João da Silva", "00002"),
            ("maria", generate_password_hash("maria123"), "Estoque", 1, "Maria Souza", "00003"),
            ("henrique", generate_password_hash("senha123"), "Financeiro", 1, "Henrique Costa", "00004"),
            ("henrique2", generate_password_hash("senha456"), "Financeiro", 1, "Henrique Santos", "00005"), # Nome duplicado, matrícula única
            ("ana", generate_password_hash("ana123"), "Secretariado", 0, "Ana Paula", "00006") # Usuário inativo
        ]
        cursor.executemany(
            "INSERT INTO CadastroUsuario (NomeUsuario, SenhaUsuario, SetorUsuario, IsActive, NomeCompleto, Matricula) VALUES (?, ?, ?, ?, ?, ?)",
            usuarios_iniciais
        )
        conn.commit()
        print("Dados iniciais de usuários inseridos.")
    else:
        print("Tabela 'CadastroUsuario' já contém dados, pulando população inicial.")

    # Popular Tabela Produtos
    cursor.execute("SELECT COUNT(*) FROM Produtos")
    if cursor.fetchone()[0] == 0:
        print("Populando tabela 'Produtos' com dados iniciais...")
        produtos_iniciais = [
            ("CAMISA", "M", "MASCULINO", "AZUL", 49.90, 100),
            ("CALÇA", "40", "FEMININO", "PRETO", 89.90, 50),
            ("TÊNIS", "42", "AMBOS", "BRANCO", 199.99, 30),
            ("BONÉ", "ÚNICO", "AMBOS", "VERMELHO", 25.00, 200)
        ]
        cursor.executemany(
            "INSERT INTO Produtos (TipoProduto, Tamanho, Genero, Cor, Preco, Quantidade) VALUES (?, ?, ?, ?, ?, ?)",
            produtos_iniciais
        )
        conn.commit()
        print("Dados iniciais de produtos inseridos.")
    else:
        print("Tabela 'Produtos' já contém dados, pulando população inicial.")

    conn.close()

inicializar_banco_de_dados()

### **Endpoints de Usuários**

@app.route("/CadastroUsuario", methods=["POST"])
def cadastrar_usuario():
    # Esta operação (criação) exige autenticação
    api_key_header = request.headers.get('X-API-Key')
    if not api_key_header or api_key_header != API_KEY_SECRET:
        return jsonify({"erro": "Acesso não autorizado. Chave de API inválida ou ausente."}), 401
    try:
        dados = request.get_json()
        nome_usuario = dados.get("NomeUsuario")
        senha_plana = dados.get("SenhaUsuario")
        setor = dados.get("SetorUsuario")
        is_active = dados.get("IsActive", True)
        nome_completo = dados.get("NomeCompleto")
        matricula = dados.get("Matricula")

        if not nome_usuario or not senha_plana or not setor:
            return jsonify({"erro": "Campos obrigatórios (NomeUsuario, SenhaUsuario, SetorUsuario) não preenchidos"}), 400

        if matricula:
            if not matricula.isdigit() or len(matricula) != 5:
                return jsonify({"erro": "Matrícula deve conter exatamente 5 dígitos numéricos."}), 400
        else:
            return jsonify({"erro": "Matrícula é obrigatória."}), 400

        conn = conectar()
        cursor = conn.cursor()

        cursor.execute("SELECT NomeUsuario FROM CadastroUsuario WHERE NomeUsuario = ?", (nome_usuario,))
        if cursor.fetchone():
            conn.close()
            return jsonify({"erro": "Nome de usuário já existe"}), 409

        cursor.execute("SELECT Matricula FROM CadastroUsuario WHERE Matricula = ?", (matricula,))
        if cursor.fetchone():
            conn.close()
            return jsonify({"erro": "Matrícula já existe"}), 409

        hashed_password = generate_password_hash(senha_plana)

        cursor.execute(
            """
            INSERT INTO CadastroUsuario (NomeUsuario, SenhaUsuario, SetorUsuario, IsActive, NomeCompleto, Matricula)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (nome_usuario, hashed_password, setor, 1 if is_active else 0, nome_completo, matricula)
        )
        conn.commit()
        conn.close()

        return jsonify({"mensagem": "Usuário cadastrado com sucesso"}), 201

    except Exception as e:
        print(f"Erro ao cadastrar usuário: {e}")
        return jsonify({"erro": str(e)}), 500

@app.route("/CadastroUsuario", methods=["GET"])
def listar_usuarios():
    # --- ALTERAÇÃO: REMOVIDA A EXIGÊNCIA DE API KEY PARA LISTAGEM ---
    try:
        conn = conectar()
        cursor = conn.cursor()
        search_term = request.args.get('search')

        select_columns = "IDCadastroUsuario, NomeUsuario, SetorUsuario, IsActive, NomeCompleto, Matricula"

        if search_term:
            cursor.execute(
                f"SELECT {select_columns} FROM CadastroUsuario WHERE NomeUsuario LIKE ? OR SetorUsuario LIKE ? OR NomeCompleto LIKE ? OR Matricula LIKE ?",
                (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%", f"%{search_term}%")
            )
        else:
            cursor.execute(f"SELECT {select_columns} FROM CadastroUsuario")

        rows = cursor.fetchall()
        conn.close()

        dados = []
        for row in rows:
            user_data = {col: row[col] for col in row.keys()}
            user_data['IsActive'] = bool(user_data['IsActive'])
            dados.append(user_data)

        return jsonify(dados)
    except Exception as e:
        print(f"Erro ao listar usuários: {e}")
        return jsonify({"erro": str(e)}), 500

@app.route("/CadastroUsuario/<string:nome_usuario>", methods=["PUT"])
def atualizar_usuario(nome_usuario):
    # Esta operação (atualização) exige autenticação
    api_key_header = request.headers.get('X-API-Key')
    if not api_key_header or api_key_header != API_KEY_SECRET:
        return jsonify({"erro": "Acesso não autorizado. Chave de API inválida ou ausente."}), 401
    try:
        dados = request.get_json()

        if not dados:
            return jsonify({"erro": "Nenhum dado fornecido para atualização"}), 400

        conn = conectar()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM CadastroUsuario WHERE NomeUsuario = ?", (nome_usuario,))
        usuario_existente = cursor.fetchone()
        if not usuario_existente:
            conn.close()
            return jsonify({"erro": "Usuário não encontrado"}), 404

        set_clauses = []
        update_values = []

        if 'SenhaUsuario' in dados and dados['SenhaUsuario']:
            hashed_password = generate_password_hash(dados['SenhaUsuario'])
            set_clauses.append("SenhaUsuario = ?")
            update_values.append(hashed_password)

        if 'SetorUsuario' in dados:
            set_clauses.append("SetorUsuario = ?")
            update_values.append(dados['SetorUsuario'])

        if 'IsActive' in dados:
            set_clauses.append("IsActive = ?")
            update_values.append(1 if dados['IsActive'] else 0)

        if 'NomeCompleto' in dados:
            set_clauses.append("NomeCompleto = ?")
            update_values.append(dados['NomeCompleto'])

        if 'Matricula' in dados:
            matricula = dados['Matricula']
            if not matricula.isdigit() or len(matricula) != 5:
                return jsonify({"erro": "Matrícula deve conter exatamente 5 dígitos numéricos."}), 400

            cursor.execute("SELECT Matricula FROM CadastroUsuario WHERE Matricula = ? AND NomeUsuario != ?", (matricula, nome_usuario))
            if cursor.fetchone():
                conn.close()
                return jsonify({"erro": "Matrícula já existe para outro usuário"}), 409

            set_clauses.append("Matricula = ?")
            update_values.append(matricula)

        if not set_clauses:
            conn.close()
            return jsonify({"mensagem": "Nenhum campo válido para atualização fornecido"}), 200

        update_query = f"UPDATE CadastroUsuario SET {', '.join(set_clauses)} WHERE NomeUsuario = ?"
        update_values.append(nome_usuario)

        cursor.execute(update_query, tuple(update_values))
        conn.commit()

        if cursor.rowcount == 0:
            conn.close()
            return jsonify({"erro": "Usuário não encontrado ou nenhum dado alterado"}), 404

        conn.close()
        return jsonify({"mensagem": f"Usuário '{nome_usuario}' atualizado com sucesso"}), 200

    except Exception as e:
        print(f"Erro ao atualizar usuário: {e}")
        return jsonify({"erro": str(e)}), 500

@app.route("/CadastroUsuario/<string:nome_usuario>", methods=["DELETE"])
def apagar_usuario_por_nome(nome_usuario):
    # Esta operação (deleção) exige autenticação
    api_key_header = request.headers.get('X-API-Key')
    if not api_key_header or api_key_header != API_KEY_SECRET:
        return jsonify({"erro": "Acesso não autorizado. Chave de API inválida ou ausente."}), 401
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM CadastroUsuario WHERE NomeUsuario = ?", (nome_usuario,))
        conn.commit()

        if cursor.rowcount == 0:
            conn.close()
            return jsonify({"erro": "Usuário não encontrado"}), 404

        conn.close()
        return jsonify({"mensagem": f"Usuário '{nome_usuario}' apagado com sucesso"}), 200

    except Exception as e:
        print(f"Erro ao apagar usuário por nome: {e}")
        return jsonify({"erro": str(e)}), 500

@app.route("/CadastroUsuario/id/<int:user_id>", methods=["DELETE"])
def apagar_usuario_por_id(user_id):
    # Esta operação (deleção) exige autenticação
    api_key_header = request.headers.get('X-API-Key')
    if not api_key_header or api_key_header != API_KEY_SECRET:
        return jsonify({"erro": "Acesso não autorizado. Chave de API inválida ou ausente."}), 401
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM CadastroUsuario WHERE IDCadastroUsuario = ?", (user_id,))
        conn.commit()

        if cursor.rowcount == 0:
            conn.close()
            return jsonify({"erro": "Usuário não encontrado com o ID especificado"}), 404

        conn.close()
        return jsonify({"mensagem": f"Usuário com ID '{user_id}' apagado com sucesso"}), 200

    except Exception as e:
        print(f"Erro ao apagar usuário por ID: {e}")
        return jsonify({"erro": str(e)}), 500

@app.route("/Login", methods=["POST"])
def login():
    try:
        dados = request.get_json()
        nome = dados.get("NomeUsuario")
        senha_digitada = dados.get("SenhaUsuario")

        if not nome or not senha_digitada:
            return jsonify({"erro": "Usuário e senha são obrigatórios"}), 400

        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT NomeUsuario, SenhaUsuario, IsActive FROM CadastroUsuario WHERE NomeUsuario = ?", (nome,))
        usuario = cursor.fetchone()
        conn.close()

        if usuario:
            stored_hashed_password = usuario["SenhaUsuario"]
            is_active = usuario["IsActive"]

            if is_active == 1 and check_password_hash(stored_hashed_password, senha_digitada):
                # Retorna a API_KEY_SECRET apenas se o login for bem-sucedido
                return jsonify({"mensagem": "Login bem-sucedido", "api_key": API_KEY_SECRET}), 200
            else:
                return jsonify({"erro": "Usuário ou senha inválidos, ou usuário inativo"}), 401
        else:
            return jsonify({"erro": "Usuário ou senha inválidos, ou usuário inativo"}), 401

    except Exception as e:
        print(f"Erro no login: {e}")
        return jsonify({"erro": str(e)}), 500

# ------------------- PRODUTOS (Com Autenticação para Escrita/Deleção) -------------------

@app.route("/CadastroProduto", methods=["POST"])
def cadastrar_produto():
    # Esta operação (criação) exige autenticação
    api_key_header = request.headers.get('X-API-Key')
    if not api_key_header or api_key_header != API_KEY_SECRET:
        return jsonify({"erro": "Acesso não autorizado. Chave de API inválida ou ausente."}), 401
    try:
        dados = request.get_json()
        tipo = dados.get("TipoProduto")
        tamanho = dados.get("Tamanho")
        genero = dados.get("Genero")
        cor = dados.get("Cor")
        preco = dados.get("Preco")
        quantidade = dados.get("Quantidade", 0)

        if not all([tipo, tamanho, genero, cor]) or preco is None:
            return jsonify({"erro": "Campos obrigatórios (TipoProduto, Tamanho, Genero, Cor, Preco) não preenchidos"}), 400

        conn = conectar()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO Produtos (TipoProduto, Tamanho, Genero, Cor, Preco, Quantidade)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (tipo, tamanho, genero, cor, preco, quantidade)
        )
        conn.commit()
        produto_id = cursor.lastrowid
        conn.close()

        return jsonify({"mensagem": "Produto cadastrado com sucesso", "id": produto_id}), 201

    except Exception as e:
        print(f"Erro ao cadastrar produto: {e}")
        return jsonify({"erro": str(e)}), 500


@app.route("/CadastroProduto", methods=["GET"])
def listar_produtos():
    # --- ALTERAÇÃO: REMOVIDA A EXIGÊNCIA DE API KEY PARA LISTAGEM ---
    try:
        conn = conectar()
        cursor = conn.cursor()
        search_term = request.args.get('search')

        if search_term:
            cursor.execute(
                "SELECT * FROM Produtos WHERE TipoProduto LIKE ? OR Tamanho LIKE ? OR Genero LIKE ? OR Cor LIKE ?",
                (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%", f"%{search_term}%")
            )
        else:
            cursor.execute("SELECT * FROM Produtos")

        rows = cursor.fetchall()
        conn.close()
        dados = [dict(row) for row in rows]
        return jsonify(dados)
    except Exception as e:
        print(f"Erro ao listar produtos: {e}")
        return jsonify({"erro": str(e)}), 500

@app.route("/CadastroProduto/<int:product_id>", methods=["PUT"])
def atualizar_produto(product_id):
    # Esta operação (atualização) exige autenticação
    api_key_header = request.headers.get('X-API-Key')
    if not api_key_header or api_key_header != API_KEY_SECRET:
        return jsonify({"erro": "Acesso não autorizado. Chave de API inválida ou ausente."}), 401
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({"erro": "Nenhum dado fornecido para atualização"}), 400

        conn = conectar()
        cursor = conn.cursor()

        set_clauses = []
        update_values = []

        field_mapping = {
            "TipoProduto": "TipoProduto",
            "Tamanho": "Tamanho",
            "Genero": "Genero",
            "Cor": "Cor",
            "Preco": "Preco",
            "Quantidade": "Quantidade"
        }

        for key, db_column in field_mapping.items():
            if key in dados:
                set_clauses.append(f"{db_column} = ?")
                update_values.append(dados[key])

        if not set_clauses:
            return jsonify({"erro": "Nenhum campo válido para atualização"}), 400

        update_query = f"UPDATE Produtos SET {', '.join(set_clauses)} WHERE id = ?"
        update_values.append(product_id)

        cursor.execute(update_query, tuple(update_values))
        conn.commit()

        if cursor.rowcount == 0:
            conn.close()
            return jsonify({"erro": "Produto não encontrado ou nenhum dado alterado"}), 404

        conn.close()
        return jsonify({"mensagem": "Produto atualizado com sucesso"}), 200

    except Exception as e:
        print(f"Erro ao atualizar produto: {e}")
        return jsonify({"erro": str(e)}), 500

@app.route("/CadastroProduto/<int:product_id>", methods=["DELETE"])
def apagar_produto(product_id):
    # Esta operação (deleção) exige autenticação
    api_key_header = request.headers.get('X-API-Key')
    if not api_key_header or api_key_header != API_KEY_SECRET:
        return jsonify({"erro": "Acesso não autorizado. Chave de API inválida ou ausente."}), 401
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Produtos WHERE id = ?", (product_id,))
        conn.commit()

        if cursor.rowcount == 0:
            conn.close()
            return jsonify({"erro": "Produto não encontrado"}), 404

        conn.close()
        return jsonify({"mensagem": "Produto apagado com sucesso"}), 200

    except Exception as e:
        print(f"Erro ao apagar produto: {e}")
        return jsonify({"erro": str(e)}), 500

@app.route("/AtualizarEstoque/<int:product_id>", methods=["PUT"])
def atualizar_estoque(product_id):
    api_key_header = request.headers.get('X-API-Key')
    if not api_key_header or api_key_header != API_KEY_SECRET:
        return jsonify({"erro": "Acesso não autorizado. Chave de API inválida ou ausente."}), 401

    try:
        dados = request.get_json()
        if not dados or "operacao" not in dados or "valor" not in dados:
            return jsonify({"erro": "É necessário fornecer 'operacao' (+, -, *, /) e 'valor'"}), 400

        operacao = dados["operacao"]
        valor = dados["valor"]

        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT Quantidade FROM Produtos WHERE id = ?", (product_id,))
        resultado = cursor.fetchone()

        if not resultado:
            conn.close()
            return jsonify({"erro": "Produto não encontrado"}), 404

        quantidade_atual = resultado["Quantidade"]

        if operacao == "+":
            nova_quantidade = quantidade_atual + valor
        elif operacao == "-":
            nova_quantidade = quantidade_atual - valor
        elif operacao == "*":
            nova_quantidade = quantidade_atual * valor
        elif operacao == "/":
            if valor == 0:
                return jsonify({"erro": "Divisão por zero não é permitida"}), 400
            nova_quantidade = quantidade_atual / valor
        else:
            return jsonify({"erro": "Operação inválida. Use apenas +, -, *, /"}), 400

        if nova_quantidade < 0:
            return jsonify({"erro": "Resultado da operação resulta em quantidade negativa"}), 400

        cursor.execute("UPDATE Produtos SET Quantidade = ? WHERE id = ?", (int(nova_quantidade), product_id))
        conn.commit()
        conn.close()

        return jsonify({
            "mensagem": "Estoque atualizado com sucesso",
            "nova_quantidade": int(nova_quantidade)
        }), 200

    except Exception as e:
        print(f"Erro ao atualizar estoque: {e}")
        return jsonify({"erro": str(e)}), 500


@app.route("/")
def homepage():
    return render_template("index.html") # Certifique-se de ter um arquivo index.html na pasta 'templates'

if __name__ == "__main__":
    app.run(debug=True)