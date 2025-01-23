pip install --upgrade google-auth google-auth-httplib2 google-api-python-client


import streamlit as st
from datetime import datetime
import pandas as pd
from google.oauth2 import service_account
import gspread
import locale

print(st.secrets)
if "gcp_service_account" not in st.secrets:
    print("Erro: chave 'gcp_service_account' não encontrada no secrets.toml")

try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except:
    locale.setlocale(locale.LC_ALL, '')

class DotacaoApp:
    def __init__(self):
        self.configure_page()
        self.setup_google_sheets()
        self.load_data()
    
    def configure_page(self):
        st.set_page_config(page_title="Disponibilização de Dotação", layout="centered")
        
        st.markdown("""
            <style>
            /* Background color for the entire page */
            .stApp {
                background-color: #004f4b;
            }
            
            /* Header styling */
            .header-image {
                width: 100%;
                margin-bottom: 2rem;
            }
            
            .stTextInput > div > div > input {
                background-color: white;
                color: black;
            }
            .stButton > button {
                background-color: #00513F;
                color: white;
                width: 100%;
                height: 50px;
                margin-top: 20px;
            }
            .main > div {
                padding: 2rem;
                max-width: 800px;
                margin: 0 auto;
                background-color: #1E1E1E;
                border-radius: 8px;
            }
            div[data-testid="stSelectbox"] {
                background-color: grey;
                color: white !important;
                padding: 5px;
                border-radius: 4px;
                margin: 10px 0;
            }
            .stDateInput > div > div > input {
                background-color: white;
                color: black;
            }
            h1, h2, h3, label, p {
                color: white !important;
            }
            </style>
            """, unsafe_allow_html=True)

    def setup_google_sheets(self):
        try:
            credentials_info = st.secrets["gcp_service_account"]
            credentials = service_account.Credentials.from_service_account_info(
                credentials_info,
                scopes=['https://www.googleapis.com/auth/spreadsheets',
                        'https://www.googleapis.com/auth/drive']
            )

            self.gc = gspread.authorize(credentials)
            self.SHEET_ID = "1sBKOPTYYbG1q7Ivqz8IildycV-Fen0PSF1mfgIDse_U"
            
            try:
                spreadsheet = self.gc.open_by_key(self.SHEET_ID)
                self.worksheet = spreadsheet.worksheet('Registros')
            except gspread.WorksheetNotFound:
                spreadsheet = self.gc.open_by_key(self.SHEET_ID)
                self.worksheet = spreadsheet.add_worksheet('Registros', 1000, 20)
                headers = ['Data', 'Órgão', 'Dotação', 'Sequencial', 'Valor']
                self.worksheet.append_row(headers)
        
        except Exception as e:
            st.error(f"Erro na configuração do Google Sheets: {str(e)}")
            raise

    def load_data(self):
        try:
            self.df = pd.read_excel('DOTACOES.xlsx')
            self.orgaos = sorted(self.df['ÓRGÃO'].unique())
        except Exception as e:
            st.error(f"Erro ao carregar dados: {str(e)}")
            raise

    def format_currency(self, value):
        try:
            return locale.currency(float(value), grouping=True, symbol='R$')
        except:
            return f"R$ {value}"

    def save_to_sheets(self, data):
        try:
            row = [
                data['Data'],
                data['Órgão'],
                data['Dotação'],
                str(data['Sequencial']),
                data['Valor']
            ]
            self.worksheet.append_row(row)
            return True
        except Exception as e:
            raise Exception(f"Erro ao salvar na planilha: {str(e)}")

    def run(self):
        # Adicionar a imagem do header
        st.markdown("""
            <img src="https://i.ibb.co/d7pmTKS/Alimentos-E-Bebidas-Email-Header.jpg" class="header-image">
        """, unsafe_allow_html=True)
        
        st.title("Disponibilização de Dotação")

        selected_orgao = st.selectbox(
            "Selecione o Órgão",
            options=[''] + self.orgaos
        )

        if selected_orgao:
            dotacoes = sorted(self.df[self.df['ÓRGÃO'] == selected_orgao]['DOTAÇÃO'].unique())
            
            selected_dotacao = st.selectbox(
                "Selecione a Dotação",
                options=[''] + dotacoes
            )

            if selected_dotacao:
                sequenciais = sorted(
                    self.df[
                        (self.df['ÓRGÃO'] == selected_orgao) & 
                        (self.df['DOTAÇÃO'] == selected_dotacao)
                    ]['SEQUENCIAL'].unique()
                )
                
                selected_sequencial = st.selectbox(
                    "Selecione o Sequencial",
                    options=sequenciais
                )

                st.markdown("### Insira abaixo o valor disponibilizado")
                valor = st.text_input(
                    "Digite o valor (R$)",
                    help="Digite o valor em reais (ex: 1.000,00)"
                )

                st.markdown("### Data da Disponibilização")
                data = st.date_input(
                    "Data",
                    value=datetime.now(),
                    format="DD/MM/YYYY",
                    label_visibility="collapsed"
                )

                if st.button("ENVIAR PARA SMO"):
                    if valor:
                        try:
                            valor_float = float(valor.replace('.', '').replace(',', '.'))
                            registro = {
                                'Data': data.strftime('%d/%m/%Y'),
                                'Órgão': selected_orgao,
                                'Dotação': selected_dotacao,
                                'Sequencial': selected_sequencial,
                                'Valor': self.format_currency(valor_float)
                            }
                            
                            if self.save_to_sheets(registro):
                                st.success(f"""
                                    Dados enviados com sucesso!
                                    Valor: {self.format_currency(valor_float)}
                                    Data: {data.strftime('%d/%m/%Y')}
                                """)
                        
                        except ValueError:
                            st.error("Por favor, insira um valor numérico válido (ex: 1.000,00)")
                        except Exception as e:
                            st.error(f"Erro ao enviar dados: {str(e)}")
                    else:
                        st.warning("Por favor, preencha o valor.")

if __name__ == "__main__":
    app = DotacaoApp()
    app.run()