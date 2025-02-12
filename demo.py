import streamlit as st
import pandas as pd
import datetime
from io import BytesIO

# Bibliotecas necessárias para geração de documentos
from fpdf import FPDF
from docx import Document

# -----------------------------------------------------------------------------
# Configuração Geral do Streamlit
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Demonstração Local", layout="wide")

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
    st.header("Cadastro da Igreja")

    igreja_data = st.session_state["igreja_data"]

    # Verifica se já existe uma Igreja cadastrada (por exemplo, checando se o CNPJ não está vazio)
    if igreja_data["cnpj"]:
        # EDIÇÃO E EXCLUSÃO DE CADASTRO EXISTENTE
        st.subheader("Edição dos Dados da Igreja Existente")

        with st.form("form_igreja_edit"):
            uploaded_logo = st.file_uploader(
                "Selecione o logotipo da Igreja (opcional)",
                type=["png", "jpg", "jpeg"]
            )
            if uploaded_logo is not None:
                igreja_data["logotipo"] = uploaded_logo

            igreja_data["cnpj"] = st.text_input(
                "CNPJ da Igreja*", 
                value=igreja_data["cnpj"]
            )
            igreja_data["data_abertura"] = st.date_input(
                "Data de abertura*",
                value=igreja_data["data_abertura"] 
                       if igreja_data["data_abertura"] 
                       else datetime.date.today(), min_value=datetime.date(1900, 1, 1)
            )
            igreja_data["endereco"] = st.text_input(
                "Endereço*", 
                value=igreja_data["endereco"]
            )

            igreja_data["pastor_nome"] = st.text_input(
                "Nome do Pastor*", 
                value=igreja_data["pastor_nome"]
            )
            col1, col2 = st.columns(2)
            with col1:
                igreja_data["pastor_entrada"] = st.date_input(
                    "Data de Entrada do Pastor*",
                    value=igreja_data["pastor_entrada"] 
                           if igreja_data["pastor_entrada"] 
                           else datetime.date.today(), min_value=datetime.date(1900, 1, 1)
                )
            with col2:
                igreja_data["pastor_saida"] = st.date_input(
                    "Data de Saída do Pastor*",
                    value=igreja_data["pastor_saida"] 
                           if igreja_data["pastor_saida"] 
                           else datetime.date.today(), min_value=datetime.date(1900, 1, 1)
                )

            save_button = st.form_submit_button("Salvar Alterações")
            if save_button:
                # Validação simples
                erros = []
                if not igreja_data["cnpj"].strip():
                    erros.append("CNPJ da Igreja")
                if not igreja_data["endereco"].strip():
                    erros.append("Endereço")
                if not igreja_data["pastor_nome"].strip():
                    erros.append("Nome do Pastor")
                if not igreja_data["data_abertura"]:
                    erros.append("Data de Abertura")
                if not igreja_data["pastor_entrada"]:
                    erros.append("Data de Entrada do Pastor")
                if not igreja_data["pastor_saida"]:
                    erros.append("Data de Saída do Pastor")

                if erros:
                    texto_erros = "### Atenção!\n\n" \
                                  "Os seguintes campos obrigatórios não foram preenchidos:\n\n"
                    for campo in erros:
                        texto_erros += f"- {campo}\n"
                    st.error(texto_erros)
                else:
                    st.session_state["igreja_data"] = igreja_data
                    st.success("Dados da Igreja atualizados com sucesso!")

        # Botão para Excluir Igreja
        if st.button("Excluir Igreja"):
            st.session_state["igreja_data"] = {
                "logotipo": None,
                "cnpj": "",
                "data_abertura": None,
                "endereco": "",
                "pastor_nome": "",
                "pastor_entrada": None,
                "pastor_saida": None
            }
            st.success("Cadastro da Igreja excluído com sucesso.")
            st.rerun()

    else:
        # CRIAÇÃO DE NOVO CADASTRO (NÃO EXISTE IGREJA)
        st.subheader("Novo Cadastro de Igreja")

        with st.form("form_igreja_new"):
            uploaded_logo = st.file_uploader(
                "Selecione o logotipo da Igreja (opcional)",
                type=["png", "jpg", "jpeg"]
            )
            if uploaded_logo is not None:
                igreja_data["logotipo"] = uploaded_logo

            igreja_data["cnpj"] = st.text_input("CNPJ da Igreja*")
            igreja_data["data_abertura"] = st.date_input(
                "Data de abertura*",
                value=datetime.date.today(), min_value=datetime.date(1900, 1, 1)
            )
            igreja_data["endereco"] = st.text_input("Endereço*")

            igreja_data["pastor_nome"] = st.text_input("Nome do Pastor*")
            col1, col2 = st.columns(2)
            with col1:
                igreja_data["pastor_entrada"] = st.date_input(
                    "Data de Entrada do Pastor*",
                    value=datetime.date.today(), min_value=datetime.date(1900, 1, 1)
                )
            with col2:
                igreja_data["pastor_saida"] = st.date_input(
                    "Data de Saída do Pastor*",
                    value=datetime.date.today(), min_value=datetime.date(1900, 1, 1)
                )

            submit_button = st.form_submit_button("Salvar Dados da Igreja")
            if submit_button:
                # Validar campos obrigatórios
                erros = []
                if not igreja_data["cnpj"].strip():
                    erros.append("CNPJ da Igreja")
                if not igreja_data["endereco"].strip():
                    erros.append("Endereço")
                if not igreja_data["pastor_nome"].strip():
                    erros.append("Nome do Pastor")
                if not igreja_data["data_abertura"]:
                    erros.append("Data de Abertura")
                if not igreja_data["pastor_entrada"]:
                    erros.append("Data de Entrada do Pastor")
                if not igreja_data["pastor_saida"]:
                    erros.append("Data de Saída do Pastor")

                if erros:
                    texto_erros = "### Atenção!\n\n" \
                                  "Os seguintes campos obrigatórios não foram preenchidos:\n\n"
                    for campo in erros:
                        texto_erros += f"- {campo}\n"
                    st.error(texto_erros)
                else:
                    st.session_state["igreja_data"] = igreja_data
                    st.success("Dados da Igreja salvos com sucesso!")


