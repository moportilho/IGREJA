import streamlit as st
import pandas as pd
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
        return True
    

    except Exception as e:
        error_message = str(e)
        # Se achar "2627" ou "duplicate key", é chave duplicada
        if "2627" in error_message or "duplicate key" in error_message:
            return "Matrícula já existe."  # Indicativo de matrícula duplicada
        else:
            return error_message  # Qualquer outro erro
    finally:
        conx.close()

# -----------------------------------------------------------------------------
# SEÇÃO DE LOGIN
# -----------------------------------------------------------------------------

# Definir credenciais (fixas para este exemplo)
CREDENTIALS = {
    "adm": "adm123",
    "adm-financeiro": "fin123"
}

# Inicializa variáveis de sessão para login/controle de acesso
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "user_role" not in st.session_state:
    st.session_state["user_role"] = None

def login_screen():
    """ Exibe a tela de login se o usuário não estiver logado. """
    st.title("Login do Sistema")
    user = st.text_input("Usuário")
    password = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if user in CREDENTIALS and password == CREDENTIALS[user]:
            st.session_state["logged_in"] = True
            st.session_state["user_role"] = user
        else:
            st.error("Usuário ou senha inválidos. Tente novamente.")

def logout_button():
    """ Botão de logout no sidebar. """
    if st.sidebar.button("Sair"):
        st.session_state["logged_in"] = False
        st.session_state["user_role"] = None
        st.rerun()  # Recarrega a página

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

# 2) Membros
if "membros_data" not in st.session_state:
    st.session_state["membros_data"] = pd.DataFrame(columns=[
        "matricula", "nome", "foto", "ministerio", "endereco",
        "telefone", "sexo", "data_nascimento", "estado_civil", "nome_conjuge",
        "disciplina_data_ini", "disciplina_data_fim", "data_entrada",
        "tipo_entrada", "data_desligamento", "motivo_desligamento",
        "mes_aniversario"
    ])

# -----------------------------------------------------------------------------
# PÁGINA 1: Cadastro da Igreja
# -----------------------------------------------------------------------------

def page_igreja():
    st.header("Cadastro de Nova Igreja")

    # Formulário simples para inserir SEM editar/excluir
    with st.form("form_nova_igreja"):

        # Carrega o logotipo (opcional) e converte em binário (se VARBINARY no banco)
        uploaded_logo = st.file_uploader("Selecione o logotipo da Igreja (opcional)", 
                                         type=["png", "jpg", "jpeg"])
        if uploaded_logo is not None:
            logotipo_bin = uploaded_logo.read()
        else:
            logotipo_bin = None

        cnpj_val = st.text_input("CNPJ da Igreja*")
        data_abertura_val = st.date_input("Data de abertura*",  value=None, min_value=datetime.date(1900, 1, 1))
        endereco_val = st.text_input("Endereço*")
        pastor_nome_val = st.text_input("Nome do Pastor*")

        col1, col2 = st.columns(2)
        with col1:
            pastor_entrada_val = st.date_input(
                "Data de Entrada do Pastor*",
                 value=None, min_value=datetime.date(1900, 1, 1)
            )
        with col2:
            pastor_saida_val = st.date_input(
                "Data de Saída do Pastor*",
                 value=None, min_value=datetime.date(1900, 1, 1)
            )

        # Botão para inserir no banco
        submit_button = st.form_submit_button("Salvar Dados da Igreja")

        if submit_button:
            # Validações simples
            erros = []
            if not cnpj_val.strip():
                erros.append("CNPJ da Igreja")
            if not endereco_val.strip():
                erros.append("Endereço")
            if not pastor_nome_val.strip():
                erros.append("Nome do Pastor")
            if not data_abertura_val:
                erros.append("Data de Abertura")
            if not pastor_entrada_val:
                erros.append("Data de Entrada do Pastor")
            if not pastor_saida_val:
                erros.append("Data de Saída do Pastor")

            if erros:
                texto_erros = "### Atenção!\n\n" \
                              "Os seguintes campos obrigatórios não foram preenchidos:\n\n"
                for campo in erros:
                    texto_erros += f"- {campo}\n"
                st.error(texto_erros)
            else:
                # Monta o INSERT
                insert_sql = """
                    INSERT INTO Igreja (
                        logotipo,
                        cnpj,
                        data_abertura,
                        endereco,
                        pastor_nome,
                        pastor_entrada,
                        pastor_saida
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """

                params_insert = (
                    logotipo_bin,
                    cnpj_val,
                    data_abertura_val,
                    endereco_val,
                    pastor_nome_val,
                    pastor_entrada_val,
                    pastor_saida_val
                )

                # Chama sua função execute_query(...) que você já tem no código
                ok = execute_query(insert_sql, params_insert)
                if ok:
                    st.success("Dados da Igreja salvos com sucesso!")
                else:
                    st.error("Falha ao inserir dados da Igreja.")

