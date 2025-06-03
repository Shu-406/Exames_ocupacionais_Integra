import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from gspread_dataframe import get_as_dataframe, set_with_dataframe
import json

SHEET_ID = "1JJfbT3dUEsQogbS1Sj8P2rOxNFlGU0Cr25gCkKm3FnY"
SHEET_NAME = "Dados" 

meses_pt = {
    "January": "Janeiro", "February": "Fevereiro", "March": "Março",
    "April": "Abril", "May": "Maio", "June": "Junho",
    "July": "Julho", "August": "Agosto", "September": "Setembro",
    "October": "Outubro", "November": "Novembro", "December": "Dezembro"
}

# Carregar credenciais do Google
def autenticar_gspread():
    credenciais = json.loads(st.secrets["gcp_service_account"])
    cliente = gspread.service_account_from_dict(credenciais)
    planilha = cliente.open_by_key(SHEET_ID)
    aba = planilha.worksheet(SHEET_NAME)
    return aba

def carregar_dados(aba):
    df = get_as_dataframe(aba)
    df = df.dropna(how="all")  # Remove linhas vazias
    return df

def salvar_dados(df, aba):
    aba.clear()
    set_with_dataframe(aba, df)

def main():
    st.set_page_config(page_title="Registro de Exames", layout="centered")
    st.title("📊 Registro de Exames Médicos (Google Sheets)")

    aba = st.tabs(["➕ Adicionar Exame", "🔍 Consultar por Data"])

    aba_google = autenticar_gspread()
    df = carregar_dados(aba_google)

    with aba[0]:
        st.header("Adicionar novo exame")

        data = st.date_input("Data do exame")

        # Listas únicas dos tipos existentes
        tipos_existentes = sorted(df["Tipo de Exame"].dropna().unique().tolist())

        # Seleção ou novo tipo
        tipo_sel = st.selectbox("Tipo de Exame", tipos_existentes + ["Outro..."], index=None)
        if tipo_sel == "Outro..." or tipo_sel is None:
            tipo = st.text_input("Digite o novo tipo de exame")
            exames_filtrados = []
        else:
            tipo = tipo_sel
            # Filtra os nomes de exame relacionados ao tipo selecionado
            exames_filtrados = sorted(df[df["Tipo de Exame"] == tipo]["Exame"].dropna().unique().tolist())

        # Seleção ou novo nome de exame
        exame_sel = st.selectbox("Nome do Exame", exames_filtrados + ["Outro..."], index=None)
        if exame_sel == "Outro..." or exame_sel is None:
            exame = st.text_input("Digite o novo nome de exame")
        else:
            exame = exame_sel

        qtd = st.number_input("Quantidade de Atendimentos", min_value=0, step=1)

        if st.button("Salvar Exame"):
            if tipo and exame and qtd > 0:
                nome_mes_en = data.strftime("%B")
                nome_mes_pt = meses_pt[nome_mes_en]

                novo = pd.DataFrame({
                    "Data": [data.strftime('%Y-%m-%d')],
                    "Mês": [nome_mes_pt],
                    "Tipo de Exame": [tipo],
                    "Exame": [exame],
                    "Quantidade": [qtd]
                })
                df = pd.concat([df, novo], ignore_index=True)
                salvar_dados(df, aba_google)
                st.success("✅ Exame salvo com sucesso!")
            else:
                st.error("Preencha todos os campos corretamente.")


    with aba[1]:
        st.header("Consultar exames por data")

        # Escolha para cabeçalho Agendado ou Realizado
        status_exame = st.radio(
            "Status do exame:",
            options=["Agendado", "Realizado"],
            index=1,
            horizontal=True
        )

        # Escolha o que mostrar na lista
        mostrar_nome = st.checkbox("Mostrar Nome do Exame", value=True)
        mostrar_tipo = st.checkbox("Mostrar Tipo de Exame", value=True)

        data_consulta = st.date_input("Escolha a data para consulta", key="consulta")
        df = carregar_dados(aba_google)
        resultados = df[df["Data"] == data_consulta.strftime('%Y-%m-%d')]

        if not resultados.empty:
            st.subheader(f"{status_exame} em {data_consulta.strftime('%d/%m/%Y')}")

            for i, row in resultados.iterrows():
                col1, col2 = st.columns([6, 1])
                with col1:
                    partes = []
                    if mostrar_nome:
                        partes.append(f"**{row['Exame']}**")
                    if mostrar_tipo:
                        partes.append(f"({row['Tipo de Exame']})")
                    texto = " ".join(partes)
                    st.write(f"{texto} - {int(row['Quantidade'])} atendimentos")

                with col2:
                    # Botão pequeno de excluir com label menor
                    if st.button("❌", key=f"del_{i}", help="Excluir exame", use_container_width=True):
                        df.drop(index=row.name, inplace=True)
                        salvar_dados(df.reset_index(drop=True), aba_google)
                        st.success("Exame excluído.")
                        st.experimental_rerun()

            st.divider()
            st.warning("⚠️ Essa ação remove **todos os exames** dessa data!")
            confirmar = st.checkbox("Confirmo que desejo excluir todos os exames deste dia.")
            if st.button("🧹 Limpar todos os exames do dia", disabled=not confirmar):
                df = df[df["Data"] != data_consulta.strftime('%Y-%m-%d')]
                salvar_dados(df.reset_index(drop=True), aba_google)
                st.success("Todos os exames dessa data foram excluídos.")
                st.experimental_rerun()

        else:
            st.info("Nenhum exame encontrado para essa data.")

        # Download
        st.divider()
        st.subheader("📥 Baixar todos os dados")
        buffer = df.to_csv(index=False).encode("utf-8")
        nome_arquivo = f"exames_{datetime.today().strftime('%Y-%m-%d')}.csv"
        st.download_button("⬇️ Baixar CSV", data=buffer, file_name=nome_arquivo, mime="text/csv")

if __name__ == "__main__":
    main()
