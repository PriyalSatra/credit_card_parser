"""
Streamlit web application for parsing credit card statements.
"""

import streamlit as st
import pandas as pd
import tempfile
import os
from parser import ChaseParser, StatementData

# Set page config
st.set_page_config(
    page_title="Credit Card Statement Multi-Parser",
    page_icon="💳",
    layout="wide"
)

# App title
st.title("💳 Credit Card Statement Multi-Parser")

# File uploader
st.header("Upload Statement")
uploaded_file = st.file_uploader(
    "Choose a PDF file",
    type="pdf",
    help="Upload a credit card statement PDF to extract transaction data"
)

if uploaded_file is not None:
    # Display file info
    st.success(f"File uploaded: {uploaded_file.name}")
    st.write(f"File size: {uploaded_file.size} bytes")
    
    # Parse the file
    with st.spinner("Parsing statement... Please wait."):
        try:
            # Create a temporary file to write the uploaded bytes
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                # Write the uploaded file bytes to the temporary file
                tmp_file.write(uploaded_file.getvalue())
                tmp_file_path = tmp_file.name
            
            # Parse using ChaseParser
            parser = ChaseParser()
            statement_data = parser.parse(tmp_file_path)
            
            # Clean up the temporary file
            os.unlink(tmp_file_path)
            
            # Display results
            st.success("✅ Statement parsed successfully!")
            
            # Summary section
            st.header("📊 Summary")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Card Last 4", statement_data.card_last_4 or "N/A")
            
            with col2:
                st.metric("Total Balance", f"${statement_data.total_balance:,.2f}")
            
            with col3:
                st.metric("Due Date", statement_data.due_date or "N/A")
            
            with col4:
                st.metric("Billing Cycle", statement_data.billing_cycle or "N/A")
            
            # Additional details
            st.subheader("Statement Details")
            details_data = {
                "Issuer": statement_data.issuer,
                "Card Last 4 Digits": statement_data.card_last_4 or "Not found",
                "Billing Cycle": statement_data.billing_cycle or "Not found",
                "Due Date": statement_data.due_date or "Not found",
                "Total Balance": f"${statement_data.total_balance:,.2f}",
                "Number of Transactions": len(statement_data.transactions)
            }
            
            for key, value in details_data.items():
                st.write(f"**{key}:** {value}")
            
            # Transactions section
            st.header("💳 Extracted Transactions")
            
            if statement_data.transactions:
                # Convert transactions to DataFrame for better display
                df = pd.DataFrame(statement_data.transactions)
                
                # Format the amount column for better display
                if 'amount' in df.columns:
                    df['amount'] = df['amount'].apply(lambda x: f"${x:,.2f}")
                
                # Display the dataframe
                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True
                )
                
                # Download option for the data
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Transactions as CSV",
                    data=csv,
                    file_name=f"transactions_{statement_data.card_last_4 or 'unknown'}.csv",
                    mime="text/csv"
                )
                
                # Show transaction statistics
                st.subheader("📈 Transaction Statistics")
                if len(statement_data.transactions) > 0:
                    amounts = [t['amount'] for t in statement_data.transactions if isinstance(t['amount'], (int, float))]
                    if amounts:
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Total Transactions", len(statement_data.transactions))
                        with col2:
                            st.metric("Average Amount", f"${sum(amounts)/len(amounts):,.2f}")
                        with col3:
                            st.metric("Highest Amount", f"${max(amounts):,.2f}")
            else:
                st.warning("⚠️ No transactions found in the statement.")
                
        except FileNotFoundError:
            st.error("❌ Error: Could not find the uploaded file.")
        except Exception as e:
            st.error(f"❌ Error parsing the statement: {str(e)}")
            st.write("Please ensure the PDF is a valid credit card statement.")

else:
    st.info("👆 Please upload a PDF file to get started.")
    st.write("""
    ### How to use:
    1. Upload a credit card statement PDF file
    2. The app will automatically parse the document
    3. View the extracted summary and transaction data
    4. Download the transaction data as CSV if needed
    """)

# Footer
st.markdown("---")
