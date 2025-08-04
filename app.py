import streamlit as st
from datetime import date
import sys
import os

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from main import (
        find_relevant_threads,
        analyze_thread_content,
        analyze_multiple_threads,
        generate_product_dossier,
    )
    from utils import parse_crewai_output
except ImportError as e:
    st.error(f"Error importing modules: {e}")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="Email Thread Analyzer", page_icon="📧", layout="wide"
)

# Initialize session state variables
if "threads" not in st.session_state:
    st.session_state.threads = []
if "selected_thread_ids" not in st.session_state:
    st.session_state.selected_thread_ids = []
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None
if "dossier" not in st.session_state:
    st.session_state.dossier = None

# Title and description
st.title("📧 Email Thread Analyzer and Product Dossier Creator")
st.markdown(
    """
This application helps you find relevant email threads and analyze them on-demand.
1. First, find relevant emails based on a date range and optional filters (keyword, sender, or general query).
2. Then, select one or more threads to analyze their content.
3. Finally, generate a detailed product dossier if needed.
"""
)

# Sidebar for inputs
with st.sidebar:
    st.header("Search Parameters")

    st.subheader("Date Range")
    start_date = st.date_input(
        "Start Date", value=date(2023, 1, 1), help="Select the start date for email search"
    )
    end_date = st.date_input(
        "End Date", value=date.today(), help="Select the end date for email search"
    )

    st.subheader("Search Filters (All Optional)")
    
    keyword = st.text_input(
        "Keyword (optional)",
        placeholder="e.g., meeting, project, proposal",
        help="Enter keywords to search for in email content (e.g., meeting, project, proposal).",
    )

    email_id = st.text_input(
        "Sender Email (optional)",
        placeholder="example@gmail.com",
        help="Enter a specific sender email address to narrow the search.",
    )
    
    query = st.text_input(
        "General Query (optional)",
        placeholder="e.g., AWS deployment issues",
        help="Enter a general search query to find emails (e.g., 'show me all emails from Kushal related to AWS').",
    )

    if st.button("🔍 Find Relevant Emails", type="primary"):
        st.session_state.threads = []
        st.session_state.selected_thread_ids = []
        st.session_state.analysis_result = None
        st.session_state.dossier = None

        if start_date > end_date:
            st.error("❌ Error: Start date cannot be after end date.")
        else:
            # Check if at least one search parameter is provided
            has_search_criteria = bool(keyword or email_id or query)
            
            if not has_search_criteria:
                st.warning("⚠️ No search criteria provided. Searching all emails in the date range...")
            
            with st.spinner("🔄 Finding and filtering relevant email threads..."):
                try:
                    st.session_state.threads = find_relevant_threads(
                        start_date=start_date.strftime("%Y/%m/%d"),
                        end_date=end_date.strftime("%Y/%m/%d"),
                        keyword=keyword if keyword else None,
                        from_email=email_id if email_id else None,
                        query=query if query else None,
                    )
                    if not st.session_state.threads:
                        st.warning("⚠️ No relevant email threads found. Try adjusting your search criteria.")
                except Exception as e:
                    st.error(f"❌ An error occurred while finding emails: {str(e)}")

# --- Main Content Area ---

# Step 2: Thread Selection
if st.session_state.threads:
    st.header("Step 2: Select Threads to Analyze")
    st.markdown("Select one or more email threads for analysis:")
    
    # Create checkboxes for each thread
    for thread in st.session_state.threads:
        thread_id = thread["id"]
        thread_label = f"Subject: {thread['subject']} | From: {thread['sender']}"
        
        # Check if this thread is currently selected
        is_selected = thread_id in st.session_state.selected_thread_ids
        
        # Create checkbox
        if st.checkbox(thread_label, value=is_selected, key=f"thread_{thread_id}"):
            if thread_id not in st.session_state.selected_thread_ids:
                st.session_state.selected_thread_ids.append(thread_id)
        else:
            if thread_id in st.session_state.selected_thread_ids:
                st.session_state.selected_thread_ids.remove(thread_id)
    
    # Show selected count
    selected_count = len(st.session_state.selected_thread_ids)
    if selected_count > 0:
        st.info(f"✅ {selected_count} thread(s) selected")

    if st.button("🔬 Analyze Selected Threads", disabled=selected_count == 0):
        st.session_state.analysis_result = None # Reset previous results
        st.session_state.dossier = None
        with st.spinner(f"🔄 Analyzing {selected_count} email thread(s)..."):
            try:
                if selected_count == 1:
                    # Single thread analysis
                    result = analyze_thread_content(st.session_state.selected_thread_ids[0])
                else:
                    # Multiple threads analysis
                    result = analyze_multiple_threads(st.session_state.selected_thread_ids)
                st.session_state.analysis_result = result
            except Exception as e:
                st.error(f"❌ An error occurred during analysis: {str(e)}")

