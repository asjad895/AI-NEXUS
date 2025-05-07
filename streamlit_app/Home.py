import streamlit as st

st.set_page_config(
    page_title="AI Nexus",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        margin-bottom: 0;
    }
    .subtitle {
        font-size: 1.5rem;
        margin-bottom: 2rem;
        color: #666;
    }
    .feature-card {
        # color for black page on streamlit, as text is white,background should be other
        background-color: lightgray;
        border-radius: 5px;
        padding: 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
        margin-bottom: 20px;
        height: 100%;
    }
    .feature-icon {
        font-size: 2rem;
        margin-bottom: 10px;
    }
    .feature-title {
        font-size: 1.5rem;
        font-weight: bold;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state for user
if 'user_id' not in st.session_state:
    st.session_state.user_id = None

# Sidebar for user settings
def render_sidebar():
    """Render the sidebar with user settings."""
    st.sidebar.title("User Settings")
    
    if st.session_state.user_id:
        st.sidebar.success(f"Logged in as: {st.session_state.user_id}")
        if st.sidebar.button("Logout"):
            st.session_state.user_id = None
            st.rerun()
    else:
        with st.sidebar.form("login_form"):
            user_id = st.text_input("Enter User ID:", key="login_user_id")
            submit = st.form_submit_button("Login")
            
            if submit and user_id:
                st.session_state.user_id = user_id
                st.rerun()

    # Navigation
    st.sidebar.title("Navigation")
    st.sidebar.markdown("Use the pages in the sidebar to navigate between different features.")
    
    # About section
    st.sidebar.title("About")
    st.sidebar.info(
        """
        GENAI: End-to-End Training and Evaluation
        A comprehensive platform for FAQ extraction, model fine-tuning, and evaluation.
        """
    )

# Main content
def main():
    # Render sidebar
    render_sidebar()
    
    # Header
    st.markdown("<h1 class='main-header'>AI NEXUS</h1>", unsafe_allow_html=True)
    st.markdown("<p class='subtitle'>GenAI: End-to-End Training and Evaluation</p>", unsafe_allow_html=True)
    
    # Feature cards
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class='feature-card'>
            <div class='feature-icon'>❓</div>
            <div class='feature-title'>FAQ Pipeline</div>
            <p>Extract FAQs from documents automatically. Upload a document and the system will identify questions and answers.</p>
            <p>Use the FAQ Pipeline to create datasets for fine-tuning models.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<div style='text-align: center; margin-top: 20px;'>", unsafe_allow_html=True)
        if st.button("Go to FAQ Pipeline", key="goto_faq"):
            st.switch_page("pages/faq.py")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class='feature-card'>
            <div class='feature-icon'>🧠</div>
            <div class='feature-title'>Fine-tuning</div>
            <p>Fine-tune AI models with your data. Use the FAQ datasets to create specialized models for your domain.</p>
            <p>Compare different models and evaluate their performance.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<div style='text-align: center; margin-top: 20px;'>", unsafe_allow_html=True)
        if st.button("Go to Fine-tuning", key="goto_finetune"):
            st.switch_page("pages/finetune.py")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Getting started section
    st.markdown("## Getting Started")
    st.markdown("""
    1. **Login** - Enter your user ID in the sidebar to get started
    2. **FAQ Pipeline** - Extract FAQs from your documents
    3. **Fine-tuning** - Use the extracted FAQs to fine-tune models
    4. **Evaluation** - Compare and evaluate model performance
    """)
    
    # System status
    st.markdown("## System Status")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("API Status", "Online", "✓")
    
    with col2:
        st.metric("Active Jobs", "3", "+1")
    
    with col3:
        st.metric("Models", "5", "+2")

if __name__ == "__main__":
    main()