import streamlit as st
import pandas as pd

st.set_page_config(page_title="FreshBooks Automation Demo", layout="wide")
st.title("📄 FreshBooks Data Entry Automation (Demo Version)")

sample_invoice_text = """
Invoice #: 2025-INV-0023
Date: 2025-05-01
Vendor: Tech Supplies Ltd.
Description: 3x USB-C Cables
Total Amount: ¥350.00 (CNY)
"""

sample_bank_text = """
Transaction Date: 2025-05-03
Payment to: Cloud Hosting Services
Amount: €120.00
"""

currency_rates = {
    "CNY": 0.14,
    "EUR": 1.08,
    "USD": 1.00
}

st.subheader("1. Simulated Invoice Text Extraction")
st.code(sample_invoice_text, language="text")

invoice_amount_cny = 350.00
invoice_converted_usd = round(invoice_amount_cny * currency_rates["CNY"], 2)

invoice_data = {
    "description": "3x USB-C Cables",
    "original_amount": f"¥{invoice_amount_cny}",
    "converted_amount": f"${invoice_converted_usd}",
    "currency": "USD"
}

st.write("**Converted Invoice Data:**")
st.table(pd.DataFrame([invoice_data]))

st.subheader("2. Simulated Bank Statement Parsing")
st.code(sample_bank_text, language="text")

bank_amount_eur = 120.00
bank_converted_usd = round(bank_amount_eur * currency_rates["EUR"], 2)

bank_data = {
    "description": "Cloud Hosting Services",
    "original_amount": f"€{bank_amount_eur}",
    "converted_amount": f"${bank_converted_usd}",
    "currency": "USD"
}

st.write("**Converted Bank Transaction:**")
st.table(pd.DataFrame([bank_data]))

st.subheader("3. Mock FreshBooks Submission")
st.success("✅ Invoice and Bank Transaction 'submitted' to FreshBooks (simulated)")

st.subheader("4. Central Google Sheet (Mock Table)")
combined_df = pd.DataFrame([invoice_data, bank_data])
st.dataframe(combined_df, use_container_width=True)
