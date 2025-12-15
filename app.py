import streamlit as st
import requests
import pandas as pd
from streamlit_js_eval import get_geolocation

# --- CONFIGURATION ---
# REPLACE THIS WITH YOUR ACTUAL GOOGLE API KEY
GOOGLE_API_KEY = "AIzaSyDdc9qS9184Heyctow0f5GzPg4TYbKFhKQ"

st.set_page_config(page_title="Jom Makan - Malaysia Food Finder", page_icon="🍽️")

# --- CUSTOM CSS FOR MOBILE FRIENDLY LOOK ---
st.markdown("""
    <style>
    .restaurant-card {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 10px;
        border-left: 5px solid #ff4b4b;
    }
    .status-open { color: green; font-weight: bold; }
    .status-closed { color: red; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- HEADER ---
st.title("🍽️ Jom Makan Nearby")
st.write("Find the best **Halal / Malay / Chinese / Indian** food near you.")

# --- STEP 1: GET GPS LOCATION ---
loc = get_geolocation()

if loc:
    user_lat = loc['coords']['latitude']
    user_lon = loc['coords']['longitude']
    st.success(f"📍 Location Found: {user_lat:.4f}, {user_lon:.4f}")
else:
    st.warning("⚠️ Waiting for GPS... (Allow location access in browser)")
    # Default to KLCC for demo purposes if no GPS yet
    user_lat, user_lon = 3.1579, 101.7116 

st.divider()

# --- STEP 2: USER PREFERENCES ---
col1, col2 = st.columns(2)

with col1:
    search_type = st.selectbox(
        "Looking for?",
        ["Restaurant", "Cafe", "Mamak", "Hotel", "Tourist Attraction"]
    )

with col2:
    radius_km = st.selectbox(
        "Distance (KM)",
        [1, 3, 5, 10]
    )

# Specific Malaysia Food Categories
food_category = "All"
if search_type in ["Restaurant", "Cafe", "Mamak"]:
    food_category = st.radio(
        "Cuisine Type:",
        ["All", "Malay", "Chinese", "Indian", "Halal", "Western"],
        horizontal=True
    )

# --- STEP 3: SEARCH LOGIC ---
def search_google_maps(lat, lon, radius, keyword, category):
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    
    # Construct the search query
    search_term = keyword
    if category != "All" and keyword in ["Restaurant", "Cafe", "Mamak"]:
        search_term = f"{category} {keyword}"
    
    params = {
        "location": f"{lat},{lon}",
        "radius": radius * 1000, # Convert km to meters
        "keyword": search_term,
        "type": "restaurant" if keyword == "Mamak" else keyword.lower(), # Map keywords to API types
        "opennow": "true", # Only show open places
        "minprice": 0,
        "key": GOOGLE_API_KEY
    }
    
    try:
        response = requests.get(url, params=params)
        return response.json().get('results', [])
    except Exception as e:
        st.error(f"Error connecting to Maps: {e}")
        return []

# --- STEP 4: DISPLAY RESULTS ---
if st.button("🔍 Search Nearby"):
    if GOOGLE_API_KEY == "YOUR_GOOGLE_API_KEY_HERE":
        st.error("🚨 Please put your Google API Key in the code first!")
    else:
        with st.spinner(f"Searching for {food_category if food_category != 'All' else ''} {search_type}..."):
            results = search_google_maps(user_lat, user_lon, radius_km, search_type, food_category)
            
            # Filter for Rating > 3.0
            results = [r for r in results if r.get('rating', 0) >= 3.0]
            
            if not results:
                st.warning("No open places found matching your criteria nearby.")
            else:
                st.write(f"Found **{len(results)}** places:")
                
                for place in results:
                    name = place.get('name')
                    rating = place.get('rating', 'N/A')
                    user_ratings = place.get('user_ratings_total', 0)
                    vicinity = place.get('vicinity')
                    place_lat = place['geometry']['location']['lat']
                    place_lng = place['geometry']['location']['lng']
                    
                    # Create clickable Google Maps and Waze Links
                    gmaps_link = f"https://www.google.com/maps/dir/?api=1&destination={place_lat},{place_lng}"
                    waze_link = f"https://waze.com/ul?ll={place_lat},{place_lng}&navigate=yes"
                    
                    # Render Card
                    st.markdown(f"""
                    <div class="restaurant-card">
                        <h3>{name}</h3>
                        <p>⭐ <b>{rating}</b> ({user_ratings} reviews)</p>
                        <p style="color:gray; font-size:0.9em;">{vicinity}</p>
                        <a href="{gmaps_link}" target="_blank" style="text-decoration:none;">
                            <button style="background-color:#4285F4; color:white; border:none; padding:8px 15px; border-radius:5px; cursor:pointer;">🗺️ Google Maps</button>
                        </a>
                        <a href="{waze_link}" target="_blank" style="text-decoration:none;">
                            <button style="background-color:#FECE31; color:black; border:none; padding:8px 15px; border-radius:5px; cursor:pointer; margin-left:10px;">🚗 Waze</button>
                        </a>
                    </div>
                    """, unsafe_allow_html=True)
