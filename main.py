import streamlit as st
import pytesseract
from PIL import Image
import fitz
import pandas as pd
import requests
import io
import os
import base64
from google.oauth2 import service_account
from googleapiclient.discovery import build

st.set_page_config(page_title="FreshBooks Automation", layout="wide")

freshbooks_api_token = st.secrets["FRESHBOOKS_API_TOKEN"]
freshbooks_business_id = st.secrets["FRESHBOOKS_BUSINESS_ID"]
exchange_api_key = st.secrets["EXCHANGE_API_KEY"]
gcp_credentials = st.secrets["GCP_SERVICE_ACCOUNT_JSON"]
gsheet_id = st.secrets["GSHEET_ID"]

def extract_text_from_image(image_file):
    image = Image.open(image_file)
    return pytesseract.image_to_string(image)

def extract_text_from_pdf(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def process_csv(file):
    return pd.read_csv(file)

def convert_currency(amount, from_currency, to_currency="USD"):
    url = f"https://v6.exchangerate-api.com/v6/{exchange_api_key}/pair/{from_currency}/{to_currency}/{amount}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get("conversion_result", amount)
    return amount

def push_to_google_sheets(dataframe, sheet_range="Sheet1!A1"):
    credentials = service_account.Credentials.from_service_account_info(gcp_credentials, scopes=["https://www.googleapis.com/auth/spreadsheets"])
    service = build('sheets', 'v4', credentials=credentials)
    sheet = service.spreadsheets()
    values = [dataframe.columns.to_list()] + dataframe.values.tolist()
    body = {"values": values}
    result = sheet.values().update(spreadsheetId=gsheet_id, range=sheet_range, valueInputOption="RAW", body=body).execute()
    return result

def create_invoice_in_freshbooks(data):
    url = f"https://api.freshbooks.com/accounting/account/{freshbooks_business_id}/invoices/invoices"
    headers = {
        "Authorization": f"Bearer {freshbooks_api_token}",
        "Content-Type": "application/json",
        "Api-Version": "alpha"
    }
    payload = {
        "invoice": {
            "customerid": data.get("customerid", 12345),
            "create_date": data.get("date", "2025-05-17"),
            "lines": [
                {
                    "name": data.get("description", "Service"),
                    "qty": 1,
                    "unit_cost": {"amount": data.get("amount", "100.00"), "code": data.get("currency", "USD")}
                }
            ]
        }
    }
    r = requests.post(url, json=payload, headers=headers)
    return r.json()

st.title("📊 FreshBooks Data Entry Automation")

tab1, tab2, tab3 = st.tabs(["Upload Invoice/Receipt", "Upload Bank Statement", "Upload CSV File"])

with tab1:
    file = st.file_uploader("Upload Scanned Invoice or Receipt (Image or PDF)", type=["jpg", "jpeg", "png", "pdf"])
    currency = st.selectbox("Currency in document", ["USD", "CNY", "EUR", "GBP", "JPY"])
    if st.button("Extract & Submit to FreshBooks", key="invoice"):
        if file is not None:
            if file.type in ["application/pdf"]:
                text = extract_text_from_pdf(file)
            else:
                text = extract_text_from_image(file)
            st.text_area("Extracted Text", text, height=200)
            amount = float(st.text_input("Amount found in document", "100.00"))
            amount_converted = convert_currency(amount, currency, "USD")
            data = {"description": text[:50], "amount": str(amount_converted), "currency": "USD"}
            response = create_invoice_in_freshbooks(data)
            df = pd.DataFrame([data])
            push_to_google_sheets(df)
            st.success("Invoice created & pushed to Google Sheets")

with tab2:
    file = st.file_uploader("Upload Bank Statement (PDF)", type=["pdf"])
    currency = st.selectbox("Currency of Bank Account", ["USD", "CNY", "EUR", "GBP", "JPY"], key="bank")
    if st.button("Extract & Save Bank Data"):
        if file is not None:
            text = extract_text_from_pdf(file)
            st.text_area("Bank Statement Text", text, height=200)
            lines = text.split("\n")
            data = []
            for line in lines:
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        amt = float(parts[-1].replace(",", "").replace("¥", "").replace("$", ""))
                        amt_usd = convert_currency(amt, currency, "USD")
                        data.append({"description": " ".join(parts[:-1]), "amount": amt_usd, "currency": "USD"})
                    except:
                        continue
            df = pd.DataFrame(data)
            st.dataframe(df)
            push_to_google_sheets(df)
            st.success("Bank statement data saved to Google Sheets")

with tab3:
    file = st.file_uploader("Upload CSV File", type=["csv"])
    currency = st.selectbox("Currency of Amounts in CSV", ["USD", "CNY", "EUR", "GBP", "JPY"], key="csv")
    if st.button("Process CSV"):
        if file is not None:
            df = process_csv(file)
            if "amount" in df.columns:
                df["converted_amount"] = df["amount"].apply(lambda x: convert_currency(x, currency, "USD"))
                df["currency"] = "USD"
                push_to_google_sheets(df)
                st.dataframe(df)
                st.success("CSV data processed & saved")

