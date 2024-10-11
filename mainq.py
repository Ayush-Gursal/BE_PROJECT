import os
import time
import json
import fitz  # PyMuPDF for PDF handling
from dotenv import load_dotenv
load_dotenv()
import streamlit as st
import base64
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field

# Set full screen mode for better visibility
st.set_page_config(layout="wide")

# Create a folder to store uploaded quotes
folder_quote = "Uploaded_Quotes"
if not os.path.exists(folder_quote):
    os.makedirs(folder_quote)

# File uploader for a single quote PDF
uploaded_quote = st.file_uploader(
    "Upload Quote", 
    type=["pdf"], 
    accept_multiple_files=False  # Only allow one file upload
)

# Initialize variables
quote_text = None
quote_pdf_url = None

if uploaded_quote:
    # Get the file name and path
    file_name = uploaded_quote.name
    file_path = os.path.join(folder_quote, file_name)
    
    # Save the uploaded PDF file
    with open(file_path, "wb") as f:
        f.write(uploaded_quote.getbuffer())
    
    # Parse the uploaded PDF file to extract text
    reader = fitz.open(file_path)
    text = ''
    for page_num in range(len(reader)):
        page = reader[page_num]
        text += page.get_text() + '\n'
    
    # Store extracted text and PDF path
    quote_text = text
    quote_pdf_url = file_path  # Store the path to the uploaded PDF
    
    st.write(f"File '{file_name}' parsed successfully.")

# API Key
api_key = os.getenv("GOOGLE_API_KEY")

class QuoteScreener(BaseModel):
    id: str
    customer_id: str
    customer_name: str
    status: str
    billing_start_date: str
    service_start_date: str
    quote_placed_at: str
    quote_expiry_at: str
    accepted_at: str
    contract_effective_date: str
    cancellation_date: str
    auto_renew: bool
    currency: str
    total_charges: str
    separate_invoice: bool
    notes: str
    require_payment_method: bool
    version: int
    version_type: str
    contract_term: str
    sender_name: str
    sender_email: str
    recipient_name: str
    recipient_email: str
    quote_pdf_url: str
    plans: list
    created_date: str
    updated_date: str
    created_by: str
    created_by_name: str
    updated_by: str
    customer_text_signature: str
    company_text_signature: str
    company_sign_at: str
    subscription_number: str

