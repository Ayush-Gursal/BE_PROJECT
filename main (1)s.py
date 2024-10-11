import os
import time
import pandas as pd
import json  # Import the JSON module
from dotenv import load_dotenv
load_dotenv()
import fitz  # PyMuPDF for PDF handling
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from tqdm import tqdm
import base64
import streamlit as st

# Set full screen mode for better visibility
st.set_page_config(layout="wide")

# Create a folder to store uploaded invoices
folder_invoice = "Uploaded_Invoices"
if not os.path.exists(folder_invoice):
    os.makedirs(folder_invoice)

# File uploader for a single invoice PDF
uploaded_invoice = st.file_uploader(
    "Upload Invoice", 
    type=["pdf"], 
    accept_multiple_files=False  # Only allow one file upload
)

# Save uploaded file to the folder and prepare PDFs for viewing
invoice_text = None
invoice_pdf_url = None

if uploaded_invoice:
    # Get the file name and path
    file_name = uploaded_invoice.name
    file_path = os.path.join(folder_invoice, file_name)
    
    # Save the uploaded PDF file
    with open(file_path, "wb") as f:
        f.write(uploaded_invoice.getbuffer())
    
    # Parse the uploaded PDF file to extract text
    reader = fitz.open(file_path)
    text = ''
    for page_num in range(len(reader)):
        page = reader[page_num]
        text += page.get_text() + '\n'
    
    # Store extracted text and PDF path
    invoice_text = text
    invoice_pdf_url = file_path  # Store the path to the uploaded PDF
    
    st.write(f"File '{file_name}' parsed successfully.")
else:
    st.write("No files uploaded.")

# Storing the API environment variable in api_key
api_key = os.getenv("GOOGLE_API_KEY")

# Pydantic class for invoice processing
class InvoiceScreener(BaseModel):
    id: str
    customer_id: str
    customer_name: str
    billing_contact: dict
    shipping_contact: dict
    invoice_date: str
    due_date: str
    subtotal: str
    invoice_tax: str
    invoice_amount: str
    line_items: list
    paid_amount: str
    balance: str
    status: str
    notes: str

# Prompt for screening invoices ---------------------------------------
Prompt_invoice = """
Task: Process the following invoice and extract detailed information into structured fields. Please include all relevant details such as:

- Invoice ID
- Customer ID
- Customer Name
- Billing Contact (first name, last name, email, phone, address)
- Shipping Contact (first name, last name, email, phone, address)
- Invoice Date
- Due Date
- Subtotal
- Tax
- Total Amount
- Paid Amount
- Balance
- Status
- Notes
- Line Items (product name, description, unit price, quantity, total)

Invoice:
<invoice>
{invoice}
</invoice>

Please format the extracted information as a JSON object.
{format_instructions}
"""

# LLM Instantiation 
def llm_instance():
    return ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        temperature=0,
        max_tokens=None,
        timeout=None,
        max_retries=2,
        use_auth_token=api_key
    )

def process_invoices(invoice_text, invoice_screener_chain):
    st.write("Invoice processing has begun:")
    invoice_score_list = []
    
    try:
        # Process the entire invoice text as a string
        invoice_score = invoice_screener_chain.invoke({"invoice": invoice_text})
        
        # Check if invoice_score is already a dict
        if isinstance(invoice_score, dict):
            invoice_score_list.append(invoice_score)
        else:
            # If it's a string (JSON), parse it
            invoice_data = json.loads(invoice_score)
            invoice_score_list.append(invoice_data)
    except Exception as e:
        st.error(f"Error processing invoice: {str(e)}")
    
    return invoice_score_list

