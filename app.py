import os
import time
import pandas as pd
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from google.cloud import language_v1
print(language_v1.__file__)
from google.api_core.client_options import ClientOptions
from pydantic import BaseModel, Field
from tqdm import tqdm
import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field+
# Load environment variables
load_dotenv()

# Streamlit UI
st.title("Invoice Information Extractor")

# Get API key from environment variable
api_key = os.getenv('GOOGLE_API_KEY')

if not api_key:
    st.error("Google Cloud API key not found. Please check your .env file.")
    st.stop()

# Initialize Google client with API key
# try:
#     client_options = ClientOptions(api_key=api_key)
#     client = language_v1.LanguageServiceClient(client_options=client_options)
#     st.success("Successfully connected to Google Cloud API")
# except Exception as e:
#     st.error(f"Failed to initialize Google Cloud client: {str(e)}")
#     st.error("Make sure your API key is correct and the Cloud Natural Language API is enabled.")
#     st.stop()

# Create folder for uploaded invoices
folder_invoice = "Uploaded_Invoices"
if not os.path.exists(folder_invoice):
    os.makedirs(folder_invoice)

# File uploader
uploaded_invoices = st.file_uploader(
    "Upload Invoice PDFs (Multiple Selection Allowed)", 
    type=["pdf"], 
    accept_multiple_files=True
)

# Pydantic model for invoice details
class InvoiceScreener(BaseModel):
    Invoice_Number: str = Field(description="Invoice Number")
    Date: str = Field(description="Date of the invoice")
    Customer_Details: str = Field(description="Customer details")
    Itemized_Products: str = Field(description="Products/Services")
    Total_Amount: str = Field(description="Total Amount")
    Tax_Amount: str = Field(description="Tax Amount")
    Discount: str = Field(description="Discount")
    Notes: str = Field(description="Additional Notes")

def process_pdf(uploaded_file):
    try:
        # Save the uploaded file
        file_path = os.path.join(folder_invoice, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Parse the PDF
        reader = PdfReader(file_path)
        text = ' '.join([page.extract_text() for page in reader.pages])
        return text
    except Exception as e:
        st.error(f"Error processing PDF {uploaded_file.name}: {str(e)}")
        return None

def analyze_text(text):
    try:
        document = language_v1.Document(
            content=text,
            type_=language_v1.Document.Type.PLAIN_TEXT
        )
        
        # Analyze entities
        response = client.analyze_entities(
            request={
                "document": document,
                "encoding_type": language_v1.EncodingType.UTF8
            }
        )
        return response.entities
    except Exception as e:
        st.error(f"Error analyzing text: {str(e)}")
        return None

def process_entities(entities):
    invoice_data = {
        "Invoice_Number": "",
        "Date": "",
        "Customer_Details": "",
        "Itemized_Products": [],
        "Total_Amount": "",
        "Tax_Amount": "",
        "Discount": "",
        "Notes": ""
    }
    
    for entity in entities:
        # Process each entity based on its type
        if entity.type_ == language_v1.Entity.Type.NUMBER:
            if any(keyword in entity.mentions[0].text.content.lower() 
                  for keyword in ["invoice", "inv", "#"]):
                invoice_data["Invoice_Number"] = entity.mentions[0].text.content
        elif entity.type_ == language_v1.Entity.Type.DATE:
            if not invoice_data["Date"]:  # Take the first date found
                invoice_data["Date"] = entity.mentions[0].text.content
        elif entity.type_ == language_v1.Entity.Type.PRICE:
            amount = entity.mentions[0].text.content
            if "total" in entity.mentions[0].text.content.lower():
                invoice_data["Total_Amount"] = amount
            elif "tax" in entity.mentions[0].text.content.lower():
                invoice_data["Tax_Amount"] = amount
    
    return invoice_data

def process_invoices(uploaded_files):
    results = []
    progress_bar = st.progress(0)
    
    for i, uploaded_file in enumerate(uploaded_files):
        st.write(f"Processing {uploaded_file.name}...")
        
        # Extract text from PDF
        text = process_pdf(uploaded_file)
        if text is None:
            continue
        
        # Analyze text
        entities = analyze_text(text)
        if entities is None:
            continue
        
        # Process entities into structured data
        invoice_data = process_entities(entities)
        results.append(invoice_data)
        
        # Update progress
        progress = (i + 1) / len(uploaded_files)
        progress_bar.progress(progress)
        
    return results

def save_results(results):
    if not results:
        st.warning("No results to save.")
        return
    
    try:
        df = pd.DataFrame(results)
        csv_file = 'invoice_results.csv'
        df.to_csv(csv_file, index=False)
        st.success(f"Results saved to {csv_file}")
        st.dataframe(df)
        
        # Offer download button
        with open(csv_file, 'rb') as f:
            st.download_button(
                label="Download Results CSV",
                data=f,
                file_name=csv_file,
                mime="text/csv"
            )
    except Exception as e:
        st.error(f"Error saving results: {str(e)}")

# Main execution
if uploaded_invoices:
    st.write(f"Processing {len(uploaded_invoices)} invoices...")
    
    results = process_invoices(uploaded_invoices)
    
    if results:
        save_results(results)
else:
    st.write("Please upload some invoice PDFs to process.")

# Cleanup
for filename in os.listdir(folder_invoice):
    file_path = os.path.join(folder_invoice, filename)
    try:
        os.remove(file_path)
    except Exception as e:
        st.warning(f"Error removing temporary file {filename}: {str(e)}")