# Prompt for screening quotes ---------------------------------------
Prompt_quote = """
Task: Process the following quote and extract detailed information into structured fields. Please include all relevant details such as:

- Quote ID
- Customer ID
- Customer Name
- Status
- Billing Start Date
- Service Start Date
- Quote Placed At
- Quote Expiry At
- Total Charges
- Currency
- Notes
- Plans (product name, plan name, unit price, quantity, total)

Quote:
<quote>
{quote}
</quote>

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

def process_quotes(quote_text, quote_screener_chain):
    st.write("Quote processing has begun:")
    quote_score_list = []
    
    try:
        # Process the entire quote text as a string
        quote_score = quote_screener_chain.invoke({"quote": quote_text})
        
        # Check if quote_score is already a dict
        if isinstance(quote_score, dict):
            quote_score_list.append(quote_score)
        else:
            # If it's a string (JSON), parse it
            quote_data = json.loads(quote_score)
            quote_score_list.append(quote_data)
    except Exception as e:
        st.error(f"Error processing quote: {str(e)}")
    
    return quote_score_list

def generate_quote_html(quote_data):
    html_content = """
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                max-width: 1000px;
                margin: auto;
                padding: 20px;
            }}
            h2, h3 {{
                text-align: center;
                margin-bottom: 20px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 20px;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 10px;
                text-align: left;
            }}
            th {{
                background-color: #f2f2f2;
            }}
            .quote-header {{
                margin-bottom: 30px;
                text-align: center;
            }}
            .quote-section {{
                margin-bottom: 20px;
            }}
            .quote-details td, .quote-details th {{
                border: none;
                padding: 5px;
            }}
            .plans th, .plans td {{
                border: 1px solid #ddd;
            }}
            .metadata-section {{
                margin-top: 20px;
            }}
        </style>
    </head>
    <body>

        <h2 class="quote-header">Quote Details</h2>

        <!-- Quote Information -->
        <div class="quote-section">
            <h3>General Information</h3>
            <table class="quote-details">
                <tr><th>Quote ID</th><td>{id}</td></tr>
                <tr><th>Customer Name</th><td>{customer_name}</td></tr>
                <tr><th>Status</th><td>{status}</td></tr>
                <tr><th>Billing Start Date</th><td>{billing_start_date}</td></tr>
                <tr><th>Service Start Date</th><td>{service_start_date}</td></tr>
                <tr><th>Quote Placed At</th><td>{quote_placed_at}</td></tr>
                <tr><th>Quote Expiry At</th><td>{quote_expiry_at}</td></tr>
                <tr><th>Total Charges</th><td>{total_charges}</td></tr>
                <tr><th>Currency</th><td>{currency}</td></tr>
                <tr><th>Notes</th><td>{notes}</td></tr>
            </table>
        </div>

        <!-- Plans Section -->
        <div class="quote-section">
            <h3>Plans</h3>
            <table class="plans">
                <tr>
                    <th>Product ID</th>
                    <th>Product Name</th>
                    <th>Plan ID</th>
                    <th>Plan Name</th>
                    <th>Pricing Model</th>
                    <th>List Price</th>
                    <th>Quantity</th>
                </tr>
    """
    
    # Loop through plans
    for plan in quote_data.get('plans', []):
        html_content += f"""
            <tr>
                <td>{plan.get('product_id', 'N/A')}</td>
                <td>{plan.get('product_name', 'N/A')}</td>
                <td>{plan.get('plan_id', 'N/A')}</td>
                <td>{plan.get('plan_name', 'N/A')}</td>
                <td>{plan.get('pricing_model', 'N/A')}</td>
                <td>{plan.get('list_price', '0.00')}</td>
                <td>{plan.get('quantity', '0')}</td>
            </tr>
        """

    # Add Metadata Section
    html_content += """
            </table>
        </div>

        <!-- Metadata Section -->
        <div class="quote-section metadata-section">
            <h3>Metadata</h3>
            <table class="metadata">
                <tr><th>Sender Name</th><td>{sender_name}</td></tr>
                <tr><th>Sender Email</th><td>{sender_email}</td></tr>
                <tr><th>Recipient Name</th><td>{recipient_name}</td></tr>
                <tr><th>Recipient Email</th><td>{recipient_email}</td></tr>
                <tr><th>Created By</th><td>{created_by_name}</td></tr>
                <tr><th>Updated By</th><td>{updated_by}</td></tr>
                <tr><th>Created At</th><td>{created_date}</td></tr>
                <tr><th>Updated At</th><td>{updated_date}</td></tr>
            </table>
        </div>

    </body>
    </html>
    """
    # Format the HTML with quote_data
    return html_content.format(
        id=quote_data.get('id', 'N/A'),
        customer_name=quote_data.get('customer_name', 'N/A'),
        status=quote_data.get('status', 'N/A'),
        billing_start_date=quote_data.get('billing_start_date', 'N/A'),
        service_start_date=quote_data.get('service_start_date', 'N/A'),
        quote_placed_at=quote_data.get('quote_placed_at', 'N/A'),
        quote_expiry_at=quote_data.get('quote_expiry_at', 'N/A'),
        total_charges=quote_data.get('total_charges', 'N/A'),
        currency=quote_data.get('currency', 'N/A'),
        notes=quote_data.get('notes', 'N/A'),
        sender_name=quote_data.get('sender_name', 'N/A'),
        sender_email=quote_data.get('sender_email', 'N/A'),
        recipient_name=quote_data.get('recipient_name', 'N/A'),
        recipient_email=quote_data.get('recipient_email', 'N/A'),
        created_by_name=quote_data.get('created_by_name', 'N/A'),
        updated_by=quote_data.get('updated_by', 'N/A'),
        created_date=quote_data.get('created_date', 'N/A'),
        updated_date=quote_data.get('updated_date', 'N/A')
    )

# Layout with two rows and two columns
if uploaded_quote:
    # Get parser
    quote_parser = JsonOutputParser(pydantic_object=QuoteScreener)

    # Get prompt
    quote_screener_prompt = PromptTemplate(
        template=Prompt_quote,
        input_variables=["quote"],
        partial_variables={"format_instructions": quote_parser.get_format_instructions()}
    )

    # Get LLM 
    llm = llm_instance()

    # Create chain
    quote_screener_chain = quote_screener_prompt | llm | quote_parser

    # Process quotes
    quote_score_list = process_quotes(quote_text, quote_screener_chain)

    # First Row Layout (PDF and JSON)
    col1, col2 = st.columns([1, 1])  # Adjust width proportions here

    with col1:
        st.write("### Quote PDF Preview")
        
        # Render the PDF as a base64 string
        with open(quote_pdf_url, "rb") as pdf_file:
            PDFbyte = pdf_file.read()
            b64_pdf = base64.b64encode(PDFbyte).decode()  # Encode PDF as base64 string
            pdf_display = f"""
            <iframe src="data:application/pdf;base64,{b64_pdf}" 
                    width="100%" height="800px" style="border: none;"></iframe>
            """
        
        st.markdown(pdf_display, unsafe_allow_html=True)  # Display the PDF in an iframe

   # Right column: Display extracted JSON data
    with col2:
        st.write("### Extracted JSON Data")
        if quote_score_list:
            # Display the first quote's data in a scrollable container
            json_data = json.dumps(quote_score_list[0], indent=2)  # Format JSON for better readability
            
            st.markdown(f"""
            <div style='height: 800px; overflow-y: scroll; border: 1px solid #ddd; padding: 10px; background-color: #f9f9f9; font-family: monospace; white-space: pre;'>
                {json_data}
            </div>
            """, unsafe_allow_html=True)

    # Second Row Layout (HTML code and Live Preview)
    col3, col4 = st.columns([1, 1])  # Adjust width proportions here

    # Left column: Display editable HTML quote
    with col3:
        st.write("### Edit HTML Quote")
        if quote_score_list:
            # Use the first quote data for display
            quote_data = quote_score_list[0]
            html_content = generate_quote_html(quote_data)
            
            # Editable HTML code
            edited_html = st.text_area("Edit HTML", value=html_content, height=800)

    # Right column: Display rendered HTML view
    with col4:
        st.write("### Live Preview (Rendered Website View)")
        st.components.v1.html(edited_html, height=800, scrolling=True)

        # Download button for the edited HTML
        if st.button("Download Edited HTML"):
            html_filename = f"{quote_data.get('id', 'quote')}_edited.html"
            with open(html_filename, "w") as f:
                f.write(edited_html)
            
            # Provide a download link
            with open(html_filename, "r") as f:
                st.download_button(
                    label="Download HTML Quote",
                    data=f,
                    file_name=html_filename,
                    mime="text/html"
                )
