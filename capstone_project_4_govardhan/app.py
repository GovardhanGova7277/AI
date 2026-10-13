# =====================================================================
# CREATE A NEW SEPARATE FILE NAMED: app.py (CORRECTED ROUTING)
# =====================================================================
import streamlit as st
import requests

st.set_page_config(page_title="Sustainability RAG Dashboard", page_icon="🌱", layout="wide")

st.title("🌱 Corporate Sustainability Advanced RAG Dashboard")
st.write("Interact with the data processing engine running in your Jupyter Notebook in real time.")


BACKEND_API_URL = "http://127.0.0.1:8000/ask"

# Simple test questions matching your project criteria
st.subheader(" Sample Assessment Queries")
sample_prompts = [
    "What are Microsoft's goals for sustainability and carbon emissions?",
    "How does Unilever manage plastic waste?",
    "What steps has Coca-Cola taken to reduce water usage?"
]
selected_sample = st.selectbox("Click to auto-populate a sample test question:", [""] + sample_prompts)
user_query = st.text_input("Or type your custom analytical question here:", value=selected_sample)

if st.button("Run Grounded RAG Pipeline Engine", type="primary"):
    if not user_query.strip():
        st.warning("Please enter a question string to continue.")
    else:
        with st.spinner("Communicating with Jupyter Notebook to retrieve contexts and generate answer..."):
            try:
                # Post the question across the local network to your active notebook cell
                payload = {"question": user_query.strip()}
                api_response = requests.post(BACKEND_API_URL, json=payload)
                
                if api_response.status_code == 200:
                    data = api_response.json()
                    
                    # 1. Render Grounded Answer Response Block
                    st.subheader(" Strategic Audit Response")
                    st.markdown(data["answer"])
                    
                    # 2. Render Step 7 Scorecard Metrics Dashboard
                    st.subheader(" Capstone Step 7 Qualitative Evaluation Scorecard")
                    eval_card = data["scorecard"]
                    
                    if "error" not in eval_card:
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            f_data = eval_card.get("1. Faithfulness (Anti-Hallucination)", {})
                            st.metric("Faithfulness Score", f"{f_data.get('Score (1-5 Scale)', 'N/A')}/5", delta=f_data.get('Assessment'))
                            st.caption(f_data.get('Judge Explanation', ''))
                        with col2:
                            r_data = eval_card.get("2. Relevance (Contextual Accuracy)", {})
                            st.metric("Relevance Score", f"{r_data.get('Score (1-5 Scale)', 'N/A')}/5", delta=r_data.get('Assessment'))
                            st.caption(r_data.get('Judge Explanation', ''))
                        with col3:
                            c_data = eval_card.get("3. Conciseness (Summary Efficiency)", {})
                            st.metric("Conciseness Score", f"{c_data.get('Score (1-5 Scale)', 'N/A')}/5", delta=c_data.get('Assessment'))
                            st.caption(c_data.get('Judge Explanation', ''))
                    else:
                        st.warning(f"Evaluation metrics skipped: {eval_card['error']}")
                    
                    # 3. Render Document Reference Source Tab Items
                    st.subheader(" Supporting Evidence Blocks (Top Reranked Context Excerpts)")
                    tabs = st.tabs([f"Excerpt {i+1} (Rerank Score: {src['reranker_score']:.4f})" for i, src in enumerate(data["sources"])])
                    
                    for idx, tab in enumerate(tabs):
                        with tab:
                            source_item = data["sources"][idx]
                            st.markdown(f"** Document Source file:** `{source_item['file_name']}`")
                            st.info(f"\"{source_item['text']}\"")
                else:
                    st.error(f"Jupyter Notebook returned an error: {api_response.text}")
            except Exception as e:
                st.error(f"Could not connect to your Jupyter Notebook. Make sure the last cell is running! Error: {e}")
