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
def page_igreja():
    st.header("Cadastro de Igreja")

    # Verifica se já existe um cadastro na tabela Igreja
    df_igreja = read_records("SELECT * FROM Igreja")
    
    if st.session_state["user_role"] == "adm-secretaria":
        st.subheader("Igreja Cadastrada")
        if df_igreja.empty:
            st.info("Nenhuma igreja cadastrada.")
        else:
            igreja = df_igreja.iloc[0]
            if igreja["logotipo"] is not None:
                st.image(igreja["logotipo"], caption="Logotipo da Igreja", width=200)
            st.write(f"**CNPJ:** {igreja['cnpj']}")
            st.write(f"**Data de Abertura:** {igreja['data_abertura']}")
            st.write(f"**Endereço:** {igreja['endereco']}")
            st.write(f"**Nome do Pastor:** {igreja['pastor_nome']}")
            st.write(f"**Data de Entrada do Pastor:** {igreja['pastor_entrada']}")
            st.write(f"**Data de Saída do Pastor:** {igreja['pastor_saida']}")
        return

    # Para usuários com permissões de edição (adm, adm-financeiro)
    if not df_igreja.empty:
        # Considerando que há apenas um registro
        igreja = df_igreja.iloc[0]
        
        # Inicializa a flag de edição, se não existir
        if "editar_igreja" not in st.session_state:
            st.session_state["editar_igreja"] = False

        
        # Modo de Edição
        if st.session_state["editar_igreja"]:
            st.subheader("Editar Dados da Igreja")
            with st.form("form_editar_igreja"):
                # Campo para logotipo: se um novo for enviado, substitui; caso contrário, mantém o atual
                uploaded_logo = st.file_uploader("Selecione um novo logotipo da Igreja (opcional)", 
                                                   type=["png", "jpg", "jpeg"])
                if uploaded_logo is not None:
                    logotipo_bin = uploaded_logo.read()
                else:
                    logotipo_bin = igreja["logotipo"]
                
                # CNPJ não é editável, pois é a chave primária
                cnpj_val = st.text_input("CNPJ da Igreja*", value=igreja["cnpj"], disabled=True)
                data_abertura_val = st.date_input("Data de Abertura*", value=igreja["data_abertura"])
                endereco_val = st.text_input("Endereço*", value=igreja["endereco"])
                pastor_nome_val = st.text_input("Nome do Pastor*", value=igreja["pastor_nome"])
                
                col1, col2 = st.columns(2)
                with col1:
                    pastor_entrada_val = st.date_input("Data de Entrada do Pastor*", value=igreja["pastor_entrada"])
                with col2:
                    pastor_saida_val = st.date_input("Data de Saída do Pastor*", value=igreja["pastor_saida"])
                
                submit_edit = st.form_submit_button("Atualizar Dados")
                
                if submit_edit:
                    update_sql = """
                        UPDATE Igreja
                        SET logotipo = ?,
                            data_abertura = ?,
                            endereco = ?,
                            pastor_nome = ?,
                            pastor_entrada = ?,
                            pastor_saida = ?
                        WHERE cnpj = ?
                    """
                    params_update = (
                        logotipo_bin,
                        data_abertura_val,
                        endereco_val,
                        pastor_nome_val,
                        pastor_entrada_val,
                        pastor_saida_val,
                        igreja["cnpj"]
                    )
                    ok_update = execute_query(update_sql, params_update)
                    if ok_update:
                        st.success("Dados da Igreja atualizados com sucesso!")
                        st.session_state["editar_igreja"] = False
                        st.rerun()  # Atualiza a página para refletir as mudanças
                    else:
                        st.error("Falha ao atualizar os dados da Igreja.")
            
            # Botão para cancelar a edição
            if st.button("Cancelar Edição"):
                st.session_state["editar_igreja"] = False
                st.rerun()
                
        # Modo de Visualização
        else:
            st.subheader("Igreja Cadastrada")
            if igreja["logotipo"] is not None:
                st.image(igreja["logotipo"], caption="Logotipo da Igreja", width=200)
            st.write(f"**CNPJ:** {igreja['cnpj']}")
            st.write(f"**Data de Abertura:** {igreja['data_abertura']}")
            st.write(f"**Endereço:** {igreja['endereco']}")
            st.write(f"**Nome do Pastor:** {igreja['pastor_nome']}")
            st.write(f"**Data de Entrada do Pastor:** {igreja['pastor_entrada']}")
            st.write(f"**Data de Saída do Pastor:** {igreja['pastor_saida']}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Editar Dados da Igreja"):
                    st.session_state["editar_igreja"] = True
                    st.rerun()
            with col2:
                if st.button("Excluir Igreja"):
                    delete_sql = "DELETE FROM Igreja WHERE cnpj = ?"
                    ok_delete = execute_query(delete_sql, (igreja["cnpj"],))
                    if ok_delete:
                        st.success("Igreja excluída com sucesso!")
                        st.rerun()
                    else:
                        st.error("Falha ao excluir a Igreja.")
                        
    else:
        # Caso não exista nenhum cadastro, exibe o formulário de cadastro
        st.subheader("Cadastrar Nova Igreja")
        with st.form("form_nova_igreja"):
            uploaded_logo = st.file_uploader("Selecione o logotipo da Igreja (opcional)", 
                                             type=["png", "jpg", "jpeg"])
            logotipo_bin = uploaded_logo.read() if uploaded_logo is not None else None

            cnpj_val = st.text_input("CNPJ da Igreja*")
            data_abertura_val = st.date_input("Data de Abertura*", value=None, min_value=datetime.date(1900, 1, 1))
            endereco_val = st.text_input("Endereço*")
            pastor_nome_val = st.text_input("Nome do Pastor*")

            col1, col2 = st.columns(2)
            with col1:
                pastor_entrada_val = st.date_input("Data de Entrada do Pastor*", value=None, min_value=datetime.date(1900, 1, 1))
            with col2:
                pastor_saida_val = st.date_input("Data de Saída do Pastor*", value=None, min_value=datetime.date(1900, 1, 1))

            submit_button = st.form_submit_button("Salvar Dados da Igreja")
            if submit_button:
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
                    texto_erros = "### Atenção!\n\nOs seguintes campos obrigatórios não foram preenchidos:\n\n"
                    for campo in erros:
                        texto_erros += f"- {campo}\n"
                    st.error(texto_erros)
                else:
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
                    ok = execute_query(insert_sql, params_insert)
                    if ok:
                        st.success("Dados da Igreja salvos com sucesso!")
                        st.rerun()
                    else:
                        st.error("Falha ao inserir dados da Igreja.")

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
            matricula_input = st.text_input("Matrícula*")
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
                if not matricula_input.strip():
                    erros.append("Matrícula")
                else:
                    try:
                        matricula_val = int(matricula_input)
                    except ValueError:
                        erros.append("Matrícula deve ser um número inteiro")
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

    df_editor = membros_df.drop(columns=["foto"])
    edited_df = st.data_editor(
        df_editor,
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
                SET matricula = ?, nome = ?, ministerio = ?, endereco = ?, telefone = ?, sexo = ?,
                    data_nascimento = ?, estado_civil = ?, nome_conjuge = ?,
                    disciplina_data_ini = ?, disciplina_data_fim = ?, data_entrada = ?,
                    tipo_entrada = ?, data_desligamento = ?, motivo_desligamento = ?, mes_aniversario = ?
                WHERE id = ?
            """
            update_params = (
                row["matricula"],
                row["nome"],
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
                try:
                    id_param = int(id_excluir)
                except ValueError:
                    st.error("ID inválido.")
                    return
                delete_sql = "DELETE FROM Membros WHERE id = ?"
                sucesso = execute_query(delete_sql, (id_param,))
                if sucesso is True:
                    st.success(f"Membro de ID {id_param} excluído.")
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
# Página 5 (exclusiva para adm-secretaria): Página para secretários
# -----------------------------------------------------------------------------
def page_secretaria():
    st.header("Página da Secretaria")
    st.write("Aqui você pode adicionar funcionalidades financeiras, por exemplo.")
# -----------------------------------------------------------------------------
# LÓGICA PRINCIPAL
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