# -----------------------------------------------------------------------------
# PÁGINA 2: Cadastro de Membros
# -----------------------------------------------------------------------------
def page_membros():
    st.header("Cadastro de Membros")

    # DataFrame com os membros
    membros_df = st.session_state["membros_data"]

    # Formulário de adicionar novo membro
    with st.expander("Adicionar Membro"):
        with st.form("form_add_membro"):
            matricula = st.text_input("Matrícula*")
            nome = st.text_input("Nome completo*")
            foto = st.file_uploader("Foto do Membro", type=["png", "jpg", "jpeg"])
            ministerio = st.text_input("Ministério*")
            endereco = st.text_input("Endereço*")
            telefone = st.text_input("Telefone* (XX)XXXXX-XXXX")

            # Validação simples de telefone
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
                # Verificação de campos obrigatórios
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

                # Se houver erros ou telefone inválido, mostramos uma mensagem só
                if erros or telefone_invalido:
                    texto_erros = "### Atenção!\n\n" \
                                  "Há campos obrigatórios não preenchidos ou inválidos:\n\n"
                    for campo in erros:
                        texto_erros += f"- {campo}\n"
                    st.error(texto_erros)
                else:
                    mes_aniversario = data_nascimento.month if data_nascimento else None

                    new_row = {
                        "matricula": matricula,
                        "nome": nome,
                        "foto": foto,
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

                    membros_df = pd.concat([membros_df, pd.DataFrame([new_row])], ignore_index=True)
                    st.session_state["membros_data"] = membros_df
                    st.success(f"Membro {nome} adicionado com sucesso!")

    # Exibição e edição dos membros
    st.subheader("Listagem de Membros")
    edited_df = st.data_editor(
        membros_df,
        hide_index=True,
        use_container_width=True,
        key="membros_editor",
        disabled=["matricula", "foto"]  # não permitir editar "foto" e "matricula"
    )
    if st.button("Salvar Alterações de Edição"):
        st.session_state["membros_data"] = edited_df
        st.success("Alterações atualizadas localmente.")

    # Excluir membro
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
                    st.session_state["membros_data"] = membros_df[
                        membros_df["matricula"] != matricula_excluir
                    ]
                    st.success(f"Membro com matrícula '{matricula_excluir}' excluído.")
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
