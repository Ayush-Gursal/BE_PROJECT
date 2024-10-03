# import os 
# import time 
# import pandas as pd
# from dotenv import load_dotenv
# load_dotenv()
# from PyPDF2 import PdfReader
# from docx import Document
# from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain_core.output_parsers import JsonOutputParser
# from langchain_core.prompts import PromptTemplate
# from langchain_core.pydantic_v1 import BaseModel, Field
# from tqdm import tqdm
# import streamlit as st

# # Create a folder to store uploaded invoices
# folder_invoice = "Uploaded_Invoices"
# if not os.path.exists(folder_invoice):
#     os.makedirs(folder_invoice)

# # File uploader for invoices
# uploaded_invoices = st.file_uploader(
#     "Upload Invoices (Multiple Selection Allowed)", 
#     type=["pdf"], 
#     accept_multiple_files=True
# )

# # Save uploaded files to the folder
# invoice_text = {}
# if uploaded_invoices:
#     for uploaded_file in uploaded_invoices:
#         file_name = uploaded_file.name
#         file_path = os.path.join(folder_invoice, file_name)
#         with open(file_path, "wb") as f:
#             f.write(uploaded_file.getbuffer())
        
#         # Parse the uploaded PDF file
#         reader = PdfReader(file_path)
#         text = ''
#         for page in reader.pages:
#             text += page.extract_text() + '\n'
#         invoice_text[file_name] = text
        
#         st.write(f"File '{file_name}' parsed successfully.")
# else:
#     st.write("No files uploaded.")

# # storing the API environment variable in api_key
# api_key = os.getenv("GOOGLE_API_KEY")

# # pydantic class for invoice processing
# class InvoiceScreener(BaseModel):
#     Invoice_Number: str = Field(description="Invoice Number")
#     Date: str = Field(description="Date of the invoice")
#     Customer_Details: str = Field(description="Details of the customer")
#     Itemized_Products: str = Field(description="List of products or services")
#     Total_Amount: str = Field(description="Total amount on the invoice")
#     Tax_Amount: str = Field(description="Tax amount on the invoice")
#     Discount: str = Field(description="Discount on the invoice")
#     Notes: str = Field(description="Any additional notes on the invoice")

# # Prompt for screening invoices ---------------------------------------
# Prompt_invoice = """
# Task: I want you to process invoices and extract key information such as invoice number, date, amount, customer details, and itemized services or products. This data will help in understanding invoice trends and monitoring financial records.

# Invoice:
# <invoice>
# {invoice}
# </invoice>

# {format_instructions}
# """

# # LLM Instantiation 
# def llm_instance():
#     return ChatGoogleGenerativeAI(
#         model="gemini-1.5-flash",
#         temperature=0,
#         max_tokens=None,
#         timeout=None,
#         max_retries=2,
#         use_auth_token=api_key
#     )

# # Processing the invoices using LLMs
# def process_invoices(invoice_text, invoice_screener_chain):
#     print("Invoice processing has begun:")
#     invoice_score_list = []
#     for name, invoice in tqdm(invoice_text.items()):
#         invoice_score = invoice_screener_chain.invoke({"invoice": invoice})
#         invoice_score_list.append(invoice_score)
#         time.sleep(5)
#     return invoice_score_list

# # Storing the results in CSV and displaying on Streamlit
# def store_results(invoice_score_list):
#     scores_df = pd.DataFrame(invoice_score_list)
#     scores_df.to_csv('invoice_data.csv', index=False)
#     st.success("Invoice processing is done! Results saved to 'invoice_data.csv'.")
#     st.dataframe(scores_df)

# # Pipeline execution 
# if uploaded_invoices:
#     # Get parser
#     invoice_parser = JsonOutputParser(pydantic_object=InvoiceScreener)

#     # Get prompt
#     invoice_screener_prompt = PromptTemplate(
#         template=Prompt_invoice,
#         input_variables=["invoice"],
#         partial_variables={"format_instructions": invoice_parser.get_format_instructions()}
#     )

#     # Get LLM 
#     llm = llm_instance()

#     # Create chain
#     invoice_screener_chain = invoice_screener_prompt | llm | invoice_parser

