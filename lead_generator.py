# lead_generator.py
import requests
import time
from typing import Dict, List
import streamlit as st
import os
from dotenv import load_dotenv
import json
from urllib.parse import quote

# lead_generator.py
class LeadGenerator:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("Missing Google API Key")
        self.api_key = api_key

        
    def generate_leads(self, business_type: str, location: str, radius: int = 20, max_results: int = 25) -> List[Dict]:
        """Generate leads using Google Places API"""
        try:
            leads = []
            next_page_token = None
            total_results = 0
            
            # Clean location
            location = location.strip()
            
            # Get location coordinates
            geocode_url = f"https://maps.googleapis.com/maps/api/geocode/json?address={quote(location)}&key={self.api_key}"
            geocode_response = requests.get(geocode_url)
            geocode_data = geocode_response.json()
            
            if geocode_data['status'] != 'OK':
                raise ValueError(f"Could not geocode location: {location}")
            
            # Extract coordinates
            lat = geocode_data['results'][0]['geometry']['location']['lat']
            lng = geocode_data['results'][0]['geometry']['location']['lng']
            
            while total_results < max_results:
                # Prepare Places API request
                url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
                params = {
                    'location': f"{lat},{lng}",
                    'radius': radius * 1609.34,  # Convert miles to meters
                    'keyword': business_type,
                    'key': self.api_key
                }
                
                if next_page_token:
                    params['pagetoken'] = next_page_token
                    time.sleep(2)  # Required delay for next page token
                
                # Make request
                response = requests.get(url, params=params)
                data = response.json()
                
                if data['status'] != 'OK':
                    break
                
                # Process results
                for place in data['results']:
                    if total_results >= max_results:
                        break
                    
                    # Get place details
                    details_url = f"https://maps.googleapis.com/maps/api/place/details/json"
                    details_params = {
                        'place_id': place['place_id'],
                        'fields': 'name,formatted_address,formatted_phone_number,website',
                        'key': self.api_key
                    }
                    
                    details_response = requests.get(details_url, params=details_params)
                    details_data = details_response.json()
                    
                    if details_data['status'] == 'OK':
                        result = details_data['result']
                        
                        lead = {
                            'company_name': result.get('name', ''),
                            'full_address': result.get('formatted_address', ''),
                            'Phone': result.get('formatted_phone_number', 'N/A'),
                            'Website': result.get('website', 'N/A')
                        }
                        
                        leads.append(lead)
                        total_results += 1
                        
                        # Show progress
                        st.write(f"Found: {lead['company_name']}")
                    
                    time.sleep(0.5)  # Rate limiting
                
                next_page_token = data.get('next_page_token')
                if not next_page_token:
                    break
            
            return leads
            
        except Exception as e:
            st.error(f"Error generating leads: {str(e)}")
            return []