# Step 3: Display Analysis and Generate Dossier
if st.session_state.analysis_result:
    thread_count = st.session_state.analysis_result.get("thread_count", 1)
    st.header(f"📋 Analysis Result ({thread_count} thread{'s' if thread_count > 1 else ''})")
    st.markdown("---")
    
    # Display the analysis text
    analysis_text = st.session_state.analysis_result.get("analysis", "No analysis content found.")
    parsed_output = parse_crewai_output(analysis_text)
    st.markdown(parsed_output)

    st.header("Step 3: Generate Product Dossier")
    product_name = st.session_state.analysis_result.get("product_name", "Unknown")
    
    if st.button(f"Generate Dossier for '{product_name}'"):
        with st.spinner(f"📚 Creating dossier for {product_name}..."):
            try:
                dossier_output = generate_product_dossier(
                    product_name=product_name,
                    product_domain=st.session_state.analysis_result.get("product_domain", "general product"),
                )
                st.session_state.dossier = dossier_output
            except Exception as e:
                st.error(f"❌ An error occurred while generating the dossier: {str(e)}")

# Display Dossier
if st.session_state.dossier:
    st.header("📊 Product Dossier")
    st.markdown("---")
    parsed_dossier = parse_crewai_output(st.session_state.dossier)
    st.markdown(parsed_dossier)

# Footer
st.markdown("---")
st.markdown("*Powered by CrewAI, Gmail API, and Streamlit*")



# import streamlit as st
# from datetime import date
# import sys
# import os

# # Add the current directory to the Python path
# sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# try:
#     from main import (
#         find_relevant_threads,
#         analyze_thread_content,
#         analyze_multiple_threads,
#         generate_product_dossier,
#     )
#     from utils import parse_crewai_output
# except ImportError as e:
#     st.error(f"Error importing modules: {e}")
#     st.stop()

# # Page configuration
# st.set_page_config(
#     page_title="Email Thread Analyzer", page_icon="📧", layout="wide"
# )

# # Initialize session state variables
# if "threads" not in st.session_state:
#     st.session_state.threads = []
# if "selected_thread_ids" not in st.session_state:
#     st.session_state.selected_thread_ids = []
# if "analysis_result" not in st.session_state:
#     st.session_state.analysis_result = None
# if "dossier" not in st.session_state:
#     st.session_state.dossier = None

# # Title and description
# st.title("📧 Email Thread Analyzer and Product Dossier Creator")
# st.markdown(
#     """
# This application helps you find relevant email threads and analyze them on-demand.
# 1. First, find relevant emails based on a date range, keywords, and optional sender.
# 2. Then, select a thread to analyze its content.
# 3. Finally, generate a detailed product dossier if needed.
# """
# )

# # Sidebar for inputs
# with st.sidebar:
#     st.header("Search Parameters")

#     st.subheader("Date Range")
#     start_date = st.date_input(
#         "Start Date", value=date(2023, 1, 1), help="Select the start date for email search"
#     )
#     end_date = st.date_input(
#         "End Date", value=date.today(), help="Select the end date for email search"
#     )

#     st.subheader("Keyword Search")
#     keyword = st.text_input(
#         "Keyword",
#         placeholder="e.g., meeting, project, proposal",
#         help="Enter keywords to search for in email content (e.g., meeting, project, proposal).",
#     )

#     st.subheader("Sender Filter")
#     email_id = st.text_input(
#         "Email ID (optional)",
#         placeholder="example@gmail.com",
#         help="Enter a specific sender email address to narrow the search.",
#     )

#     if st.button("🔍 Find Relevant Emails", type="primary"):
#         st.session_state.threads = []
#         st.session_state.selected_thread_ids = []
#         st.session_state.analysis_result = None
#         st.session_state.dossier = None

