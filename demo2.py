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
# Página 1: Cadastro da Igreja (CORRIGIDO)
# -----------------------------------------------------------------------------
def page_igreja():
    st.header("Cadastro da Igreja")

    igreja_data = st.session_state["igreja_data"]

    with st.form("form_igreja"):
        # Logotipo (upload de arquivo de imagem)
        uploaded_logo = st.file_uploader("Selecione o logotipo da Igreja (opcional)", 
                                         type=["png", "jpg", "jpeg"])
        if uploaded_logo is not None:
            igreja_data["logotipo"] = uploaded_logo

        igreja_data["cnpj"] = st.text_input("CNPJ da Igreja*", value=igreja_data["cnpj"])
        igreja_data["data_abertura"] = st.date_input(
            "Data de abertura*",
            value=igreja_data["data_abertura"] if igreja_data["data_abertura"] else datetime.date.today()
        )
        igreja_data["endereco"] = st.text_input("Endereço*", value=igreja_data["endereco"])

        # Pastor
        igreja_data["pastor_nome"] = st.text_input("Nome do Pastor*", value=igreja_data["pastor_nome"])
        col1, col2 = st.columns(2)
        with col1:
            igreja_data["pastor_entrada"] = st.date_input(
                "Data de Entrada do Pastor*",
                value=igreja_data["pastor_entrada"] if igreja_data["pastor_entrada"] else datetime.date.today()
            )
        with col2:
            igreja_data["pastor_saida"] = st.date_input(
                "Data de Saída do Pastor*",
                value=igreja_data["pastor_saida"] if igreja_data["pastor_saida"] else datetime.date.today()
            )

        submit_button = st.form_submit_button("Salvar Dados da Igreja")
        if submit_button:
            # Validar campos obrigatórios
            erros = []

            # Para campos de texto, usamos strip() para garantir que não estejam vazios
            if not igreja_data["cnpj"].strip():
                erros.append("CNPJ da Igreja")
            if not igreja_data["endereco"].strip():
                erros.append("Endereço")
            if not igreja_data["pastor_nome"].strip():
                erros.append("Nome do Pastor")

            # Para campos de data, basta checar se não é None
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
                # Se tudo certo, salvamos no session_state
                st.session_state["igreja_data"] = igreja_data
                st.success("Dados da Igreja salvos com sucesso!")


# -----------------------------------------------------------------------------
# Página 2: Cadastro de Membros (Adicionar, Alterar, Excluir)
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
            data_nascimento = st.date_input("Data de Nascimento*", value=None)
            estado_civil = st.selectbox(
                "Estado Civil*",
                ["Selecione...", "Solteiro(a)", "Casado(a)", "Divorciado(a)", "Viúvo(a)"]
            )
            nome_conjuge = st.text_input("Nome do Cônjuge (*Obrigatório se Casado)")
            disciplina_data_ini = st.date_input("Data de início Disciplina", value=None)
            disciplina_data_fim = st.date_input("Data de saída Disciplina", value=None)
            data_entrada = st.date_input("Data de entrada (Ativo)*", value=datetime.date.today())
            tipo_entrada = st.selectbox(
                "Tipo de entrada*",
                ["Selecione...", "Batismo", "Transferência", "Aclamação"]
            )
            data_desligamento = st.date_input("Data do desligamento (Inativo)", value=None)
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

                # Exemplo: data_nascimento e data_entrada obrigatórias
                if not data_nascimento:
                    erros.append("Data de Nascimento")
                if not data_entrada:
                    erros.append("Data de entrada (Ativo)")

                # Se houver erros, mostramos uma mensagem só
                if erros or telefone_invalido:
                    texto_erros = "### Atenção!\n\n" \
                                  "Há campos obrigatórios não preenchidos ou inválidos:\n\n"
                    for campo in erros:
                        texto_erros += f"- {campo}\n"
                    st.error(texto_erros)
                else:
                    new_id = len(membros_df) + 1
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
        disabled=["matricula", "foto"]  # "foto" e "id" ficam inalteráveis nessa tela
    )
    if st.button("Salvar Alterações de Edição"):
        st.session_state["membros_data"] = edited_df
        st.success("Alterações atualizadas localmente.")

    # Excluir membro
    with st.expander("Excluir Membro"):
            # Obter a lista de matrículas do DataFrame
            # (pode ser convertida em lista para o selectbox)
            lista_matriculas = list(membros_df["matricula"].unique())

            # Caso não haja membros, podemos tratar exceção:
            if len(lista_matriculas) == 0:
                st.info("Não há membros cadastrados para exclusão.")
            else:
                # Criamos o selectbox com as matrículas existentes
                matricula_excluir = st.selectbox(
                    "Matrícula do membro a excluir",
                    options=lista_matriculas
                )

                if st.button("Confirmar Exclusão"):
                    # Verifica se existe no DataFrame
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
            st.image(row["foto"], caption=f"ID: {row['id']} | Nome: {row['nome']}", width=100)

# -----------------------------------------------------------------------------
# Página 3: Relatórios
# -----------------------------------------------------------------------------
def page_relatorios():
    st.header("Relatórios")

    st.write("### Exemplos de geração de arquivos e botões")

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Gerar PDF - Certificado de Batismo"):
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
    "Cadastro de Membros": page_membros,
    "Relatórios": page_relatorios
}

with st.sidebar:
    selected_page = st.selectbox("Selecione a Página", list(pages.keys()))

pages[selected_page]()
