import os
import csv
from datetime import datetime
from flask import Flask, request, render_template
from user_agents import parse

app = Flask(__name__)

# Configuration
LOG_FILE = 'visit_log.csv'
# **** ADDED NEW FIELDS TO HEADER ****
LOG_HEADER = [
    'Timestamp', 'IP Address',
    'Is Bot', 'Is Mobile', 'Is Tablet', 'Is PC', 'Is Touch Capable',
    'Browser Family', 'Browser Version',
    'OS Family', 'OS Version',
    'Device Family', 'Device Brand', 'Device Model',
    'Accept Language', 'Do Not Track',
    'User Agent String'
]

# --- Helper Functions ---

def get_client_ip():
    """Gets the client's IP address, considering proxies."""
    if request.headers.getlist("X-Forwarded-For"):
       ip = request.headers.getlist("X-Forwarded-For")[0].strip()
    elif request.headers.get("X-Real-IP"):
        ip = request.headers.get("X-Real-IP").strip()
    else:
       ip = request.remote_addr
    return ip

def log_visit(data):
    """Appends visit data to the CSV log file."""
    file_exists = os.path.isfile(LOG_FILE)
    # Ensure all header fields are present in the data, even if None
    log_entry = {field: data.get(field, None) for field in LOG_HEADER}
    try:
        with open(LOG_FILE, 'a', newline='', encoding='utf-8') as csvfile:
            # Use the full LOG_HEADER for the writer
            writer = csv.DictWriter(csvfile, fieldnames=LOG_HEADER)
            if not file_exists or os.path.getsize(LOG_FILE) == 0:
                writer.writeheader()
            writer.writerow(log_entry) # Write the prepared log_entry
    except IOError as e:
        print(f"Error writing to log file {LOG_FILE}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during logging: {e}")


# --- Routes ---

@app.route('/')
def index():
    # 1. Get IP Address
    ip_address = get_client_ip()

    # 2. Get User Agent String and Other Headers
    ua_string = request.headers.get('User-Agent', 'Unknown')
    accept_language = request.headers.get('Accept-Language')
    dnt_header = request.headers.get('DNT') # Do Not Track (usually '1' if enabled)

    # 3. Parse User Agent
    user_agent = parse(ua_string)

    # 4. Get Timestamp
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')

    # 5. Prepare data for logging and display
    # **** ADDED NEW FIELDS TO DATA ****
    visit_data = {
        'Timestamp': timestamp,
        'IP Address': ip_address,

        # User Agent Derived
        'Is Bot': user_agent.is_bot,
        'Is Mobile': user_agent.is_mobile,
        'Is Tablet': user_agent.is_tablet,
        'Is PC': user_agent.is_pc,
        'Is Touch Capable': user_agent.is_touch_capable,
        'Browser Family': user_agent.browser.family,
        'Browser Version': user_agent.browser.version_string,
        'OS Family': user_agent.os.family,
        'OS Version': user_agent.os.version_string,
        'Device Family': user_agent.device.family,
        'Device Brand': user_agent.device.brand,
        'Device Model': user_agent.device.model,
        'User Agent String': ua_string,

        # Other Headers
        'Accept Language': accept_language,
        'Do Not Track': dnt_header,
    }

    # 6. Log the visit (append to CSV)
    log_visit(visit_data)

    # 7. Render a template to show the user *their* info
    return render_template('index.html', data=visit_data)

# --- Run the App ---

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) # Remember debug=False for production