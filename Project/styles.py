import streamlit as st

def get_dark_mode_css():
    """
    Returns the final, most forceful CSS string for the dark mode theme.
    This version uses !important to override any conflicting default styles.
    """
    return """
    <style>
        /* --- Page Background (Most Forceful Selector) --- */
        /* This targets the root element of the Streamlit app */
        #root > div:nth-child(1) > div > div > div > div {
            background-image: linear-gradient(135deg, #2d3436 0%, #1a1a1a 80%) !important;
            background-attachment: fixed !important;
            background-size: cover !important;
        }

        /* --- Default Text and Headers --- */
        /* Apply white color to all text elements */
        body, .st-emotion-cache-1r4qj8v, p, li, h1, h2, h3, h4, h5, h6, .st-emotion-cache-1kyxreq, .st-emotion-cache-1y4p8pa {
            color: #ffffff !important;
        }
        
        /* Ensure specific subheader text is also white */
        .st-emotion-cache-1629p8f h2, .st-emotion-cache-1629p8f h3 {
             color: #ffffff !important;
        }

        /* --- Card Styling --- */
        /* This selector is for the st.container(border=True) */
        [data-testid="stVerticalBlockBorderWrapper"] {
            background-color: rgba(255, 255, 255, 0.05) !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            border-radius: 15px !important;
        }
        
        /* Make sure text inside the cards is also visible */
        [data-testid="stVerticalBlockBorderWrapper"] p, [data-testid="stVerticalBlockBorderWrapper"] li {
            color: #e0e0e0 !important; /* Lighter grey for card descriptions */
        }
        
          /* --- Refined Text Styling --- */
        /* Instead of '*', target common text containers */
        .stApp, .stApp p, .stApp li, .stApp h1, .stApp h2, .st.App h3 {
            color: #ffffff; /* Set default text to white */
        }
        
               select, option {
            color: #ffffff !important;
            background-color: #2e2e2e !important;
        }

        /* Fix for dropdowns to remain white text when selected */
       /* Main dropdown container */
        [data-baseweb="select"] {
            color: black !important;
        }

        /* Dropdown menu options */
        [data-baseweb="popover"] [role="option"] {
            background-color: white !important;
            color: black !important;
        }

        /* Hovered item */
        [data-baseweb="popover"] [role="option"]:hover {
            background-color: #f0f0f0 !important;
            color: black !important;
        }

        /* Selected item tags */
        [data-baseweb="tag"] {
            background-color: #e0e0e0 !important;
            color: black !important;
        }

        /* Input field text */
        [data-baseweb="select"] input {
            color: black !important;
        }

        /* Placeholder text (like 'Choose an option') */
        [data-baseweb="select"] div[role="button"] {
            color: black !important;
        }
                /* --- Button Styling --- */

        /* General rule for all stButton containers */
        .stButton {
            display: flex;
            justify-content: center;
        }

        /* --- Forceful Selector for Form Submit Buttons --- */
        /* This targets the submit button within a form by chaining test IDs */
        /* Submit button inside form (🔵 blue theme) */
        div[data-testid="stForm"] div[data-testid="stFormSubmitButton"] button {
            border: 2px solid #1f77b4 !important; /* Blue border */
            background-color: transparent !important;
            color: #1f77b4 !important; /* Blue text */
            font-weight: bold !important;
            border-radius: 0.5rem !important;
            width: 100%;
        }
        div[data-testid="stForm"] div[data-testid="stFormSubmitButton"] button:hover {
            border-color: #1f77b4 !important;
            background-color: #1f77b4 !important;
            color: white !important;
        }
        div[data-testid="stForm"] div[data-testid="stFormSubmitButton"] button:focus {
            box-shadow: 0 0 0 0.2rem rgba(31, 119, 180, 0.5) !important;
        }

        /* Regular st.button outside of forms */
        div[data-testid="stButton"] button {
            background-color: transparent !important;
            color: #1f77b4 !important;
            font-weight: bold !important;
            border-radius: 0.5rem !important;
            border: 2px solid #1f77b4 !important;
        }
        div[data-testid="stButton"] button:hover {
            background-color: #1f77b4 !important;
            color: white !important;
        }

        /* --- TAB STYLING (Final, Most Forceful Version) --- */

        /* Style the text of the selected tab */
        button[data-baseweb="tab"][aria-selected="true"] p {
            color: #1f77b4 !important;  /* Blue text */
            font-weight: bold !important;
        }

        /* Blue indicator line under active tab */
        button[data-baseweb="tab"][aria-selected="true"] > div > div {
            background-color: #1f77b4 !important;  /* Blue line */
        }

    </style>
    """