# import os
# import fitz  # PyMuPDF for PDF handling
# import json
# from dotenv import load_dotenv
# from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain_core.prompts import PromptTemplate
# import streamlit as st
# import html

# # Load environment variables
# load_dotenv()

# # Streamlit setup for UI
# st.set_page_config(layout="wide")

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

# # Save uploaded files to the folder and parse the first page
# invoice_text = {}
# if uploaded_invoices:
#     for uploaded_file in uploaded_invoices:
#         file_name = uploaded_file.name
#         file_path = os.path.join(folder_invoice, file_name)
#         with open(file_path, "wb") as f:
#             f.write(uploaded_file.getbuffer())

#         # Parse the uploaded PDF file using fitz
#         reader = fitz.open(file_path)
#         text = ''
#         for page_num in range(len(reader)):
#             page = reader[page_num]
#             text += page.get_text() + '\n'
#         invoice_text[file_name] = text

#         st.write(f"File '{file_name}' parsed successfully.")
# else:
#     st.write("No files uploaded.")

# # Set the API key from the .env file
# api_key = os.getenv("GOOGLE_API_KEY")

# # Define the fields we want to extract
# fields = [
#     "id", "customer_id", "customer_name", "status", "billing_start_date",
#     "service_start_date", "quote_placed_at", "quote_expiry_at", "accepted_at",
#     "contract_effective_date", "cancellation_date", "auto_renew", "currency",
#     "total_charges", "separate_invoice", "notes", "require_payment_method",
#     "version", "version_type", "contract_term", "sender_name", "sender_email",
#     "recipient_name", "recipient_email", "quote_pdf_url", "plans", "created_date",
#     "updated_date", "created_by", "created_by_name", "updated_by",
#     "customer_text_signature", "company_text_signature", "company_sign_at",
#     "subscription_number"
# ]

# # Enhanced Prompt for screening invoices
# Prompt_invoice = PromptTemplate(
#     template="""Extract the following information from the invoice. If a field is not present, write 'N/A'. Format the output as a valid JSON object with the following keys:

# {fields}

# For the 'plans' field, extract all relevant plan information including name, description, price, and quantity as a list of objects.

# Important: 
# 1. Ensure the output is a properly formatted JSON object.
# 2. All string values must be enclosed in double quotes.
# 3. Use valid JSON data types (strings, numbers, booleans, null, arrays, objects).
# 4. Do not include any explanatory text before or after the JSON object.
# 5. If a field is not found, use "N/A" (with quotes) for string fields, or null for other types.

# Invoice:
# {invoice}

# JSON output:""",
#     input_variables=["invoice"],
#     partial_variables={"fields": ", ".join(fields)}
# )

# # LLM Instantiation
# def llm_instance():
#     return ChatGoogleGenerativeAI(
#         model="gemini-1.0-pro",
#         temperature=0,
#         max_output_tokens=2048,
#         top_p=1,
#         top_k=1,
#         use_auth_token=api_key
#     )

# # Enhanced JSON parser with debugging
# def parse_json(text):
#     try:
#         # Remove any leading/trailing whitespace
#         text = text.strip()
        
#         # If the text starts with a backtick code block, remove it
#         if text.startswith("```json"):
#             text = text[7:]
#         if text.startswith("```"):
#             text = text[3:]
#         if text.endswith("```"):
#             text = text[:-3]
        
#         # Remove any remaining leading/trailing whitespace
#         text = text.strip()
        
#         return json.loads(text)
#     except json.JSONDecodeError as e:
#         st.error(f"JSON parsing error: {str(e)}")
#         st.text("Raw content received:")
#         st.code(text)  # Display the raw text that couldn't be parsed
#         return None

# def generate_editable_html(json_data):
#     html_content = """
#     <!DOCTYPE html>
#     <html>
#     <head>
#         <style>
#             body { font-family: Arial, sans-serif; line-height: 1.6; }
#             .container { max-width: 800px; margin: 0 auto; padding: 20px; }
#             .field { margin-bottom: 15px; }
#             label { display: block; font-weight: bold; margin-bottom: 5px; }
#             input, textarea { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
#             .plans-container { border: 1px solid #ddd; padding: 10px; margin-bottom: 10px; }
#             .plan { background-color: #f5f5f5; padding: 10px; margin-bottom: 10px; }
#             button { background-color: #4CAF50; color: white; padding: 10px 15px; border: none; 
#                      border-radius: 4px; cursor: pointer; }
#             button:hover { background-color: #45a049; }
#             #jsonOutput { width: 100%; height: 200px; font-family: monospace; }
#         </style>
#     </head>
#     <body>
#         <div class="container">
#             <form id="invoiceForm" onsubmit="return false;">
#     """
    
