Site do streamlit: https://demoigreja.streamlit.app

Conexão dinamica, colocare sempre após novo commit do código
server = st.secrets["server"]
database = st.secrets["database"]
username = st.secrets["username"]
password = st.secrets["password"]
driver = '{ODBC Driver 17 for SQL Server}'
