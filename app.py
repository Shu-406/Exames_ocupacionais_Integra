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
        tipo_sel = st.selectbox("Tipo de Exame", tipos_existentes + ["Adicionar exame"], index=None)
        if tipo_sel == "Adicionar exame" or tipo_sel is None:
            tipo = st.text_input("Digite o novo tipo de exame")
            exames_filtrados = []
        else:
            tipo = tipo_sel
            # Filtra os nomes de exame relacionados ao tipo selecionado
            exames_filtrados = sorted(df[df["Tipo de Exame"] == tipo]["Exame"].dropna().unique().tolist())

        # Seleção ou novo nome de exame
        exame_sel = st.selectbox("Nome do Exame", exames_filtrados + ["Adicionar exame"], index=None)
        if exame_sel == "Adicionar exame" or exame_sel is None:
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
            with aba[1]:
        st.header("Consultar exames por data")

        data_consulta = st.date_input("Escolha a data para consulta", key="consulta")
        df = carregar_dados(aba_google)
        resultados = df[df["Data"] == data_consulta.strftime('%Y-%m-%d')].copy()

        # Rótulo no cabeçalho ("Agendado", "Realizado", etc.)
        status = st.selectbox("Tipo de registro:", ["Realizado", "Agendado"])

        if not resultados.empty:
            st.subheader(f"Exames {status.lower()}s em {data_consulta.strftime('%d/%m/%Y')}")

            # Exibir exames por nome, tipo ou ambos
            modo_exibicao = st.radio("Exibir colunas:", ["Nome", "Tipo", "Nome + Tipo"], horizontal=True)

            # Ajustar a visualização conforme a opção escolhida
            colunas_mostrar = []
            if modo_exibicao == "Nome":
                colunas_mostrar = ["Exame", "Quantidade"]
            elif modo_exibicao == "Tipo":
                colunas_mostrar = ["Tipo de Exame", "Quantidade"]
            else:
                colunas_mostrar = ["Tipo de Exame", "Exame", "Quantidade"]

            # Converter quantidade para int (sem casas decimais)
            resultados["Quantidade"] = resultados["Quantidade"].astype(int)

            # Mostrar a tabela
            st.dataframe(resultados[colunas_mostrar], use_container_width=True, hide_index=True)

            # Exclusão individual (mais técnica – identificando pelo nome do exame)
            st.divider()
            st.subheader("🗑️ Gerenciar exclusões")
            exame_selecionado = st.selectbox("Selecione um exame para excluir", resultados["Exame"].unique())
            if st.button("Excluir exame selecionado"):
                df = df[~((df["Data"] == data_consulta.strftime('%Y-%m-%d')) & (df["Exame"] == exame_selecionado))]
                salvar_dados(df.reset_index(drop=True), aba_google)
                st.success("Exame excluído com sucesso.")
                st.rerun()

            # Exclusão em massa
            st.warning("⚠️ Essa ação remove **todos os exames** dessa data!")
            confirmar = st.checkbox("Confirmo que desejo excluir todos os exames deste dia.")
            if st.button("🧹 Limpar todos os exames do dia", disabled=not confirmar):
                df = df[df["Data"] != data_consulta.strftime('%Y-%m-%d')]
                salvar_dados(df.reset_index(drop=True), aba_google)
                st.success("Todos os exames dessa data foram excluídos.")
                st.rerun()
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