#     # Add fields dynamically based on the JSON data
#     for field, value in json_data.items():
#         if field != 'plans':
#             html_content += f"""
#                 <div class="field">
#                     <label for="{field}">{field.replace('_', ' ').title()}:</label>
#                     <input type="text" id="{field}" data-field="{field}" 
#                            value="{html.escape(str(value))}" onchange="updateJSON()">
#                 </div>
#             """
    
#     # Add plans section
#     html_content += """
#                 <div class="field">
#                     <label>Plans:</label>
#                     <div id="plansContainer">
#     """
    
#     if 'plans' in json_data and json_data['plans']:
#         for plan in json_data['plans']:
#             html_content += f"""
#                 <div class="plan">
#                     <input type="text" data-plan-field="name" placeholder="Plan Name" 
#                            value="{html.escape(str(plan.get('name', '')))}" onchange="updateJSON()">
#                     <input type="text" data-plan-field="description" placeholder="Description" 
#                            value="{html.escape(str(plan.get('description', '')))}" onchange="updateJSON()">
#                     <input type="number" data-plan-field="price" placeholder="Price" 
#                            value="{html.escape(str(plan.get('price', '')))}" onchange="updateJSON()">
#                     <input type="number" data-plan-field="quantity" placeholder="Quantity" 
#                            value="{html.escape(str(plan.get('quantity', '')))}" onchange="updateJSON()">
#                 </div>
#             """
    
#     html_content += """
#                     </div>
#                     <button type="button" onclick="addPlan()">Add Plan</button>
#                 </div>
                
#                 <div class="field">
#                     <label for="jsonOutput">JSON Output:</label>
#                     <textarea id="jsonOutput" readonly></textarea>
#                 </div>
#             </form>
#         </div>
#         <script>
#             function updateJSON() {
#                 let result = {};
#                 document.querySelectorAll('[data-field]').forEach(input => {
#                     let fieldName = input.getAttribute('data-field');
#                     if (fieldName !== 'plans') {
#                         result[fieldName] = input.value || "N/A";
#                     }
#                 });
                
#                 let plans = [];
#                 document.querySelectorAll('.plan').forEach(planDiv => {
#                     let plan = {};
#                     planDiv.querySelectorAll('[data-plan-field]').forEach(input => {
#                         let fieldName = input.getAttribute('data-plan-field');
#                         plan[fieldName] = input.value || "N/A";
#                     });
#                     plans.push(plan);
#                 });
#                 result.plans = plans;
                
#                 document.getElementById('jsonOutput').value = JSON.stringify(result, null, 2);
#             }
            
#             function addPlan() {
#                 const plansContainer = document.getElementById('plansContainer');
#                 const newPlan = document.createElement('div');
#                 newPlan.className = 'plan';
#                 newPlan.innerHTML = `
#                     <input type="text" data-plan-field="name" placeholder="Plan Name" onchange="updateJSON()">
#                     <input type="text" data-plan-field="description" placeholder="Description" onchange="updateJSON()">
#                     <input type="number" data-plan-field="price" placeholder="Price" onchange="updateJSON()">
#                     <input type="number" data-plan-field="quantity" placeholder="Quantity" onchange="updateJSON()">
#                 `;
#                 plansContainer.appendChild(newPlan);
#                 updateJSON();
#             }
            
#             // Initialize JSON output
#             updateJSON();
#         </script>
#     </body>
#     </html>
#     """
#     return html_content

# # Process invoices using LangChain and output structured JSON
# def process_invoices(invoice_text, invoice_screener_chain):
#     st.write("Processing invoices...")
#     invoice_results = []
#     for name, invoice in invoice_text.items():
#         try:
#             st.write(f"Processing invoice: {name}")
#             result = invoice_screener_chain.invoke({"invoice": invoice})
#             result_content = result.content if hasattr(result, 'content') else str(result)
            
#             # Display raw result for debugging
#             st.write("Raw result from model:")
#             st.code(result_content)
            
#             parsed_result = parse_json(result_content)
#             if parsed_result:
#                 invoice_results.append(parsed_result)
#                 st.success(f"Successfully parsed JSON for invoice {name}")
#             else:
#                 st.error(f"Failed to parse JSON for invoice {name}")
#         except Exception as e:
#             st.error(f"Error processing invoice {name}: {str(e)}")
#     return invoice_results

# # Main execution
# if uploaded_invoices:
#     # Instantiate the LLM
#     llm = llm_instance()

#     # Create a LangChain chain for processing
#     invoice_screener_chain = Prompt_invoice | llm

