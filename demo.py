import streamlit as st
import pandas as pd
import time
import datetime
import pyodbc
from io import BytesIO

# Bibliotecas necessárias para geração de documentos
from fpdf import FPDF
from docx import Document

# -----------------------------------------------------------------------------
# Configuração Geral do Streamlit
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Demonstração Local", layout="wide")

# -----------------------------------------------------------------------------
# Conexão com banco de dados
# -----------------------------------------------------------------------------
def get_connection():
    server = st.secrets["server"]
    database = st.secrets["database"]
    username = st.secrets["username"]
    password = st.secrets["password"]
    driver = '{ODBC Driver 17 for SQL Server}'
    try:
        conx = pyodbc.connect(
            'Driver='+ driver + ';Server='+ server + ';Database=' + database + ';Uid=' + username + ';Pwd={' + password + '}'
        )
        return conx
    except Exception as e:
        st.error(f"Erro ao conectar ao banco de dados: {e}")
        return None


def read_records(query, params=None):
    """
    Executa um SELECT e retorna um DataFrame.
    """
    conx = get_connection()
    if not conx:
        return pd.DataFrame()
    try:
        df = pd.read_sql(query, conx, params=params)
        return df
    except Exception as e:
        st.error(f"Erro ao ler registros: {e}")
        return pd.DataFrame()
    finally:
        conx.close()


# -----------------------------------------------------------------------------
# Executa um comando SQL (INSERT, UPDATE ou DELETE) e confirma (commit)
# -----------------------------------------------------------------------------

def execute_query(query, params=None):
    """
    Executa um comando SQL (INSERT, UPDATE ou DELETE) e confirma (commit).
    """
    conx = get_connection()
    if not conx:
        return False
    try:
        cursor = conx.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        conx.commit()
        if cursor.rowcount == 0:
            return "Nenhuma linha foi afetada."
        return True

    except Exception as e:
        error_message = str(e)
        # Se achar "2627" ou "duplicate key", é chave duplicada
        if "2627" in error_message or "duplicate key" in error_message:
            return "Entrada duplicada."  # Mensagem genérica
        else:
            return error_message
    finally:
        conx.close()


# -----------------------------------------------------------------------------
# SEÇÃO DE LOGIN
# -----------------------------------------------------------------------------

CREDENTIALS = {
    "adm": "adm123",
    "adm-financeiro": "fin123",
    "adm-secretaria": "sec123"
}

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "user_role" not in st.session_state:
    st.session_state["user_role"] = None


def login_screen():
    st.title("Login do Sistema")
    user = st.text_input("Usuário")
    password = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if user in CREDENTIALS and password == CREDENTIALS[user]:
            st.session_state["logged_in"] = True
            st.session_state["user_role"] = user
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos. Tente novamente.")


def logout_button():
    if st.sidebar.button("Sair"):
        st.session_state["logged_in"] = False
        st.session_state["user_role"] = None
        st.rerun()


# -----------------------------------------------------------------------------
# INICIALIZAÇÃO DE DADOS (session_state)
# -----------------------------------------------------------------------------

# 1) Igreja
if "igreja_data" not in st.session_state:
    st.session_state["igreja_data"] = {
        "logotipo": None,
        "cnpj": "",
        "data_abertura": None,
        "endereco": "",
        "pastor_nome": "",
        "pastor_entrada": None,
        "pastor_saida": None
    }

# 2) Membros (ajustado para novo esquema: PK 'id' e nova coluna 'matricula')
if "membros_data" not in st.session_state:
    st.session_state["membros_data"] = pd.DataFrame(columns=[
        "id", "matricula", "nome", "foto", "ministerio", "endereco",
        "telefone", "sexo", "data_nascimento", "estado_civil", "nome_conjuge",
        "disciplina_data_ini", "disciplina_data_fim", "data_entrada",
        "tipo_entrada", "data_desligamento", "motivo_desligamento",
        "mes_aniversario"
    ])


# -----------------------------------------------------------------------------
# PÁGINA 1: Cadastro da Igreja
# -----------------------------------------------------------------------------
# ... (sem alterações) ...

# -----------------------------------------------------------------------------
# PÁGINA 2: Cadastro de Membros
# -----------------------------------------------------------------------------