#         if not keyword:
#             st.error("❌ Error: Keyword field cannot be empty.")
#         elif start_date > end_date:
#             st.error("❌ Error: Start date cannot be after end date.")
#         else:
#             with st.spinner("🔄 Finding and filtering relevant email threads..."):
#                 try:
#                     st.session_state.threads = find_relevant_threads(
#                         start_date=start_date.strftime("%Y/%m/%d"),
#                         end_date=end_date.strftime("%Y/%m/%d"),
#                         keyword=keyword,
#                         from_email=email_id if email_id else None,
#                     )
#                     if not st.session_state.threads:
#                         st.warning("⚠️ No relevant email threads found. Try adjusting your search criteria.")
#                 except Exception as e:
#                     st.error(f"❌ An error occurred while finding emails: {str(e)}")

# # --- Main Content Area ---

# # Step 2: Thread Selection
# if st.session_state.threads:
#     st.header("Step 2: Select Threads to Analyze")
#     st.markdown("Select one or more email threads for analysis:")
    
#     # Create checkboxes for each thread
#     for thread in st.session_state.threads:
#         thread_id = thread["id"]
#         thread_label = f"Subject: {thread['subject']} | From: {thread['sender']}"
        
#         # Check if this thread is currently selected
#         is_selected = thread_id in st.session_state.selected_thread_ids
        
#         # Create checkbox
#         if st.checkbox(thread_label, value=is_selected, key=f"thread_{thread_id}"):
#             if thread_id not in st.session_state.selected_thread_ids:
#                 st.session_state.selected_thread_ids.append(thread_id)
#         else:
#             if thread_id in st.session_state.selected_thread_ids:
#                 st.session_state.selected_thread_ids.remove(thread_id)
    
#     # Show selected count
#     selected_count = len(st.session_state.selected_thread_ids)
#     if selected_count > 0:
#         st.info(f"✅ {selected_count} thread(s) selected")

#     if st.button("🔬 Analyze Selected Threads", disabled=selected_count == 0):
#         st.session_state.analysis_result = None # Reset previous results
#         st.session_state.dossier = None
#         with st.spinner(f"🔄 Analyzing {selected_count} email thread(s)..."):
#             try:
#                 if selected_count == 1:
#                     # Single thread analysis
#                     result = analyze_thread_content(st.session_state.selected_thread_ids[0])
#                 else:
#                     # Multiple threads analysis
#                     result = analyze_multiple_threads(st.session_state.selected_thread_ids)
#                 st.session_state.analysis_result = result
#             except Exception as e:
#                 st.error(f"❌ An error occurred during analysis: {str(e)}")

# # Step 3: Display Analysis and Generate Dossier
# if st.session_state.analysis_result:
#     thread_count = st.session_state.analysis_result.get("thread_count", 1)
#     st.header(f"📋 Analysis Result ({thread_count} thread{'s' if thread_count > 1 else ''})")
#     st.markdown("---")
    
#     # --- THIS IS THE FIX ---
#     # Explicitly get the analysis text, parse it, and display it.
#     analysis_text = st.session_state.analysis_result.get("analysis", "No analysis content found.")
#     parsed_output = parse_crewai_output(analysis_text)
#     st.markdown(parsed_output)
#     # -----------------------

#     st.header("Step 3: Generate Product Dossier")
#     product_name = st.session_state.analysis_result.get("product_name", "Unknown")
    
#     if st.button(f"Generate Dossier for '{product_name}'"):
#         with st.spinner(f"📚 Creating dossier for {product_name}..."):
#             try:
#                 dossier_output = generate_product_dossier(
#                     product_name=product_name,
#                     product_domain=st.session_state.analysis_result.get("product_domain", "general product"),
#                 )
#                 st.session_state.dossier = dossier_output
#             except Exception as e:
#                 st.error(f"❌ An error occurred while generating the dossier: {str(e)}")

# # Display Dossier
# if st.session_state.dossier:
#     st.header("📊 Product Dossier")
#     st.markdown("---")
#     parsed_dossier = parse_crewai_output(st.session_state.dossier)
#     st.markdown(parsed_dossier)

# # Footer
# st.markdown("---")
# st.markdown("*Powered by CrewAI, Gmail API, and Streamlit*")