##DELETE
    # Lê todas as igrejas do banco
    df_igrejas = read_records("SELECT cnpj, pastor_nome FROM Igreja")
    st.subheader("Excluir Igreja Cadastrada:")

    # Seleciona a igreja a excluir com base no ID
    igreja_ids = df_igrejas["cnpj"].tolist()
    igreja_escolhida = st.selectbox(
        "Selecione o CNPJ da Igreja que deseja excluir",
        options=igreja_ids
    )

    if st.button("Confirmar Exclusão"):
        # Faz o DELETE
        delete_sql = "DELETE FROM Igreja WHERE cnpj = ?"
        ok_delete = execute_query(delete_sql, (igreja_escolhida,))
        if ok_delete:
            st.success(f"Igreja {igreja_escolhida} excluída com sucesso.")
            # Recarrega a listagem
            df_igrejas = read_records("SELECT cnpj, pastor_nome FROM Igreja")
        else:
            st.error("Falha ao excluir a Igreja.")



# -----------------------------------------------------------------------------
# PÁGINA 2: Cadastro de Membros
# -----------------------------------------------------------------------------

def page_membros():
    st.header("Cadastro de Membros")

    
    df_membros = read_records ("SELECT * FROM Membros")
    if df_membros.empty:
        st.info("Ainda não há nenhum membro adicionado.")

    # Armazena localmente na tela 
    st.session_state["membros_data"] = df_membros

    # DataFrame com os membros do banco
    membros_df = st.session_state["membros_data"]

    # Formulário de adicionar novo membro
    with st.expander("Adicionar Membro"):
        with st.form("form_add_membro"):
            matricula = st.text_input("Matrícula*")
            nome = st.text_input("Nome completo*")
            uploaded_foto = st.file_uploader("Foto do Membro (opcional)", 
                                                type=["png", "jpg", "jpeg"])
            if uploaded_foto is not None:
                foto_bytes = uploaded_foto.read()  # converte arquivo em bytes
            else:
                foto_bytes = None
                
            ministerio = st.text_input("Ministério*")
            endereco = st.text_input("Endereço*")
            telefone = st.text_input("Telefone* (XX)XXXXX-XXXX")
            telefone_invalido = False
            if telefone:
                if not telefone.isdigit():
                    st.error("Telefone deve conter apenas números.")
                    telefone_invalido = True
                elif len(telefone) != 11:
                    st.error("Telefone deve ter 11 dígitos (2 do DDD + 9 do número).")
                    telefone_invalido = True
            sexo = st.selectbox("Sexo*", ["Selecione...", "Masculino", "Feminino", "Outro"])
            data_nascimento = st.date_input("Data de Nascimento*", value=None, min_value=datetime.date(1900, 1, 1))
            estado_civil = st.selectbox(
                "Estado Civil*",
                ["Selecione...", "Solteiro(a)", "Casado(a)", "Divorciado(a)", "Viúvo(a)"]
            )
            nome_conjuge = st.text_input("Nome do Cônjuge (*Obrigatório se Casado)")
            disciplina_data_ini = st.date_input("Data de início Disciplina", value=None, min_value=datetime.date(1900, 1, 1))
            disciplina_data_fim = st.date_input("Data de saída Disciplina", value=None, min_value=datetime.date(1900, 1, 1))
            data_entrada = st.date_input("Data de entrada (Ativo)*", value=datetime.date.today(), min_value=datetime.date(1900, 1, 1))
            tipo_entrada = st.selectbox(
                "Tipo de entrada*",
                ["Selecione...", "Batismo", "Transferência", "Aclamação"]
            )
            data_desligamento = st.date_input("Data do desligamento (Inativo)", value=None, min_value=datetime.date(1900, 1, 1))
            motivo_desligamento = st.selectbox(
                "Motivo do Desligamento (*Obrigatório se desligado)",
                ["Nenhum", "A pedido", "Ausência", "Transferência", "Outra denominação", "Outros motivos"]
            )

            submitted = st.form_submit_button("Adicionar Membro")
            if submitted:
                
                erros = []
                if not matricula.strip():
                    erros.append("Matrícula")
                if not nome.strip():
                    erros.append("Nome completo")
                if not ministerio.strip():
                    erros.append("Ministério")
                if not endereco.strip():
                    erros.append("Endereço")
                if not telefone.strip():
                    erros.append("Telefone")
                if sexo == "Selecione...":
                    erros.append("Sexo")
                if estado_civil == "Selecione...":
                    erros.append("Estado Civil")
                if estado_civil == "Casado(a)" and not nome_conjuge.strip():
                    erros.append("Nome do Cônjuge")
                if tipo_entrada == "Selecione...":
                    erros.append("Tipo de entrada")
                if not data_nascimento:
                    erros.append("Data de Nascimento")
                if not data_entrada:
                    erros.append("Data de entrada (Ativo)")
                if erros or telefone_invalido:
                    texto_erros = "### Atenção!\n\n" \
                                  "Há campos obrigatórios não preenchidos ou inválidos:\n\n"
                    for campo in erros:
                        texto_erros += f"- {campo}\n"
                    st.error(texto_erros)
                else:
                    mes_aniversario = data_nascimento.month if data_nascimento else None

