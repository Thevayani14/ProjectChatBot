import streamlit as st
from streamlit_calendar import calendar
from database import get_calendar_events, save_calendar_events, delete_calendar_event
from streamlit.components.v1 import html

def calendar_page():
    """
    Displays a full-screen, interactive calendar using robust session_state for callbacks.
    """
    st.set_page_config(layout="wide")

    # --- Initialize session state for the action ---
    if "calendar_action" not in st.session_state:
        st.session_state.calendar_action = None

    # --- JAVASCRIPT FOR SETTING SESSION STATE ---
    # This JS does not return a value. It sends a message to Streamlit to set a session state key.
    js_code = """
    <script>
    // This is the new, robust communication method
    function sendActionToStreamlit(action) {
        const componentValue = {
            type: "SET_SESSION_STATE",
            key: "calendar_action",
            value: action
        };
        window.parent.postMessage({
            isStreamlitMessage: true,
            type: "SET_COMPONENT_VALUE",
            data: {
                componentId: "streamlit-calendar-component", // This can be any unique ID
                componentValue: componentValue
            }
        }, "*");
    }
    
    // We add listeners to the window to capture the calendar's internal messages
    window.addEventListener('message', function(event) {
        if (event.data.type === 'calendar_event_click') {
            sendActionToStreamlit({type: 'eventClick', data: event.data.event});
        }
        if (event.data.type === 'calendar_date_select') {
            sendActionToStreamlit({type: 'dateSelect', data: event.data.selection});
        }
    }, false);
    </script>
    """
    # Inject the script. We don't care about its return value.
    html(js_code, height=0)

    # --- PAGE HEADER AND NAVIGATION ---
    st.title("📅 My Calendar & Notes")
    if st.button("⬅️ Back to Dashboard"):
        st.session_state.page = "homepage"
        st.set_page_config(layout="centered")
        st.session_state.calendar_action = None # Reset action on navigation
        st.rerun()
    st.markdown("---")

    # --- TWO-COLUMN LAYOUT ---
    left_col, right_col = st.columns([0.65, 0.35])

    # --- LEFT COLUMN: THE CALENDAR ---
    with left_col:
        events = get_calendar_events(st.session_state.user_id)
        
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
            # The JS functions now trigger the new communication method
            "eventClick": "function(info) { window.postMessage({type: 'calendar_event_click', event: {id: info.event.id, title: info.event.title}}, '*'); }",
            "select": "function(info) { window.postMessage({type: 'calendar_date_select', selection: {start: info.startStr, end: info.endStr}}, '*'); }",
        }
        
        calendar(events=events, options=calendar_options, key="full_calendar_component")

    # --- RIGHT COLUMN: MANAGEMENT PANEL ---
    with right_col:
        st.subheader("Manage Events")
        
        # We now check our session state variable directly
        action = st.session_state.calendar_action
        
        if action:
            event_type = action.get("type")
            data = action.get("data", {})

            if event_type == "eventClick":
                st.info(f"Selected Event: **{data['title']}**")
                if st.button(f"Delete this event", key=f"delete_full_{data['id']}", type="primary", use_container_width=True):
                    if delete_calendar_event(int(data['id'])):
                        st.toast("Event deleted!")
                        st.session_state.calendar_action = None # Reset the action
                        st.rerun()
                    else:
                        st.error("Failed to delete event.")

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
                            st.session_state.calendar_action = None # Reset the action
                            st.rerun()
                        else:
                            st.error("Failed to add note.")
        
        # Default message
        if not action:
            st.info("Click on a day in the calendar to add a new note, or click on an existing event to manage it.")
