# Project Title: Invoice Extractor

## Overview

Invoice Extractor is a web-based application that allows users to upload invoices (PDFs), preview the first page, and extract important information such as Invoice Number, Date, Customer Details, Itemized Products/Services, Total Amount, and Tax. The application is powered by AI models like LangChain and Google Generative AI (PaLM).

## Features

- Upload invoices in PDF format.
- Preview the first page of the PDF on the left side of the screen.
- Extract key details from the invoice using AI and display them in a structured format (right side).
- Data is processed and displayed in real-time.

## Tech Stack

- **Backend**: Python, Streamlit
- **Libraries** : 
  - `PyPDF2` for parsing PDFs
  - `pdf2image` for rendering PDF pages
  - `LangChain` for AI language model interaction
  - `pandas` for handling data
  - `tqdm` for progress bars
  - `dotenv` for environment variable management
- **AI**: Google PaLM (Generative AI)

## Setup Instructions

### Prerequisites

- **Python 3.8+** installed.
- **Google Cloud API Key** with access to Generative AI (PaLM).

### Installation

1. **Clone the repository** :
   ```bash
   git clone https://github.com/Ayush-Gursal/Ordway_Labs_Project.git
   cd Ordway_Labs_Project

2. **Create a virtual environment** :
   ```bash
   python -m venv venv

3. **Activate the virtual environment** :
     ```bash
     venv\Scripts\activate

3. **Install the required dependencies** :

     ```bash
     pip install -r requirements.txt
3. **Set up environment variables**:
    - Create a `.env` file in the root directory of your project..
    - Add the following content to the `.env` file:

     ```bash
     GOOGLE_API_KEY=your_google_api_key_here

3. **Run the application** :
     ```bash
     streamlit run main.py

3. **Project Structure** :

    BE_Project/|

    ├── Uploaded_Invoices/        
    ├── .gitignore                
    ├── .env                      
    ├── README.md                 
    ├── main.py                   
    ├── requirements.txt          
    └── invoice_data.csv         


