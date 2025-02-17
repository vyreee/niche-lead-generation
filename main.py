import streamlit as st
import pandas as pd
from scraper import EnhancedWebsiteScraper
from analyzer import EnhancedContentAnalyzer
from email_finder import EmailFinder
from lead_processor import LeadProcessor
from lead_generator import LeadGenerator
import traceback

def init_api_components(openai_key, google_key):
    """Initialize API components with validation and debugging"""
    try:
        # Initialize each component separately with debug output
        st.write("Initializing Scraper...")
        scraper = EnhancedWebsiteScraper()
        
        st.write("Initializing Content Analyzer...")
        # Make sure the key is being passed as a string
        analyzer = EnhancedContentAnalyzer(api_key=str(openai_key).strip())
        
        st.write("Initializing Email Finder...")
        email_finder = EmailFinder(api_key=str(openai_key).strip())
        
        st.write("Initializing Lead Generator...")
        lead_generator = LeadGenerator(api_key=str(google_key).strip())
        
        st.write("Initializing Lead Processor...")
        processor = LeadProcessor(
            scraper=scraper,
            analyzer=analyzer,
            email_finder=email_finder,
            generator=lead_generator
        )
        
        st.write("All components initialized successfully!")
        return processor
        
    except Exception as e:
        st.error("🚨 Initialization Error")
        st.error(f"Error details: {str(e)}")
        st.error(f"Error location:\n{traceback.format_exc()}")
        return None

