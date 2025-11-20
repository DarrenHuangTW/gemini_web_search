import streamlit as st
import os
import json
import pandas as pd
from google import genai
from google.genai import types
from openai import OpenAI
from datetime import datetime
import io

def init_gemini_client(api_key):
    return genai.Client(api_key=api_key)

def init_openai_client(api_key):
    return OpenAI(api_key=api_key)

def process_prompt_gemini(client, prompt):
    grounding_tool = types.Tool(
        google_search=types.GoogleSearch()
    )
    
    config = types.GenerateContentConfig(
        tools=[grounding_tool]
    )
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=config,
    )
    
    result = {
        "original_prompt": prompt,
        "provider": "Gemini",
        "web_search_used": False,
        "web_search_queries": [],
        "cited_sources": [],
        "final_response": ""
    }
    
    # Check if Google search was used
    if (hasattr(response.candidates[0], 'grounding_metadata') and 
        response.candidates[0].grounding_metadata):
        
        # Extract web search queries
        if hasattr(response.candidates[0].grounding_metadata, 'web_search_queries'):
            queries = response.candidates[0].grounding_metadata.web_search_queries
            if queries:
                result["web_search_used"] = True
                result["web_search_queries"] = [str(query) for query in queries]
        
        # Extract cited sources
        if hasattr(response.candidates[0].grounding_metadata, 'grounding_chunks'):
            chunks = response.candidates[0].grounding_metadata.grounding_chunks
            if chunks:
                for chunk in chunks:
                    if hasattr(chunk, 'web') and chunk.web:
                        result["cited_sources"].append({
                            "title": chunk.web.title,
                            "url": chunk.web.uri
                        })
    
    # Extract response text
    if (hasattr(response.candidates[0], 'content') and 
        response.candidates[0].content and
        hasattr(response.candidates[0].content, 'parts')):
        
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'text'):
                result["final_response"] = part.text
                break
    
    return result

def process_prompt_openai(client, prompt):
    result = {
        "original_prompt": prompt,
        "provider": "OpenAI",
        "web_search_used": False,
        "web_search_queries": [],
        "cited_sources": [],
        "final_response": ""
    }
    
    try:
        response = client.responses.create(
            model="gpt-4o",
            input=prompt,
            tools=[{"type": "web_search"}]
        )
        
        # Extract query from web search tool call
        for output in response.output:
            if hasattr(output, 'action') and hasattr(output.action, 'query'):
                result["web_search_used"] = True
                result["web_search_queries"].append(output.action.query)
        
        # Extract cited URLs
        for output in response.output:
            if hasattr(output, 'content'):
                for content in output.content:
                    if hasattr(content, 'annotations'):
                        for annotation in content.annotations:
                            if hasattr(annotation, 'url') and hasattr(annotation, 'title'):
                                result["cited_sources"].append({
                                    "title": annotation.title,
                                    "url": annotation.url
                                })
        
        # Extract response text
        for output in response.output:
            if hasattr(output, 'content'):
                for content in output.content:
                    if hasattr(content, 'text'):
                        result["final_response"] = content.text
                        break
        
    except Exception as e:
        result["final_response"] = f"Error: {str(e)}"
    
    return result

def create_downloadable_data(results):
    processed_data = []
    
    for result in results:
        processed_data.append({
            "Original Prompt": result["original_prompt"],
            "Provider": result["provider"],
            "Web Search Used": result["web_search_used"],
            "Number of Queries": len(result["web_search_queries"]),
            "Web Search Queries": "; ".join(result["web_search_queries"]) if result["web_search_queries"] else "",
            "Cited Sources URLs": "; ".join([source["url"] for source in result["cited_sources"]]) if result["cited_sources"] else "",
            "Cited Sources Titles": "; ".join([source["title"] for source in result["cited_sources"]]) if result["cited_sources"] else "",
            "Final Response": result["final_response"]
        })
    
    return pd.DataFrame(processed_data)