#     # Process invoices
#     invoice_score_list = process_invoices(invoice_text, invoice_screener_chain)

#     # Store results
#     store_results(invoice_score_list)
import os
import time
import pandas as pd
from dotenv import load_dotenv
load_dotenv()
import fitz  # PyMuPDF for PDF handling
from docx import Document
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from tqdm import tqdm
import streamlit as st

# Set full screen mode for better visibility
st.set_page_config(layout="wide")

# Create a folder to store uploaded invoices
folder_invoice = "Uploaded_Invoices"
if not os.path.exists(folder_invoice):
    os.makedirs(folder_invoice)

# File uploader for invoices
uploaded_invoices = st.file_uploader(
    "Upload Invoices (Multiple Selection Allowed)", 
    type=["pdf"], 
    accept_multiple_files=True
)

# Save uploaded files to the folder and display the first page
invoice_text = {}
if uploaded_invoices:
    for uploaded_file in uploaded_invoices:
        file_name = uploaded_file.name
        file_path = os.path.join(folder_invoice, file_name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Parse the uploaded PDF file
        reader = fitz.open(file_path)
        text = ''
        for page_num in range(len(reader)):
            page = reader[page_num]
            text += page.get_text() + '\n'
        invoice_text[file_name] = text
        
        st.write(f"File '{file_name}' parsed successfully.")
else:
    st.write("No files uploaded.")

# storing the API environment variable in api_key
api_key = os.getenv("GOOGLE_API_KEY")

# pydantic class for invoice processing
class InvoiceScreener(BaseModel):
    Invoice_Number: str = Field(description="Invoice Number")
    Date: str = Field(description="Date of the invoice")
    Customer_Details: str = Field(description="Details of the customer")
    Itemized_Products: str = Field(description="List of products or services")
    Total_Amount: str = Field(description="Total amount on the invoice")
    Tax_Amount: str = Field(description="Tax amount on the invoice")
    Discount: str = Field(description="Discount on the invoice")
    Notes: str = Field(description="Any additional notes on the invoice")

# Prompt for screening invoices ---------------------------------------
Prompt_invoice = """
Task: I want you to process invoices and extract key information such as invoice number, date, amount, customer details, and itemized services or products. This data will help in understanding invoice trends and monitoring financial records.

Invoice:
<invoice>
{invoice}
</invoice>

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

# Processing the invoices using LLMs
def process_invoices(invoice_text, invoice_screener_chain):
    st.write("Invoice processing has begun:")
    invoice_score_list = []
    for name, invoice in tqdm(invoice_text.items()):
        invoice_score = invoice_screener_chain.invoke({"invoice": invoice})
        invoice_score_list.append(invoice_score)
        time.sleep(5)
    return invoice_score_list

# Storing the results and returning DataFrame
def store_results(invoice_score_list):
    scores_df = pd.DataFrame(invoice_score_list)
    scores_df.to_csv('invoice_data.csv', index=False)
    st.success("Invoice processing is done! Results saved to 'invoice_data.csv'.")
    return scores_df

# Function to display the first page of the PDF as an image using PyMuPDF
def display_pdf_page_as_image(file_path):
    doc = fitz.open(file_path)
    first_page = doc.load_page(0)  # Load the first page
    pix = first_page.get_pixmap()  # Render page as an image
    img_path = f"{file_path}_first_page.png"
    pix.save(img_path)
    return img_path

# Layout with two columns (left: PDF preview, right: extracted info)
if uploaded_invoices:
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

    # Streamlit layout for displaying PDF and extracted information
    col1, col2 = st.columns([1, 1])  # Adjust width proportions here

    # Left column: Display first page of uploaded PDF as image
    with col1:
        st.write("### First Page Preview")
        for uploaded_file in uploaded_invoices:
            file_path = os.path.join(folder_invoice, uploaded_file.name)
            img_path = display_pdf_page_as_image(file_path)
            st.image(img_path, width=600)  # Increase the width for better visibility

    # Right column: Display extracted table
    with col2:
        st.write("### Extracted Invoice Information")
        # Display the final table (one table only)
        final_scores_df = store_results(invoice_score_list)
        st.dataframe(final_scores_df, height=600)  # Scrollable table for large data