def main():
    st.set_page_config(page_title="Lead Generator Pro", layout="wide")
    st.title("🎯 Lead Generator Pro")

    # Add API key inputs in sidebar
    st.sidebar.title("API Configuration")
    
    openai_api_key = st.sidebar.text_input(
        "OpenAI API Key", 
        type="password",
        help="Get your API key from https://platform.openai.com/api-keys"
    )
    
    google_api_key = st.sidebar.text_input(
        "Google Places API Key",
        type="password",
        help="Get your API key from https://console.cloud.google.com/apis/credentials"
    )

    # Check for API keys
    if not openai_api_key or not google_api_key:
        st.warning("Please enter your API keys in the sidebar to use the application.")
        return

    # Initialize processor with explicit error handling
    processor = init_api_components(
        openai_key=openai_api_key,
        google_key=google_api_key
    )
    
    if not processor:
        st.error("Failed to initialize the application. Please check the error messages above.")
        return

    # Create tabs for different functionalities
    tab1, tab2 = st.tabs(["Upload Leads", "Generate Leads"])

    with tab1:
        st.header("Process Existing Leads")
        uploaded_file = st.file_uploader("Upload CSV with leads", type="csv")
        
        if uploaded_file:
            try:
                df = pd.read_csv(uploaded_file)
                st.write("Preview of uploaded data:")
                st.dataframe(df.head())
                
                required_cols = ['company_name', 'Website']
                missing_cols = [col for col in required_cols if col not in df.columns]
                
                if missing_cols:
                    st.error(f"Missing required columns: {', '.join(missing_cols)}")
                    return
                
                if st.button("Process Leads"):
                    with st.spinner("Processing leads..."):
                        # Remove duplicates
                        df = df.drop_duplicates(subset=['company_name', 'Website'])
                        st.write(f"Processing {len(df)} unique leads...")
                        
                        # Process leads
                        results_df = processor.process_leads(df)
                        
                        # Show results and download options
                        st.success("Processing complete!")
                        st.write("Results:")
                        st.dataframe(results_df)
                        
                        # Prepare download options
                        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
                        
                        # CSV download
                        csv = results_df.to_csv(index=False)
                        st.download_button(
                            label="📥 Download CSV",
                            data=csv,
                            file_name=f"processed_leads_{timestamp}.csv",
                            mime="text/csv"
                        )
                        
                        # Excel download
                        excel_data = processor.download_excel(results_df, f"processed_leads_{timestamp}.xlsx")
                        st.download_button(
                            label="📊 Download Excel",
                            data=excel_data,
                            file_name=f"processed_leads_{timestamp}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                        
            except Exception as e:
                st.error(f"Error processing file: {str(e)}")
                st.error(f"Error details:\n{traceback.format_exc()}")

    with tab2:
        st.header("Generate New Leads")
        
        # Business type selection
        business_types = {
            "Real Estate": "real estate agent OR realtor",
            "Insurance Agent": "insurance agent OR insurance broker",
            "Financial Advisor": "financial advisor OR financial planner",
            "Lawyer": "lawyer OR attorney OR law firm",
            "Doctor": "doctor OR physician OR medical practice",
            "Dentist": "dentist OR dental practice",
            "Accountant": "accountant OR CPA OR accounting firm",
            "Marketing Agency": "marketing agency OR digital marketing",
            "Home Services": "home services",
            "Health & Wellness": "health and wellness",
            "Automotive Services": "automotive services",
            "Professional Services": "professional services",
            "Health & Beauty": "health and beauty",
            "Restaurants & Food Services": "restaurants and food services",
            "Fitness & Sports": "fitness and sports",
            "Event & Entertainment Services": "event and entertainment services",
            "Education & Tutoring": "education and tutoring",
            "Pet Services": "pet services",
            "Retail & Local Shops": "retail and local shops",
            "Unique & Miscellaneous Local Businesses": "unique local businesses",
            "Celebrations & Parties": "celebrations and parties",
            "Weddings": "weddings",
            "Baby & Parenting Events": "baby and parenting events",
            "Graduations & Educational Milestones": "graduations and educational milestones"
        }
        
        col1, col2 = st.columns(2)
        
        with col1:
            selected_type = st.selectbox(
                "Select Business Type",
                options=list(business_types.keys())
            )
            
            location = st.text_input(
                "Location (City, State)",
                placeholder="e.g., Boston, MA"
            )
        
        with col2:
            radius = st.slider(
                "Search Radius (miles)",
                min_value=5,
                max_value=50,
                value=20
            )
            
            max_results = st.slider(
                "Maximum Results",
                min_value=5,
                max_value=100,
                value=25
            )
        
        if st.button("Generate Leads"):
            if not location or ',' not in location:
                st.error("Please enter location in City, State format")
                return
            
            try:
                with st.spinner("Generating leads..."):
                    # Generate leads
                    leads = processor.generator.generate_leads(
                        business_type=business_types[selected_type],
                        location=location,
                        radius=radius,
                        max_results=max_results
                    )
                
                if leads:
                    # Convert to DataFrame
                    leads_df = pd.DataFrame(leads)
                    
                    # Remove duplicates
                    leads_df = leads_df.drop_duplicates(subset=['company_name', 'Website'])
                    
                    st.write(f"Found {len(leads_df)} unique leads")
                    st.dataframe(leads_df)
                    
                    if st.button("Process Generated Leads"):
                        with st.spinner("Processing leads..."):
                            # Process leads with owner/email discovery
                            results_df = processor.process_leads(leads_df)
                        
                        st.success("Processing complete!")
                        st.write("Results with owner information:")
                        st.dataframe(results_df)
                        
                        # Prepare downloads
                        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
                        
                        # CSV download
                        csv = results_df.to_csv(index=False)
                        st.download_button(
                            label="📥 Download CSV",
                            data=csv,
                            file_name=f"generated_leads_{timestamp}.csv",
                            mime="text/csv"
                        )
                        
                        # Excel download
                        excel_data = processor.download_excel(results_df, f"processed_leads_{timestamp}.xlsx")
                        st.download_button(
                            label="📊 Download Excel",
                            data=excel_data,
                            file_name=f"processed_leads_{timestamp}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    
            except Exception as e:
                st.error(f"Error generating leads: {str(e)}")
                st.error(f"Error details:\n{traceback.format_exc()}")

if __name__ == "__main__":
    main()