import streamlit as st
import pandas as pd
from datetime import datetime
import os
from io import BytesIO
import requests
from graphviz import Digraph
import base64
import matplotlib.pyplot as plt

ARQUIVO_EXCEL = "exames.xlsx"

def inicializar_planilha():
    if not os.path.exists(ARQUIVO_EXCEL):
        df = pd.DataFrame(columns=["Data", "Mês", "Tipo de Exame", "Exame", "Quantidade"])
        df.to_excel(ARQUIVO_EXCEL, index=False)

def carregar_dados():
    return pd.read_excel(ARQUIVO_EXCEL)

def salvar_dados(df):
    df.to_excel(ARQUIVO_EXCEL, index=False)

def gerar_excel_para_download(df):
    buffer = BytesIO()
    df.to_excel(buffer, index=False)
    buffer.seek(0)
    return buffer

def main():
    st.set_page_config(page_title="Registro de Exames", layout="centered")
    st.title("📊 Registro de Exames Médicos")

    aba = st.tabs(["➕ Adicionar Exame", "🔍 Consultar por Data"])

    with aba[0]:
        st.header("Adicionar novo exame")

        data = st.date_input("Data do exame")
        tipo = st.text_input("Tipo de Exame (ex: Laboratorial, Imagem)")
        exame = st.text_input("Nome do Exame (ex: Hemograma)")
        qtd = st.number_input("Quantidade de Atendimentos", min_value=0, step=1)

        if st.button("Salvar Exame"):
            if tipo and exame and qtd > 0:
                df = carregar_dados()
                mes = data.strftime("%B").capitalize()
                novo_registro = pd.DataFrame({
                    "Data": [data],
                    "Mês": [mes],
                    "Tipo de Exame": [tipo],
                    "Exame": [exame],
                    "Quantidade": [qtd]
                })
                df = pd.concat([df, novo_registro], ignore_index=True)
                salvar_dados(df)
                st.success("✅ Exame salvo com sucesso!")
            else:
                st.error("Por favor, preencha todos os campos corretamente.")

    with aba[1]:
        st.header("Consultar exames por data")

        data_consulta = st.date_input("Escolha a data para consulta", key="consulta")
        df = carregar_dados()
        resultados = df[df["Data"] == pd.to_datetime(data_consulta)]

        if not resultados.empty:
            st.subheader(f"Exames em {data_consulta.strftime('%d/%m/%Y')}")

            for i, row in resultados.iterrows():
                col1, col2 = st.columns([5, 1])
                with col1:
                    st.write(f"**{row['Exame']}** ({row['Tipo de Exame']}) - {row['Quantidade']} atendimentos")
                with col2:
                    if st.button("🗑️ Excluir", key=f"del_{i}"):
                        df.drop(index=i, inplace=True)
                        salvar_dados(df.reset_index(drop=True))
                        st.success(f"Exame '{row['Exame']}' excluído com sucesso!")
                        st.experimental_rerun()

            st.divider()
            st.warning("⚠️ Essa ação remove **todos os exames** dessa data!")
            confirmar = st.checkbox("Confirmo que desejo excluir todos os exames deste dia.")
            if st.button("🧹 Limpar todos os exames do dia", disabled=not confirmar):
                df = df[df["Data"] != pd.to_datetime(data_consulta)]
                salvar_dados(df.reset_index(drop=True))
                st.success("Todos os exames dessa data foram excluídos com sucesso!")
                st.experimental_rerun()
        else:
            st.info("Nenhum exame encontrado para essa data.")

        # 🔽 Botão de download da planilha completa
        st.divider()
        st.subheader("📥 Baixar todos os dados")
        df_completo = carregar_dados()
        buffer = gerar_excel_para_download(df_completo)
        nome_arquivo = f"exames_{datetime.today().strftime('%Y-%m-%d')}.xlsx"
        st.download_button(
            label="⬇️ Baixar planilha completa",
            data=buffer,
            file_name=nome_arquivo,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

if __name__ == "__main__":
    inicializar_planilha()
    main()




