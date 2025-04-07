%%writefile app.py
import streamlit as st
import requests
from bs4 import BeautifulSoup
import openai
from urllib.parse import urlparse

st.set_page_config(page_title="Document QA Assistant", layout="wide")

st.title("Document QA Assistant")
st.write("Enter a document URL and ask questions about its content.")

# Input for OpenAI API key
api_key = st.text_input("Enter your OpenAI API key:", type="password")

# Input for document URL
doc_url = st.text_input("Enter document URL:")

# Document content storage
document_content = ""

# Function to extract text from URL
def extract_text_from_url(url):
    try:
        # Check if URL is valid
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            return "Error: Invalid URL format. Please include http:// or https://"
        
        # Make request to the URL
        response = requests.get(url)
        response.raise_for_status()
        
        # Parse HTML content
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract text (remove scripts, styles, etc.)
        for script in soup(["script", "style", "header", "footer", "nav"]):
            script.extract()
        
        # Get text content
        text = soup.get_text(separator='\n')
        
        # Clean up text (remove extra whitespace)
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return text
    
    except requests.exceptions.RequestException as e:
        return f"Error fetching document: {str(e)}"
    except Exception as e:
        return f"Error processing document: {str(e)}"

# Button to fetch document
if st.button("Fetch Document") and doc_url:
    with st.spinner("Fetching document content..."):
        document_content = extract_text_from_url(doc_url)
        
        # Display preview of document
        st.subheader("Document Content Preview:")
        st.text_area("Preview", document_content[:1000] + "..." if len(document_content) > 1000 else document_content, height=200)
        
        # Save document in session state for later use
        st.session_state.document_content = document_content

# Question input
user_question = st.text_input("Ask a question about the document:")

# Function to get answer using OpenAI
def get_answer_from_openai(question, document, api_key):
    try:
        openai.api_key = api_key
        
        # Prepare prompt
        prompt = f"""
        Document content:
        {document[:4000]}
        
        Question: {question}
        
        Please answer the question based only on the information provided in the document.
        If the answer is not in the document, say "I don't have enough information to answer this question."
        """
        
        # Call OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that answers questions based on document content."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        return f"Error generating answer: {str(e)}"

# Button to get answer
if st.button("Get Answer") and user_question and api_key:
    if not hasattr(st.session_state, 'document_content') or not st.session_state.document_content:
        st.error("Please fetch a document first.")
    else:
        with st.spinner("Generating answer..."):
            answer = get_answer_from_openai(user_question, st.session_state.document_content, api_key)
            
            # Display answer
            st.subheader("Answer:")
            st.write(answer)

# Instructions in sidebar
st.sidebar.title("How to Use")
st.sidebar.write("""
1. Enter your OpenAI API key
2. Paste a document URL (web page, article, etc.)
3. Click 'Fetch Document' to extract the content
4. Ask a question about the document
5. Click 'Get Answer' to receive a response
""")

st.sidebar.title("Limitations")
st.sidebar.write("""
- Works best with HTML web pages
- May not work with PDFs or other document formats
- Limited to processing ~4000 characters of the document due to API constraints
- Requires a valid OpenAI API key
""")
