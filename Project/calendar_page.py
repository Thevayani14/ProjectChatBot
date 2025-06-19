import streamlit as st
from streamlit_calendar import calendar
from database import get_calendar_events, save_calendar_events, delete_calendar_event
from streamlit.components.v1 import html

def calendar_page():
    """
    Displays a full-screen, interactive calendar using robust JavaScript callbacks for state management.
    """
    st.set_page_config(layout="wide")

    # --- JAVASCRIPT FOR ROBUST CALLBACKS ---
    # This JS code will be injected into the page. When an event happens on the calendar,
    # this code communicates directly with Streamlit's session state.
    js_code = """
    <script>
    // Function to send data back to Streamlit
    function sendToStreamlit(type, data) {
        const streamlit_data = {
            "type": type,
            "data": data
        };
        window.parent.postMessage({
            "type": "streamlit:setComponentValue",
            "key": "calendar_callback", // This must match the key of the html component
            "value": streamlit_data
        }, "*");
    }

    // Add event listeners to the parent window to capture calendar actions
    window.parent.addEventListener('message', function(event) {
        if (event.data.type === 'calendar_event_click') {
            sendToStreamlit('eventClick', event.data.event);
        }
        if (event.data.type === 'calendar_date_select') {
            sendToStreamlit('dateSelect', event.data.selection);
        }
    }, false);
    </script>
    """
    
    # We use st.html to inject the JS. Its return value is our reliable state.
    calendar_callback_data = html(f"<div id='calendar-callback-container'>{js_code}</div>", height=0)

    # --- PAGE HEADER AND NAVIGATION ---
    st.title("📅 My Calendar & Notes")
    if st.button("⬅️ Back to Dashboard"):
        st.session_state.page = "homepage"
        st.set_page_config(layout="centered")
        st.rerun()
    st.markdown("---")

    # --- TWO-COLUMN LAYOUT ---
    left_col, right_col = st.columns([0.65, 0.35])

    # --- LEFT COLUMN: THE CALENDAR ITSELF ---
    with left_col:
        events = get_calendar_events(st.session_state.user_id)
        
        # --- MODIFIED CALENDAR OPTIONS ---
        # We now define JS functions to be called on events instead of relying on the return value.
        calendar_options = {
            "editable": False,
            "selectable": True,
            "headerToolbar": {
                "left": "today prev,next",
                "center": "title",
                "right": "dayGridMonth,timeGridWeek,listWeek"
            },
            "initialView": "dayGridMonth",
            "height": "auto",
            # When an event is clicked, run this JS function
            "eventClick": "function(info) { window.parent.postMessage({type: 'calendar_event_click', event: {id: info.event.id, title: info.event.title}}, '*'); }",
            # When a date is selected, run this JS function
            "select": "function(info) { window.parent.postMessage({type: 'calendar_date_select', selection: {start: info.startStr, end: info.endStr}}, '*'); }",
        }
        
        calendar(events=events, options=calendar_options, key="full_calendar_component")

    # --- RIGHT COLUMN: THE MANAGEMENT PANEL ---
    with right_col:
        st.subheader("Manage Events")
        
        # We now use the state from our JS callback component
        if calendar_callback_data:
            event_type = calendar_callback_data.get("type")
            data = calendar_callback_data.get("data", {})

            # Case 1: An event was clicked
            if event_type == "eventClick":
                st.info(f"Selected Event: **{data['title']}**")
                if st.button(f"Delete this event", key=f"delete_full_{data['id']}", type="primary", use_container_width=True):
                    if delete_calendar_event(int(data['id'])):
                        st.toast("Event deleted!")
                        st.rerun()
                    else:
                        st.error("Failed to delete event.")

            # Case 2: A date was selected
            elif event_type == "dateSelect":
                start_date_str = data["start"].split("T")[0]
                with st.form(key="add_event_form_full"):
                    st.write(f"**Add a new note for {start_date_str}**")
                    event_title = st.text_input("Note / Event Title:")
                    submitted = st.form_submit_button("Add to Calendar")
                    if submitted and event_title:
                        new_event = {
                            "title": event_title,
                            "start": start_date_str,
                            "end": start_date_str,
                            "color": "#6f42c1"
                        }
                        if save_calendar_events(st.session_state.user_id, [new_event], is_generated=False):
                            st.toast("Note added!")
                            st.rerun()
                        else:
                            st.error("Failed to add note.")
        else:
            st.info("Click on a day in the calendar to add a new note, or click on an existing event to manage it.")
