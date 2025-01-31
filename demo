import streamlit as st
import pandas as pd
import datetime
from io import BytesIO

# -----------------------------------------------------------------------------
# Configuração Geral do Streamlit
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Demonstração Local", layout="wide")

# -----------------------------------------------------------------------------
# Inicialização de session_state para armazenar dados temporariamente
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

# 2) Congregação
if "congregacao_data" not in st.session_state:
    st.session_state["congregacao_data"] = {
        "data_abertura": None,
        "data_encerramento": None,
        "endereco": "",
        "pastor_nome": "",
        "pastor_entrada": None,
        "pastor_saida": None
    }

# 3) Membros
if "membros_data" not in st.session_state:
    st.session_state["membros_data"] = pd.DataFrame(columns=[
        "id", "matricula", "nome", "foto", "ministerio", "endereco",
        "telefone", "sexo", "data_nascimento", "estado_civil", "nome_conjuge",
        "disciplina_data_ini", "disciplina_data_fim", "data_entrada",
        "tipo_entrada", "data_desligamento", "motivo_desligamento",
        "mes_aniversario"
    ])

# -----------------------------------------------------------------------------
# Página 1: Cadastro da Igreja
# -----------------------------------------------------------------------------
def page_igreja():
    st.header("Cadastro da Igreja")

    # Carregar dados do session_state
    igreja_data = st.session_state["igreja_data"]

    with st.form("form_igreja"):
        # Logotipo (upload de arquivo de imagem)
        uploaded_logo = st.file_uploader("Selecione o logotipo da Igreja (opcional)", type=["png", "jpg", "jpeg"])
        if uploaded_logo is not None:
            igreja_data["logotipo"] = uploaded_logo

        igreja_data["cnpj"] = st.text_input("CNPJ da Igreja", value=igreja_data["cnpj"])
        igreja_data["data_abertura"] = st.date_input(
            "Data de abertura",
            value=igreja_data["data_abertura"] if igreja_data["data_abertura"] else datetime.date.today()
        )
        igreja_data["endereco"] = st.text_input("Endereço Completo", value=igreja_data["endereco"])

        # Pastor
        igreja_data["pastor_nome"] = st.text_input("Nome do Pastor", value=igreja_data["pastor_nome"])
        col1, col2 = st.columns(2)
        with col1:
            igreja_data["pastor_entrada"] = st.date_input(
                "Data de Entrada do Pastor",
                value=igreja_data["pastor_entrada"] if igreja_data["pastor_entrada"] else datetime.date.today()
            )
        with col2:
            igreja_data["pastor_saida"] = st.date_input(
                "Data de Saída do Pastor",
                value=igreja_data["pastor_saida"] if igreja_data["pastor_saida"] else datetime.date.today()
            )

        submit_button = st.form_submit_button("Salvar Dados da Igreja")
        if submit_button:
            st.session_state["igreja_data"] = igreja_data
            st.success("Dados da Igreja salvos com sucesso!")

    # Mostrar dados (pré-visualização)
    #st.write("### Pré-visualização dos dados da Igreja")
    #st.json(st.session_state["igreja_data"])
    #if st.session_state["igreja_data"]["logotipo"] is not None:
        #st.image(st.session_state["igreja_data"]["logotipo"], width=100)

# -----------------------------------------------------------------------------
# Página 2: Cadastro da Congregação
# -----------------------------------------------------------------------------
def page_congregacao():
    st.header("Cadastro da Congregação")

    congregacao_data = st.session_state["congregacao_data"]

    with st.form("form_congregacao"):
        congregacao_data["data_abertura"] = st.date_input(
            "Data de abertura",
            value=congregacao_data["data_abertura"] if congregacao_data["data_abertura"] else datetime.date.today()
        )
        congregacao_data["data_encerramento"] = st.date_input(
            "Data de encerramento (se houver)",
            value=congregacao_data["data_encerramento"] if congregacao_data["data_encerramento"] else datetime.date.today()
        )
        congregacao_data["endereco"] = st.text_input("Endereço Completo", value=congregacao_data["endereco"])

        # Pastor
        congregacao_data["pastor_nome"] = st.text_input("Nome do Pastor", value=congregacao_data["pastor_nome"])
        col1, col2 = st.columns(2)
        with col1:
            congregacao_data["pastor_entrada"] = st.date_input(
                "Data de Entrada do Pastor",
                value=congregacao_data["pastor_entrada"] if congregacao_data["pastor_entrada"] else datetime.date.today()
            )
        with col2:
            congregacao_data["pastor_saida"] = st.date_input(
                "Data de Saída do Pastor",
                value=congregacao_data["pastor_saida"] if congregacao_data["pastor_saida"] else datetime.date.today()
            )

        submit_button = st.form_submit_button("Salvar Dados da Congregação")
        if submit_button:
            st.session_state["congregacao_data"] = congregacao_data
            st.success("Dados da Congregação salvos com sucesso!")

    # st.write("### Pré-visualização dos dados da Congregação")
    # st.json(st.session_state["congregacao_data"])