# =============================================
# 2) FAZER O INSERT NO BANCO
# =============================================

                    insert_sql = """
                        INSERT INTO Membros (
                            matricula, nome, foto, ministerio, endereco, telefone, sexo,
                            data_nascimento, estado_civil, nome_conjuge,
                            disciplina_data_ini, disciplina_data_fim, data_entrada,
                            tipo_entrada, data_desligamento, motivo_desligamento,
                            mes_aniversario
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

                        """
                    params = (
                        matricula,
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
                    elif sucesso == "duplicate":
                        st.error("Matrícula já existe.")
                    else:
                        st.error(f"Falha ao inserir membro: {sucesso}")

                    new_row = {
                        "matricula": matricula,
                        "nome": nome,
                        "foto": foto_bytes,
                        "ministerio": ministerio,
                        "endereco": endereco,
                        "telefone": telefone,
                        "sexo": sexo,
                        "data_nascimento": data_nascimento,
                        "estado_civil": estado_civil,
                        "nome_conjuge": nome_conjuge,
                        "disciplina_data_ini": disciplina_data_ini,
                        "disciplina_data_fim": disciplina_data_fim,
                        "data_entrada": data_entrada,
                        "tipo_entrada": tipo_entrada,
                        "data_desligamento": data_desligamento,
                        "motivo_desligamento": motivo_desligamento,
                        "mes_aniversario": mes_aniversario
                    }
    

    # Exibição e edição dos membros
    st.subheader("Listagem de Membros")
    edited_df = st.data_editor(
        membros_df,
        hide_index=True,
        use_container_width=True,
        key="membros_editor",
    ) 
    
# ============================================
# 3) Se quiser salvar EDIÇÃO no banco (UPDATE)
# ============================================

    if st.button("Salvar Alterações de Edição"):
        for idx, row in edited_df.iterrows():
            update_sql = """
                UPDATE Membros
                SET nome = ?, foto = ?, ministerio = ?, endereco = ?, telefone = ?, sexo = ?,
                    data_nascimento = ?, estado_civil = ?, nome_conjuge = ?,
                    disciplina_data_ini = ?, disciplina_data_fim = ?,
                    data_entrada = ?, tipo_entrada = ?, data_desligamento = ?,
                    motivo_desligamento = ?, mes_aniversario = ?
                WHERE matricula = ?
            """
            update_params = (
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
                row["matricula"]
            )
            execute_query(update_sql, update_params)
       
        st.session_state["membros_data"] = edited_df
        st.success("Alterações atualizadas!")

 # ======================================
 # 4) EXCLUIR DO BANCO (DELETE)
 # ====================================== 
    
    with st.expander("Excluir Membro"):
        lista_matriculas = list(membros_df["matricula"].unique())
        if len(lista_matriculas) == 0:
            st.info("Não há membros cadastrados para exclusão.")
        else:
            matricula_excluir = st.selectbox(
                "Matrícula do membro a excluir",
                options=lista_matriculas
            )

            if st.button("Confirmar Exclusão"):
                if matricula_excluir in membros_df["matricula"].values:

                    delete_sql = "DELETE FROM Membros WHERE matricula = ?"
                    sucesso = execute_query(delete_sql, (matricula_excluir,))
                    if sucesso:
                        st.success(f"Membro '{matricula_excluir}' excluído.")
                        # Recarrega a lista
                        df_membros = read_records("SELECT * FROM Membros")
                        st.session_state["membros_data"] = df_membros
                    else:
                        st.error("Falha ao excluir membro.")
                else:
                    st.warning(f"A matrícula '{matricula_excluir}' não foi encontrada.")
    
   
        # Pré-visualizar fotos (caso queira)
    st.subheader("Fotos dos Membros")
    for idx, row in st.session_state["membros_data"].iterrows():
        if row["foto"] is not None:
            st.image(row["foto"], caption=row['nome'], width=100)

# -----------------------------------------------------------------------------
# PÁGINA 3: Relatórios
# -----------------------------------------------------------------------------

def page_relatorios():
    st.header("Relatórios")

    membros_df = st.session_state["membros_data"]

    col1, col2, col3 = st.columns(3)

    # 1) Geração de PDF do Certificado de Batismo
    with col1:
        if st.button("Gerar PDF - Certificado de Batismo"):
            # Exemplo de uso de FPDF (biblioteca fpdf)
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=16, style='B')
            pdf.cell(200, 10, txt="CERTIFICADO DE BATISMO", ln=1, align='C')
            pdf.set_font("Arial", size=12)

            # Conteúdo simples de exemplo
            pdf.ln(10)
            pdf.multi_cell(0, 10, txt=(
                "Declaramos que o membro [NOME] recebeu o Santo Batismo nesta igreja,\n"
                "conforme as doutrinas cristãs, no dia [DATA].\n\n"
                "Assinatura:\n"
                "_________________________________________"
            ))

            # Gera PDF em memória
            pdf_data = pdf.output(dest="S").encode("latin-1")  # FPDF gera em bytes
            st.download_button(
                label="Baixar PDF Certificado",
                data=pdf_data,
                file_name="certificado_batismo.pdf",
                mime="application/pdf"
            )

    # 2) Geração de Word (DOCX) da Carta de Transferência
    with col2:
        if st.button("Gerar Word - Carta de Transferência"):
            doc = Document()
            doc.add_heading("CARTA DE TRANSFERÊNCIA", 0)

            p = doc.add_paragraph()
            p.add_run("Aos cuidados da Igreja de destino,\n\n").bold = True
            p.add_run(
                "Certificamos que o(a) membro [NOME] faz parte de nossa congregação, "
                "estando em comunhão, e solicitou transferência para a Igreja [DESTINO]. "
                "Concede-se, portanto, esta carta para os devidos fins.\n\n"
            )
            p.add_run("Atenciosamente,\n[Igreja de Origem]")

            # Salvar em memória
            doc_buffer = BytesIO()
            doc.save(doc_buffer)
            doc_buffer.seek(0)

            st.download_button(
                label="Baixar Word Transferência",
                data=doc_buffer.getvalue(),
                file_name="carta_transferencia.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )

    # 3) Geração de PDF - Carta por Ausência
    with col3:
        if st.button("Gerar PDF - Carta por Ausência"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=16, style='B')
            pdf.cell(200, 10, txt="CARTA POR AUSÊNCIA", ln=1, align='C')
            pdf.set_font("Arial", size=12)

            pdf.ln(10)
            pdf.multi_cell(0, 10, txt=(
                "Ao(À) Sr(a). [NOME DO MEMBRO],\n\n"
                "Consta em nossos registros que o(a) senhor(a) se encontra ausente de nossas atividades "
                "e cultos por período prolongado. Solicitamos o comparecimento ou contato para "
                "regularização de seu estado como membro ativo.\n\n"
                "Atenciosamente,\n[Igreja]"
            ))

            pdf_data = pdf.output(dest="S").encode("latin-1")
            st.download_button(
                label="Baixar PDF Carta Ausência",
                data=pdf_data,
                file_name="carta_ausencia.pdf",
                mime="application/pdf"
            )

    # 4) Geração de Excel com os membros cadastrados
    st.subheader("Gerar Excel dos Membros Cadastrados")
    if st.button("Gerar Excel"):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            membros_df.to_excel(writer, sheet_name="Membros", index=False)
        st.download_button(
            label="Baixar Excel com Membros",
            data=output.getvalue(),
            file_name="relatorio_membros.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# -----------------------------------------------------------------------------
# Página 4 (exclusiva para adm-financeiro): Página Financeira
# -----------------------------------------------------------------------------
def page_financeiro():
    st.header("Página Financeira")
    st.write("Aqui você pode adicionar funcionalidades financeiras, por exemplo.")

# -----------------------------------------------------------------------------
# LÓGICA PRINCIPAL
# -----------------------------------------------------------------------------
def main():
    # Se não estiver logado, mostra a tela de login
    if not st.session_state["logged_in"]:
        login_screen()
        return

    # Se estiver logado, mostra o menu lateral e as páginas correspondentes
    logout_button()  # Botão de sair no menu lateral

    # Verifica o tipo de usuário (role)
    user_role = st.session_state["user_role"]

    # Dicionário de páginas para cada tipo de usuário
    pages_adm = {
        "Cadastro da Igreja": page_igreja,
        "Cadastro de Membros": page_membros,
        "Relatórios": page_relatorios
    }
    pages_financeiro = {
        "Cadastro da Igreja": page_igreja,
        "Cadastro de Membros": page_membros,
        "Relatórios": page_relatorios,
        "Página Financeira": page_financeiro
    }

    if user_role == "adm":
        pages = pages_adm
    elif user_role == "adm-financeiro":
        pages = pages_financeiro
    else:
        st.error("Usuário desconhecido. Verifique as credenciais.")
        return

    with st.sidebar:
        selected_page = st.selectbox("Selecione a Página", list(pages.keys()))

    # Executa a função correspondente à página selecionada
    pages[selected_page]()

if __name__ == "__main__":
    main()
