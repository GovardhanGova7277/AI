"""
Streamlit Frontend for Multi-Agent Research Analyst
Deploy this to Streamlit Community Cloud for public access.
"""

import streamlit as st
import time

# Page configuration
st.set_page_config(
    page_title="Agentic Research Analyst",
    page_icon="mag",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for clean formatting
st.markdown("""
<style>
    .report-text { line-height: 1.8; }
    blockquote { border-left: 4px solid #4CAF50; padding-left: 1rem; margin: 1rem 0; }
</style>
""", unsafe_allow_html=True)

def initialize_system():
    """Initialize the graph without interrupts for smooth web execution."""
    return build_research_graph(enable_interrupt=False)

def stream_results(graph, question, config):
    """Generator to yield state updates as they happen."""
    initial_state = {
        "question": question, "plan": [], "findings": [], "draft": "",
        "references": [], "critique": "", "iterations": 0, "approved": False
    }
    
    # stream() yields updates node by node
    for event in graph.stream(initial_state, config=config):
        node_name = list(event.keys())[0]
        node_state = event[node_name]
        yield node_name, node_state

# --- Sidebar ---
with st.sidebar:
    st.header("System Architecture")
    st.caption("Powered by LangGraph & Groq")
    st.markdown("""
    **Workflow Patterns:**
    - Planner-Executor
    - Orchestrator-Workers (Parallel Fan-out)
    - Evaluator-Optimizer (Critic Loop)
    """)
    st.divider()
    st.markdown("**Tech Stack:**\n- LLM: Groq (Llama 3.3 70B)\n- Search: Tavily\n- Orchestration: LangGraph")

# --- Main Interface ---
st.title("Multi-Agent Research Analyst")
st.markdown("Enter a complex research question. The system will decompose it, research it in parallel, synthesize a brief, and run it through a quality critic.")

question = st.text_area(
    "Research Question:",
    height=100,
    placeholder="e.g., Compare the current EV strategies of Tata Motors and BYD."
)

if st.button("Run Analysis", type="primary", disabled=not question):
    graph = initialize_system()
    
    # UI Containers
    plan_container = st.expander("Research Plan", expanded=False)
    trace_container = st.expander("Live Agent Trace", expanded=True)
    result_container = st.container()
    
    start_time = time.time()
    trace_logs = []
    final_draft = ""  # <-- Initialize in the OUTER scope
    
    config = {"configurable": {"thread_id": f"streamlit-run-{time.time()}"}}
    
    with st.spinner("Agents are working..."):
        for node_name, node_state in stream_results(graph, question, config):
            
            # Handle Planner output
            if node_name == "planner" and node_state.get("plan"):
                with plan_container:
                    st.write("**Generated Sub-Questions:**")
                    for i, pq in enumerate(node_state["plan"], 1):
                        st.write(f"{i}. {pq}")
            
            # Handle Researcher output
            if "researcher" in node_name:
                for finding in node_state.get("findings", []):
                    log = f"**{node_name.upper()}** completed: {finding.get('sub_question', '')[:60]}..."
                    trace_logs.append(log)
            
            # Handle Synthesiser output & capture the draft
            if node_name == "synthesiser":
                trace_logs.append("**SYNTHESISER** completed drafting brief.")
                if node_state.get("draft"):
                    final_draft = node_state["draft"] # <-- Capture it here!
                
            # Handle Critic output
            if node_name == "critic":
                iterations = node_state.get("iterations", 0)
                approved = node_state.get("approved", False)
                status = "APPROVED" if approved else f"NEEDS REVISION (Iteration {iterations})"
                trace_logs.append(f"**CRITIC** status: {status}")
            
            # Update trace log live
            trace_placeholder = trace_container.empty()
            trace_placeholder.markdown("\n".join(f"- {log}" for log in trace_logs))
    
    end_time = time.time()
    total_time = round(end_time - start_time, 2)
    
    # Display Final Result
    with result_container:
        st.divider()
        col1, col2, col3 = st.columns(3)
        col1.metric("Time Taken", f"{total_time}s")
        col2.metric("Critic Iterations", trace_logs[-1].count("Iteration") if trace_logs else 0)
        col3.metric("Status", "Complete")
        
        st.markdown("---")
        st.subheader("Research Brief")
        st.markdown(final_draft, unsafe_allow_html=True)

else:
    st.info("Awaiting a research question to begin analysis.")