# -----------------------------------------------------------------------------
# Página 3: Cadastro de Membros (Adicionar, Alterar, Excluir)
# -----------------------------------------------------------------------------
def page_membros():
    st.header("Cadastro de Membros")

    # DataFrame com os membros
    membros_df = st.session_state["membros_data"]

    # Formulário de adicionar novo membro
    with st.expander("Adicionar Membro"):
        with st.form("form_add_membro"):
            matricula = st.text_input("Matrícula")
            nome = st.text_input("Nome completo")
            foto = st.file_uploader("Foto do Membro", type=["png", "jpg", "jpeg"])
            ministerio = st.text_input("Ministério (ex: Minist. Surdos)")
            endereco = st.text_input("Endereço Completo")
            telefone = st.text_input("Telefone")
            sexo = st.selectbox("Sexo", ["Masculino", "Feminino", "Outro"])
            data_nascimento = st.date_input("Data de Nascimento", value=datetime.date(1990, 1, 1))
            estado_civil = st.selectbox("Estado Civil", ["Solteiro(a)", "Casado(a)", "Divorciado(a)", "Viúvo(a)"])
            nome_conjuge = st.text_input("Nome do Cônjuge", value="")
            disciplina_data_ini = st.date_input("Data de início Disciplina", value=None)
            disciplina_data_fim = st.date_input("Data de saída Disciplina", value=None)
            data_entrada = st.date_input("Data de entrada (Ativo)", value=datetime.date.today())
            tipo_entrada = st.selectbox("Tipo de entrada", ["Batismo", "Transferência", "Aclamação"])
            data_desligamento = st.date_input("Data do desligamento (Inativo)", value=None)
            motivo_desligamento = st.selectbox(
                "Motivo do Desligamento",
                ["Nenhum", "A pedido", "Ausência", "Transferência", "Outra denominação", "Outros motivos"]
            )

            submitted = st.form_submit_button("Adicionar Membro")
            if submitted:
                new_id = len(membros_df) + 1
                mes_aniversario = data_nascimento.month
                new_row = {
                    "id": new_id,
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
        disabled=["id", "foto"]  # "foto" e "id" ficam inalteráveis nessa tela
    )
    if st.button("Salvar Alterações de Edição"):
        st.session_state["membros_data"] = edited_df
        st.success("Alterações atualizadas localmente.")

    # Excluir membro
    with st.expander("Excluir Membro"):
        membro_id_excluir = st.number_input("ID do membro a excluir", value=0)
        if st.button("Confirmar Exclusão"):
            if membro_id_excluir in st.session_state["membros_data"]["id"].values:
                st.session_state["membros_data"] = st.session_state["membros_data"][
                    st.session_state["membros_data"]["id"] != membro_id_excluir
                ]
                st.success(f"Membro ID {membro_id_excluir} excluído.")
            else:
                st.warning(f"ID {membro_id_excluir} não encontrado.")

    # Pré-visualizar fotos (caso queira)
    st.subheader("Fotos dos Membros")
    for idx, row in st.session_state["membros_data"].iterrows():
        if row["foto"] is not None:
            st.image(row["foto"], caption=f"ID: {row['id']} | Nome: {row['nome']}", width=100)

# -----------------------------------------------------------------------------
# Página 4: Relatórios
# -----------------------------------------------------------------------------
def page_relatorios():
    st.header("Relatórios")

    st.write("### Exemplos de geração de arquivos e botões")

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Gerar PDF - Certificado de Batismo"):
            # Aqui você chamaria a função que gera PDF (ex: ReportLab, WeasyPrint, etc.)
            st.success("Gerando PDF — Certificado de Batismo... (exemplo)")

    with col2:
        if st.button("Gerar Word - Carta de Transferência"):
            st.success("Gerando Word — Carta de Transferência... (exemplo)")

    with col3:
        if st.button("Gerar PDF - Carta por Ausência"):
            st.success("Gerando PDF — Carta por Ausência... (exemplo)")

    st.subheader("Gerar Excel Exemplo")
    df_mock = pd.DataFrame({
        "Nome": ["João", "Maria", "Pedro"],
        "Cargo": ["Membro", "Membro", "Pastor"]
    })
    if st.button("Gerar Excel"):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_mock.to_excel(writer, index=False, sheet_name="Plan1")
        st.download_button(
            label="Baixar Excel",
            data=output.getvalue(),
            file_name="relatorio_exemplo.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# -----------------------------------------------------------------------------
# Navegação Entre Páginas
# -----------------------------------------------------------------------------
pages = {
    "Cadastro da Igreja": page_igreja,
    "Cadastro da Congregação": page_congregacao,
    "Cadastro de Membros": page_membros,
    "Relatórios": page_relatorios
}

with st.sidebar:
    selected_page = st.selectbox("Selecione a Página", list(pages.keys()))

# Chamar a página selecionada
pages[selected_page]()