# Generate HTML for the invoice
def generate_invoice_html(invoice_data):
    html_content = f"""
    <html>
    <head>
    <style>
        body {{font-family: Arial, sans-serif; max-width: 1000px; margin: auto; padding: 20px;}}
        h2, h3 {{text-align: center; margin-bottom: 20px;}}
        table {{width: 100%; border-collapse: collapse; margin-bottom: 20px;}}
        th, td {{border: 1px solid #ddd; padding: 10px; text-align: left;}}
        th {{background-color: #f2f2f2;}}
    </style>
    </head>
    <body>
    <h2>Invoice Details</h2>
    
    <div>
        <h3>General Information</h3>
        <table>
            <tr><th>Invoice ID</th><td>{invoice_data.get('id', 'N/A')}</td></tr>
            <tr><th>Customer Name</th><td>{invoice_data.get('customer_name', 'N/A')}</td></tr>
            <tr><th>Status</th><td>{invoice_data.get('status', 'N/A')}</td></tr>
            <tr><th>Invoice Date</th><td>{invoice_data.get('invoice_date', 'N/A')}</td></tr>
            <tr><th>Due Date</th><td>{invoice_data.get('due_date', 'N/A')}</td></tr>
            <tr><th>Total Amount</th><td>{invoice_data.get('invoice_amount', 'N/A')}</td></tr>
        </table>
    </div>

    <div>
        <h3>Line Items</h3>
        <table>
            <tr><th>Product Name</th><th>Description</th><th>Unit Price</th><th>Quantity</th><th>Total</th></tr>
    """
    
    # Loop through line items
    for line_item in invoice_data.get('line_items', []):
        html_content += f"""
            <tr>
                <td>{line_item.get('product_name', 'N/A')}</td>
                <td>{line_item.get('description', 'N/A')}</td>
                <td>{line_item.get('unit_price', '0.00')}</td>
                <td>{line_item.get('quantity', '0')}</td>
                <td>{line_item.get('total', '0.00')}</td>
            </tr>
        """

    # Add totals, tax, and discount sections
    html_content += f"""
        </table>
    </div>

    <div>
        <h3>Metadata</h3>
        <table>
            <tr><th>Subtotal</th><td>{invoice_data.get('subtotal', 'N/A')}</td></tr>
            <tr><th>Paid Amount</th><td>{invoice_data.get('paid_amount', 'N/A')}</td></tr>
            <tr><th>Balance</th><td>{invoice_data.get('balance', 'N/A')}</td></tr>
            <tr><th>Notes</th><td>{invoice_data.get('notes', 'N/A')}</td></tr>
        </table>
    </div>

    </body>
    </html>
    """
    return html_content

# Layout with two rows and two columns
if uploaded_invoice:
    # Get parser
    invoice_parser = JsonOutputParser(pydantic_object=InvoiceScreener)

    # Get prompt
    invoice_screener_prompt = PromptTemplate(
        template=Prompt_invoice,
        input_variables=["invoice"],
        partial_variables={"format_instructions": invoice_parser.get_format_instructions()}
    )

    # Get LLM 
    llm = llm_instance()

    # Create chain
    invoice_screener_chain = invoice_screener_prompt | llm | invoice_parser

    # Process invoices
    invoice_score_list = process_invoices(invoice_text, invoice_screener_chain)

    # First Row Layout (PDF and JSON)
    col1, col2 = st.columns([1, 1])

    with col1:
        st.write("### Invoice PDF Preview")
        with open(invoice_pdf_url, "rb") as pdf_file:
            PDFbyte = pdf_file.read()
            b64_pdf = base64.b64encode(PDFbyte).decode()
            pdf_display = f"""
            <iframe src="data:application/pdf;base64,{b64_pdf}" width="100%" height="600px" style="border: none;"></iframe> """ 
            st.markdown(pdf_display, unsafe_allow_html=True)
    
    with col2:
        st.write("### Extracted JSON Data")
        if invoice_score_list:
            # Get the first invoice's data
            json_data = invoice_score_list[0]  # Extract the first invoice
            
            # Convert the JSON to a formatted string
            json_str = json.dumps(json_data, indent=4)  # Convert JSON to a formatted string
            
            # Create a scrollable container for the JSON data
            st.markdown(
                '<div style="max-height: 600px; overflow-y: auto; border: 1px solid #ddd; padding: 10px; background-color: #f9f9f9; font-family: monospace; white-space: pre;">'
                f'{json_str}'
                '</div>', 
                unsafe_allow_html=True
            )

    # Second Row Layout (HTML code and Live Preview)
    col3, col4 = st.columns([1, 1])

    with col3:
        st.write("### Edit HTML Invoice")
        if invoice_score_list:
            invoice_data = invoice_score_list[0]
            html_content = generate_invoice_html(invoice_data)
            edited_html = st.text_area("Edit HTML", value=html_content, height=600)

    with col4:
        st.write("### Live Preview (Rendered Website View)")
        st.components.v1.html(edited_html, height=600, scrolling=True)

        if st.button("Download Edited HTML"):
            html_filename = f"{invoice_data.get('id', 'invoice')}.html"
            with open(html_filename, "w") as f:
                f.write(edited_html)
            with open(html_filename, "r") as f:
                st.download_button(
                    label="Download HTML Invoice",
                    data=f,
                    file_name=html_filename,
                    mime="text/html"
                )