#     # Process and extract the invoices
#     extracted_invoice_data = process_invoices(invoice_text, invoice_screener_chain)

#     # Display the extracted data
#     if extracted_invoice_data:
#         for idx, data in enumerate(extracted_invoice_data):
#             st.write(f"### Invoice {idx + 1}")
            
#             # Generate and display editable HTML interface
#             html_content = generate_editable_html(data)
#             st.components.v1.html(html_content, height=800, scrolling=True)
            
#         # Save the original JSON to a file
#         with open('extracted_invoice_data.json', 'w') as json_file:
#             json.dump(extracted_invoice_data, json_file, indent=4)
#         st.success("Original invoice data saved as 'extracted_invoice_data.json'.")
#     else:
#         st.warning("No valid data was extracted from the invoices.")

import os
import fitz  # PyMuPDF for PDF handling
import json
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
import streamlit as st
import html

# Load environment variables
load_dotenv()

# Streamlit setup for UI
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

# Save uploaded files to the folder and parse the first page
invoice_text = {}
if uploaded_invoices:
    for uploaded_file in uploaded_invoices:
        file_name = uploaded_file.name
        file_path = os.path.join(folder_invoice, file_name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Parse the uploaded PDF file using fitz
        reader = fitz.open(file_path)
        text = ''
        for page_num in range(len(reader)):
            page = reader[page_num]
            text += page.get_text() + '\n'
        invoice_text[file_name] = text

        st.write(f"File '{file_name}' parsed successfully.")
else:
    st.write("No files uploaded.")

# Set the API key from the .env file
api_key = os.getenv("GOOGLE_API_KEY")

# Define the fields we want to extract
fields = [
    "id", "customer_id", "customer_name", "status", "billing_start_date",
    "service_start_date", "quote_placed_at", "quote_expiry_at", "accepted_at",
    "contract_effective_date", "cancellation_date", "auto_renew", "currency",
    "total_charges", "separate_invoice", "notes", "require_payment_method",
    "version", "version_type", "contract_term", "sender_name", "sender_email",
    "recipient_name", "recipient_email", "quote_pdf_url", "plans", "created_date",
    "updated_date", "created_by", "created_by_name", "updated_by",
    "customer_text_signature", "company_text_signature", "company_sign_at",
    "subscription_number"
]

# Enhanced Prompt for screening invoices
Prompt_invoice = PromptTemplate(
    template="""Extract the following information from the invoice. If a field is not present, write 'N/A'. Format the output as a valid JSON object with the following keys:

{fields}

For the 'plans' field, extract all relevant plan information including name, description, price, and quantity as a list of objects.

Important: 
1. Ensure the output is a properly formatted JSON object.
2. All string values must be enclosed in double quotes.
3. Use valid JSON data types (strings, numbers, booleans, null, arrays, objects).
4. Do not include any explanatory text before or after the JSON object.
5. If a field is not found, use "N/A" (with quotes) for string fields, or null for other types.

Invoice:
{invoice}

JSON output:""",
    input_variables=["invoice"],
    partial_variables={"fields": ", ".join(fields)}
)

# LLM Instantiation
def llm_instance():
    return ChatGoogleGenerativeAI(
        model="gemini-1.0-pro",
        temperature=0,
        max_output_tokens=2048,
        top_p=1,
        top_k=1,
        use_auth_token=api_key
    )

# Enhanced JSON parser with debugging
def parse_json(text):
    try:
        # Remove any leading/trailing whitespace
        text = text.strip()
        
        # If the text starts with a backtick code block, remove it
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        
        # Remove any remaining leading/trailing whitespace
        text = text.strip()
        
        return json.loads(text)
    except json.JSONDecodeError as e:
        st.error(f"JSON parsing error: {str(e)}")
        st.text("Raw content received:")
        st.code(text)  # Display the raw text that couldn't be parsed
        return None

# Editable form interface using Streamlit's input widgets
def display_editable_invoice_form(json_data):
    st.write("### Editable FusionAuth Order Form")
    
    # Customer Information
    st.subheader("Customer (Licensee) Information")
    company_name = st.text_input("Company Name", value=json_data.get('customer_name', 'N/A'))
    contact_name = st.text_input("Primary Contact", value=json_data.get('recipient_name', 'N/A'))
    address = st.text_area("Address", value=json_data.get('customer_address', 'N/A'))
    email = st.text_input("Email Address", value=json_data.get('recipient_email', 'N/A'))
    phone = st.text_input("Phone Number", value=json_data.get('recipient_phone', 'N/A'))
    
    # General Information
    st.subheader("General Information")
    billing_cycle = st.text_input("Billing Cycle", value="Annual upon signature; anniversary date thereafter")
    usage_above_minimum = st.text_input("Usage Above Minimum", value="$350 per 10k MAU")
    payment_terms = st.text_input("Payment Terms", value="Net 30")
    payment_method = st.text_input("Payment Method", value=json_data.get('payment_method', 'check/ACH payment'))

    # Order Information
    st.subheader("Order Information")
    for idx, plan in enumerate(json_data.get('plans', [])):
        st.text(f"Plan {idx + 1}")
        name = st.text_input(f"Plan {idx + 1} Name", value=plan.get('name', 'N/A'), key=f"plan_name_{idx}")
        description = st.text_area(f"Plan {idx + 1} Description", value=plan.get('description', 'N/A'), key=f"plan_desc_{idx}")
        quantity = st.number_input(f"Plan {idx + 1} Quantity", value=int(plan.get('quantity', 0)), key=f"plan_qty_{idx}")
        price = st.number_input(f"Plan {idx + 1} Price", value=float(plan.get('price', 0)), key=f"plan_price_{idx}")
    
    # Additional Terms
    st.subheader("Additional Terms")
    system_access = st.text_input("System Access", value="Licensee will receive access to services by 5/1/2024.")
    renewal_terms = st.text_input("Renewal Terms", value="The Initial Term will automatically renew unless either party provides 30 days' notice.")
    
    # Signatures
    st.subheader("Signatures")
    signer_name = st.text_input("Inversoft Signer Name", value="Mark van Oppen")
    signer_date = st.text_input("Inversoft Signer Date", value="4/17/2024")
    customer_name = st.text_input("Customer Signer Name", value="Phil Hewitt")
    customer_date = st.text_input("Customer Signer Date", value="4/24/2024")

    # Update the JSON with the new values
    updated_data = {
        "customer_name": company_name,
        "recipient_name": contact_name,
        "customer_address": address,
        "recipient_email": email,
        "recipient_phone": phone,
        "payment_method": payment_method,
        "plans": [
            {
                "name": st.session_state.get(f"plan_name_{idx}", plan.get('name')),
                "description": st.session_state.get(f"plan_desc_{idx}", plan.get('description')),
                "quantity": st.session_state.get(f"plan_qty_{idx}", plan.get('quantity')),
                "price": st.session_state.get(f"plan_price_{idx}", plan.get('price')),
            } for idx, plan in enumerate(json_data.get('plans', []))
        ],
        "system_access": system_access,
        "renewal_terms": renewal_terms,
        "signatures": {
            "inversoft_signer_name": signer_name,
            "inversoft_signer_date": signer_date,
            "customer_signer_name": customer_name,
            "customer_signer_date": customer_date
        }
    }
    
    # Display the updated JSON for preview or download
    st.subheader("Updated JSON Output")
    st.json(updated_data)
    
    # Provide download option for the updated JSON
    st.download_button(
        label="Download Updated JSON",
        data=json.dumps(updated_data, indent=4),
        file_name='updated_invoice_data.json'
    )

# Process invoices using LangChain and output editable structured form
def process_invoices(invoice_text, invoice_screener_chain):
    st.write("Processing invoices...")
    invoice_results = []
    for name, invoice in invoice_text.items():
        try:
            st.write(f"Processing invoice: {name}")
            result = invoice_screener_chain.invoke({"invoice": invoice})
            result_content = result.content if hasattr(result, 'content') else str(result)
            
            # Display raw result for debugging
            st.write("Raw result from model:")
            st.code(result_content)
            
            parsed_result = parse_json(result_content)
            if parsed_result:
                invoice_results.append(parsed_result)
                st.success(f"Successfully parsed JSON for invoice {name}")
                
                # Display the editable form
                display_editable_invoice_form(parsed_result)
                
            else:
                st.error(f"Failed to parse JSON for invoice {name}")
        except Exception as e:
            st.error(f"Error processing invoice {name}: {str(e)}")
    return invoice_results

# Main execution
if uploaded_invoices:
    # Instantiate the LLM
    llm = llm_instance()

    # Create a LangChain chain for processing
    invoice_screener_chain = Prompt_invoice | llm

    # Process and extract the invoices
    extracted_invoice_data = process_invoices(invoice_text, invoice_screener_chain)

    # Save the original JSON to a file
    if extracted_invoice_data:
        with open('extracted_invoice_data.json', 'w') as json_file:
            json.dump(extracted_invoice_data, json_file, indent=4)
        st.success("Original invoice data saved as 'extracted_invoice_data.json'.")
else:
    st.warning("No valid data was extracted from the invoices.")
