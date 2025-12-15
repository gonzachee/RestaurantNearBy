import streamlit as st
import requests
from streamlit_js_eval import get_geolocation

# --- CONFIGURATION ---
st.set_page_config(page_title="Jom Makan - Malaysia Food Finder", page_icon="🍽️", layout="wide")

# 🔑 PASTE YOUR GOOGLE API KEY BELOW
GOOGLE_API_KEY = "AIzaSyDdc9qS9184Heyctow0f5GzPg4TYbKFhKQ"

# --- CUSTOM CSS FOR MOBILE FRIENDLY CARDS ---
st.markdown("""
    <style>
    .restaurant-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border-left: 6px solid #ff4b4b;
    }
    .restaurant-card h3 {
        margin: 0 0 10px 0;
        color: #333;
    }
    .rating-badge {
        background-color: #e6f4ea;
        color: #137333;
        padding: 5px 10px;
        border-radius: 15px;
        font-weight: bold;
        font-size: 0.9em;
    }
    .btn-waze {
        background-color: #FECE31;
        color: black;
        border: none;
        padding: 10px 20px;
        border-radius: 8px;
        font-weight: bold;
        cursor: pointer;
        text-decoration: none;
        display: inline-block;
    }
    .btn-google {
        background-color: #4285F4;
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 8px;
        font-weight: bold;
        cursor: pointer;
        text-decoration: none;
        display: inline-block;
        margin-right: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- HEADER ---
st.title("🍽️ Jom Makan Nearby")
st.markdown("For travelers & sales teams: Find **Open** & **High Rated** food spots instantly.")

# --- SIDEBAR: SEARCH SETTINGS ---
with st.sidebar:
    st.header("Search Settings")
    
    search_type = st.selectbox(
        "Looking for?",
        ["Restaurant", "Cafe", "Mamak", "Kopitiam", "Hawker Center"]
    )

    # Specific Cuisine Filters
    cuisine_type = "All"
    if search_type in ["Restaurant", "Cafe"]:
        cuisine_type = st.radio(
            "Cuisine / Type:",
            ["All", "Malay", "Chinese", "Indian", "Halal", "Western", "Thai"],
            index=0
        )

    radius_km = st.slider("Distance (KM)", 1, 10, 5)

# --- GPS LOGIC ---
st.info("📍 Attempting to get your GPS location... Please 'Allow' if asked.")
loc = get_geolocation()

# Default to KLCC if GPS fails (for testing)
user_lat, user_lon = 3.1579, 101.7116 
gps_available = False

if loc:
    user_lat = loc['coords']['latitude']
    user_lon = loc['coords']['longitude']
    gps_available = True
    st.success(f"✅ Location Found: {user_lat:.4f}, {user_lon:.4f}")
else:
    st.warning("⚠️ GPS not detected yet. Using Default Location (KLCC) for demo.")

st.divider()

# --- FUNCTION: GOOGLE PLACES SEARCH ---
def search_google_maps(lat, lon, radius, keyword, category):
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    
    # 1. Build the search term (e.g., "Malay Restaurant")
    final_keyword = keyword
    if category != "All":
        final_keyword = f"{category} {keyword}"
    
    # 2. Map 'Mamak' explicitly because Google understands it well in Malaysia
    search_type_api = final_keyword.lower()
    
    params = {
        "location": f"{lat},{lon}",
        "radius": radius * 1000, 
        "keyword": search_type_api,
        "type": "restaurant",
        "opennow": "true", # Crucial for travelers!
        "key": GOOGLE_API_KEY
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        # DEBUG: Check for API errors (Billing, Quota, etc)
        if data.get('status') != "OK" and data.get('status') != "ZERO_RESULTS":
            st.error(f"⚠️ API Error: {data.get('status')}")
            st.error(f"Details: {data.get('error_message')}")
            return []
            
        return data.get('results', [])
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return []

# --- MAIN UI ---
if st.button("🔍 Find Food Nearby", type="primary"):
    
    if "YOUR_GOOGLE_API" in GOOGLE_API_KEY:
        st.error("🚨 Stop! You forgot to paste your Google API Key in the code.")
    else:
        with st.spinner("Searching for the best spots..."):
            results = search_google_maps(user_lat, user_lon, radius_km, search_type, cuisine_type)
            
            # Filter: Only show places with valid ratings (e.g. 3.5+)
            # Note: Some new places have 0 rating, we keep them if you want
            valid_results = [r for r in results if r.get('rating', 0) >= 3.0]
            
            if not valid_results:
                st.warning(f"No open places found for **{cuisine_type} {search_type}** within {radius_km}km.")
                st.write("Tip: Try increasing the distance or selecting 'All' cuisines.")
            else:
                st.write(f"Found **{len(valid_results)}** places:")
                
                for place in valid_results:
                    name = place.get('name')
                    rating = place.get('rating', 'N/A')
                    total_ratings = place.get('user_ratings_total', 0)
                    address = place.get('vicinity', 'No address')
                    
                    place_lat = place['geometry']['location']['lat']
                    place_lng = place['geometry']['location']['lng']
                    
                    # Links
                    waze_url = f"https://waze.com/ul?ll={place_lat},{place_lng}&navigate=yes"
                    google_url = f"https://www.google.com/maps/search/?api=1&query={place_lat},{place_lng}&query_place_id={place.get('place_id')}"

                    # Render Card using HTML
                    st.markdown(f"""
                    <div class="restaurant-card">
                        <div style="display:flex; justify-content:space-between;">
                            <h3>{name}</h3>
                            <span class="rating-badge">⭐ {rating} ({total_ratings})</span>
                        </div>
                        <p style="color:#666; margin-bottom:15px;">📍 {address}</p>
                        <a href="{google_url}" target="_blank" class="btn-google">🗺️ Maps</a>
                        <a href="{waze_url}" target="_blank" class="btn-waze">🚗 Waze</a>
                    </div>
                    """, unsafe_allow_html=True)