def page_membros():
    st.header("Cadastro de Membros")
    df_membros = read_records("SELECT * FROM Membros")

    # Para secretaria: apenas visualização
    if st.session_state["user_role"] == "adm-secretaria":
        if df_membros.empty:
            st.info("Ainda não há nenhum membro adicionado.")
        else:
            st.subheader("Listagem de Membros")
            st.dataframe(df_membros)
            st.subheader("Fotos dos Membros")
            for _, row in df_membros.iterrows():
                if row["foto"] is not None:
                    st.image(row["foto"], caption=row['nome'], width=100)
        return

    if df_membros.empty:
        st.info("Ainda não há nenhum membro adicionado.")

    # Sincroniza com session_state
    st.session_state["membros_data"] = df_membros
    membros_df = st.session_state["membros_data"]

    # Formulário de adicionar novo membro
    with st.expander("Adicionar Membro"):
        with st.form("form_add_membro"):
            matricula_input = st.text_input("Matrícula (opcional)")
            nome = st.text_input("Nome completo*")
            uploaded_foto = st.file_uploader("Foto do Membro (opcional)", type=["png", "jpg", "jpeg"])
            foto_bytes = uploaded_foto.read() if uploaded_foto is not None else None
            ministerio = st.text_input("Ministério*")
            endereco = st.text_input("Endereço*")
            telefone = st.text_input("Telefone* (DDXXXXXXXXX)")
            sexo = st.selectbox("Sexo*", ["Selecione...", "Masculino", "Feminino", "Outro"])
            data_nascimento = st.date_input("Data de Nascimento*", min_value=datetime.date(1900, 1, 1))
            estado_civil = st.selectbox("Estado Civil*", ["Selecione...", "Solteiro(a)", "Casado(a)", "Divorciado(a)", "Viúvo(a)"])
            nome_conjuge = st.text_input("Nome do Cônjuge (se Casado)")
            disciplina_data_ini = st.date_input("Data de início Disciplina", min_value=datetime.date(1900, 1, 1))
            disciplina_data_fim = st.date_input("Data de saída Disciplina", min_value=datetime.date(1900, 1, 1))
            data_entrada = st.date_input("Data de entrada (Ativo)*", value=datetime.date.today(), min_value=datetime.date(1900, 1, 1))
            tipo_entrada = st.selectbox("Tipo de entrada*", ["Selecione...", "Batismo", "Transferência", "Aclamação"])
            data_desligamento = st.date_input("Data do desligamento (Inativo)", min_value=datetime.date(1900, 1, 1))
            motivo_desligamento = st.selectbox("Motivo do Desligamento", ["Nenhum", "A pedido", "Ausência", "Transferência", "Outra denominação", "Outros motivos"])

            submitted = st.form_submit_button("Adicionar Membro")
            if submitted:
                erros = []
                # Validações básicas
                if not nome.strip(): erros.append("Nome completo")
                if not ministerio.strip(): erros.append("Ministério")
                if not endereco.strip(): erros.append("Endereço")
                if not telefone.strip(): erros.append("Telefone")
                if sexo == "Selecione...": erros.append("Sexo")
                if estado_civil == "Selecione...": erros.append("Estado Civil")
                if estado_civil == "Casado(a)" and not nome_conjuge.strip(): erros.append("Nome do Cônjuge")
                if tipo_entrada == "Selecione...": erros.append("Tipo de entrada")
                if not data_nascimento: erros.append("Data de Nascimento")
                if erros:
                    st.error("Preencha corretamente os campos obrigatórios: " + ", ".join(erros))
                else:
                    # Converte matrícula opcional
                    matricula_val = None
                    if matricula_input.strip():
                        try:
                            matricula_val = int(matricula_input)
                        except ValueError:
                            st.error("Matrícula deve ser um número inteiro.")
                            return
                    mes_aniversario = data_nascimento.month

                    insert_sql = """
                        INSERT INTO Membros (
                            matricula, nome, foto, ministerio, endereco, telefone, sexo,
                            data_nascimento, estado_civil, nome_conjuge,
                            disciplina_data_ini, disciplina_data_fim, data_entrada,
                            tipo_entrada, data_desligamento, motivo_desligamento,
                            mes_aniversario
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """
                    params = (
                        matricula_val,
                        nome,
                        foto_bytes,
                        ministerio,
                        endereco,
                        telefone,
                        sexo,
                        data_nascimento,
                        estado_civil,
                        nome_conjuge,
                        disciplina_data_ini,
                        disciplina_data_fim,
                        data_entrada,
                        tipo_entrada,
                        data_desligamento,
                        motivo_desligamento,
                        mes_aniversario
                    )
                    sucesso = execute_query(insert_sql, params)
                    if sucesso is True:
                        st.success("Membro inserido com sucesso!")
                        st.rerun()
                    else:
                        st.error(f"Falha ao inserir membro: {sucesso}")

    # Exibição e edição dos membros
    st.subheader("Listagem de Membros")
    edited_df = st.data_editor(
        membros_df,
        hide_index=True,
        use_container_width=True,
        key="membros_editor",
        column_config={
            "id": st.column_config.TextColumn("ID", disabled=True)
        }
    )

    # Salvar edições no banco
    if st.button("Salvar Alterações de Edição"):
        for _, row in edited_df.iterrows():
            update_sql = """
                UPDATE Membros
                SET matricula = ?, nome = ?, foto = ?, ministerio = ?, endereco = ?, telefone = ?, sexo = ?,
                    data_nascimento = ?, estado_civil = ?, nome_conjuge = ?,
                    disciplina_data_ini = ?, disciplina_data_fim = ?, data_entrada = ?,
                    tipo_entrada = ?, data_desligamento = ?, motivo_desligamento = ?, mes_aniversario = ?
                WHERE id = ?
            """
            update_params = (
                row["matricula"],
                row["nome"],
                row["foto"],
                row["ministerio"],
                row["endereco"],
                row["telefone"],
                row["sexo"],
                row["data_nascimento"],
                row["estado_civil"],
                row["nome_conjuge"],
                row["disciplina_data_ini"],
                row["disciplina_data_fim"],
                row["data_entrada"],
                row["tipo_entrada"],
                row["data_desligamento"],
                row["motivo_desligamento"],
                row["mes_aniversario"],
                row["id"]
            )
            execute_query(update_sql, update_params)
        st.success("Alterações atualizadas!")
        st.rerun()

    # Exclusão de membro
    with st.expander("Excluir Membro"):
        lista_ids = list(membros_df["id"].unique())
        if not lista_ids:
            st.info("Não há membros cadastrados para exclusão.")
        else:
            id_excluir = st.selectbox(
                "ID do membro a excluir",
                options=lista_ids
            )
            if st.button("Confirmar Exclusão"):
                delete_sql = "DELETE FROM Membros WHERE id = ?"
                sucesso = execute_query(delete_sql, (id_excluir,))
                if sucesso is True:
                    st.success(f"Membro de ID {id_excluir} excluído.")
                    st.session_state["membros_data"] = read_records("SELECT * FROM Membros")
                    st.rerun()
                else:
                    st.error(f"Falha ao excluir membro: {sucesso}")

    # Pré-visualizar fotos
    st.subheader("Fotos dos Membros")
    for _, row in st.session_state["membros_data"].iterrows():
        if row["foto"] is not None:
            st.image(row["foto"], caption=row['nome'], width=100)

# -----------------------------------------------------------------------------
# Demais páginas (Relatórios, Financeiro, Secretaria) e main() permanecem inalteradas
# -----------------------------------------------------------------------------

def main():
    if not st.session_state["logged_in"]:
        login_screen()
        return
    logout_button()
    role = st.session_state["user_role"]
    pages = {
        "adm": {"Cadastro de Igreja": page_igreja, "Cadastro de Membros": page_membros, "Relatórios": page_relatorios},
        "adm-financeiro": {"Cadastro de Igreja": page_igreja, "Cadastro de Membros": page_membros, "Relatórios": page_relatorios, "Página Financeira": page_financeiro},
        "adm-secretaria": {"Cadastro de Igreja": page_igreja, "Cadastro de Membros": page_membros}
    }.get(role, {})
    if not pages:
        st.error("Usuário desconhecido. Verifique as credenciais.")
        return
    with st.sidebar:
        choice = st.selectbox("Selecione a Página", list(pages.keys()))
    pages[choice]()

if __name__ == "__main__":
    main()