def main():
    st.set_page_config(
        page_title="Overdose AI Web Search App", 
        page_icon="🔍",
        layout="wide"
    )
    
    st.title("🔍 Overdose AI Web Search App")
    st.markdown("Enter up to 50 prompts to process with AI models and web search capabilities.")
    
    # Initialize session state
    if 'results' not in st.session_state:
        st.session_state.results = []
    if 'processed_count' not in st.session_state:
        st.session_state.processed_count = 0
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("🔧 Configuration")
        
        # Provider selection
        provider = st.selectbox(
            "Choose AI Provider:",
            ["Gemini", "OpenAI"],
            help="Select which AI provider to use for web search"
        )
        
        # API Key input based on provider
        if provider == "Gemini":
            api_key = st.text_input(
                "Google AI API Key:",
                type="password",
                placeholder="Enter your Google AI API key",
                help="Get your API key from https://aistudio.google.com/app/apikey"
            )
            model_info = "**Model:** Gemini 2.5 Flash"
            features_info = "**Features:** Google Search grounding"
        else:  # OpenAI
            api_key = st.text_input(
                "OpenAI API Key:",
                type="password",
                placeholder="Enter your OpenAI API key",
                help="Get your API key from https://platform.openai.com/api-keys"
            )
            model_info = "**Model:** GPT-4o"
            features_info = "**Features:** Web search capabilities"
        
        if api_key:
            st.success("✅ API key provided")
        else:
            st.warning("⚠️ Please enter your API key to use the app")
        
        st.divider()
        
        st.markdown(f"**Provider:** {provider}")
        st.markdown(model_info)
        st.markdown(features_info)
        
        st.divider()
        
        if st.button("🗑️ Clear All Results", type="secondary"):
            st.session_state.results = []
            st.session_state.processed_count = 0
            st.rerun()
    
    # Input section
    st.header("📝 Input Prompts")
    
    # Text area for multiple prompts
    prompts_input = st.text_area(
        "Enter your prompts (one per line, max 50):",
        height=200,
        placeholder="Enter your prompts here, one per line...\nExample:\nWhat's the latest news about AI?\nTell me about climate change in 2024."
    )
    
    # Process button
    col1, col2 = st.columns([1, 4])
    with col1:
        process_button = st.button("🚀 Process Prompts", type="primary")
    
    if process_button and prompts_input.strip():
        # Check if API key is provided
        if not api_key:
            st.error(f"❌ Please enter your {provider} API key in the sidebar.")
            return
        
        prompts = [prompt.strip() for prompt in prompts_input.split('\n') if prompt.strip()]
        
        if len(prompts) > 50:
            st.error("Please limit to 50 prompts maximum.")
            return
        
        if len(prompts) == 0:
            st.error("Please enter at least one prompt.")
            return
        
        # Initialize client based on provider
        try:
            if provider == "Gemini":
                client = init_gemini_client(api_key)
            else:  # OpenAI
                client = init_openai_client(api_key)
        except Exception as e:
            st.error(f"Failed to initialize {provider} client: {str(e)}")
            return
        
        # Process prompts with progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        results = []
        for i, prompt in enumerate(prompts):
            status_text.text(f"Processing prompt {i+1} of {len(prompts)}: {prompt[:50]}...")
            
            try:
                if provider == "Gemini":
                    result = process_prompt_gemini(client, prompt)
                else:  # OpenAI
                    result = process_prompt_openai(client, prompt)
                results.append(result)
            except Exception as e:
                st.error(f"Error processing prompt '{prompt}': {str(e)}")
                results.append({
                    "original_prompt": prompt,
                    "provider": provider,
                    "web_search_used": False,
                    "web_search_queries": [],
                    "cited_sources": [],
                    "final_response": f"Error: {str(e)}"
                })
            
            progress_bar.progress((i + 1) / len(prompts))
        
        st.session_state.results.extend(results)
        st.session_state.processed_count += len(prompts)
        status_text.text("✅ Processing complete!")
        
        st.success(f"Processed {len(prompts)} prompts successfully!")
    
    # Results section
    if st.session_state.results:
        st.header("📊 Results")
        st.markdown(f"**Total processed prompts:** {st.session_state.processed_count}")
        
        # Summary statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            search_used_count = sum(1 for r in st.session_state.results if r["web_search_used"])
            st.metric("Prompts using Web Search", search_used_count)
        with col2:
            total_queries = sum(len(r["web_search_queries"]) for r in st.session_state.results)
            st.metric("Total Search Queries", total_queries)
        with col3:
            total_sources = sum(len(r["cited_sources"]) for r in st.session_state.results)
            st.metric("Total Cited Sources", total_sources)
        with col4:
            provider_counts = {}
            for r in st.session_state.results:
                provider_counts[r["provider"]] = provider_counts.get(r["provider"], 0) + 1
            provider_summary = ", ".join([f"{k}: {v}" for k, v in provider_counts.items()])
            st.metric("Provider Usage", provider_summary)
        
        # Display results in table format
        display_data = []
        for i, result in enumerate(st.session_state.results):
            # Format queries as numbered list
            queries_list = []
            for j, query in enumerate(result["web_search_queries"], 1):
                queries_list.append(f"{j}. {query}")
            
            # Format cited sources as numbered list
            sources_list = []
            for j, source in enumerate(result["cited_sources"], 1):
                sources_list.append(f"{j}. {source['title']} ({source['url']})")
            
            # Truncate response to 300 characters
            truncated_response = result["final_response"]
            if len(truncated_response) > 300:
                truncated_response = truncated_response[:297] + "..."
            
            display_data.append({
                "ID": i + 1,
                "Original Prompt": result["original_prompt"],
                "Provider": result["provider"],
                "Web Search Used": "✅ Yes" if result["web_search_used"] else "❌ No",
                "# Queries": len(result["web_search_queries"]),
                "Web Search Queries": "\n".join(queries_list) if queries_list else "None",
                "Final Response (300 chars)": truncated_response
            })
        
        if display_data:
            df_display = pd.DataFrame(display_data)
            st.dataframe(
                df_display,
                width='stretch',
                height=600,
                column_config={
                    "ID": st.column_config.NumberColumn("ID", width="small"),
                    "Original Prompt": st.column_config.TextColumn("Original Prompt", width="medium"),
                    "Provider": st.column_config.TextColumn("Provider", width="small"),
                    "Web Search Used": st.column_config.TextColumn("Search Used", width="small"),
                    "# Queries": st.column_config.NumberColumn("# Queries", width="small"),
                    "Web Search Queries": st.column_config.TextColumn("Queries", width="medium"),
                    "Final Response (300 chars)": st.column_config.TextColumn("Response", width="large")
                }
            )
        
        # Download section
        st.header("💾 Download Results")
        
        # Create downloadable data
        df = create_downloadable_data(st.session_state.results)
        
        # Download as CSV
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_data = csv_buffer.getvalue()
        
        # Download as JSON
        json_data = json.dumps(st.session_state.results, indent=2)
        
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="📄 Download as CSV",
                data=csv_data,
                file_name=f"ai_web_search_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        with col2:
            st.download_button(
                label="📋 Download as JSON",
                data=json_data,
                file_name=f"ai_web_search_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    # Footer
    st.divider()
    st.markdown(
        "<div style='text-align: center; color: gray; font-size: 12px; margin-top: 50px;'>"
        "Built by Darren Huang • Reach out for questions or feature requests"
        "</div>", 
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()