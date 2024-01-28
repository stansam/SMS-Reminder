from flask import Flask, request
import africastalking
import threading
import time

app = Flask(__name__)

# Set your Africa's Talking API key and username
api_key = 'your_api_key'
username = 'your_username'

# Initialize the Africa's Talking SDK
africastalking.initialize(username, api_key)

# Initialize the USSD service
ussd = africastalking.USSD

# Dictionary to store user input
user_data = {}

# Dictionary to store scheduled reminders
scheduled_reminders = {}

# Define the USSD callback endpoint
@app.route('/ussd/callback', methods=['POST'])
def ussd_callback():
    session_id = request.form['sessionId']
    text = request.form['text']

    # Implement logic to handle USSD session based on the user's input
    if text == '':
        response = "CON Welcome to Reminder App. Enter your task:"
    elif 'CON' in text:
        # User is still entering data
        response = handle_user_input(session_id, text)
    else:
        # User has finished entering data
        response = "END Task set. You will receive a reminder."

    return response

def handle_user_input(session_id, text):
    parts = text.split('*')

    if len(parts) == 1:
        # User is entering the task
        user_data[session_id] = {'task': text}
        return "CON Enter the time for the reminder (e.g., 10.00pm):"

    elif len(parts) == 2:
        # User is entering the time
        user_data[session_id]['time'] = text
        return "CON Enter your phone number:"

    elif len(parts) == 3:
        # User is entering the phone number
        user_data[session_id]['phone_number'] = text

        # Prompt the user for confirmation and display entered details
        confirmation_message = (
            f"CON Confirm:\n"
            f"Task: {user_data[session_id]['task']}\n"
            f"Time: {user_data[session_id]['time']}\n"
            f"Phone Number: {user_data[session_id]['phone_number']}\n"
            "1. Confirm\n"
            "2. Cancel"
        )
        return confirmation_message

    elif len(parts) == 4:
        # User confirms or cancels
        if text == '1':
            # Schedule the task to be executed at the specified time
            schedule_time = user_data[session_id]['time']
            schedule_reminder(session_id, schedule_time)
            
            return "END Reminder set successfully."
        elif text == '2':
            # User cancels the operation
            return "END Operation canceled."
        else:
            # Invalid input, prompt again
            return "CON Invalid input. Please choose 1 to confirm or 2 to cancel."

    else:
        # Use Africa's Talking USSD API to send response
        send_ussd_response(session_id, "END Invalid input. Please try again.")
        return "END Invalid input. Please try again."

def schedule_reminder(session_id, schedule_time):
    # Parse the schedule time and convert it to seconds since epoch
    scheduled_time_seconds = parse_schedule_time(schedule_time)

    # Get the current time in seconds since epoch
    current_time_seconds = int(time.time())

    # Calculate the delay in seconds
    delay_seconds = scheduled_time_seconds - current_time_seconds

    # Schedule the reminder using threading.Timer
    reminder_thread = threading.Timer(delay_seconds, send_reminder, args=[session_id])
    reminder_thread.start()

    # Store the scheduled reminder thread in the dictionary
    scheduled_reminders[session_id] = reminder_thread

def parse_schedule_time(schedule_time):
    # Implement parsing logic based on your time format (e.g., '10.00pm')
    # This is a placeholder, you might need to adjust based on your time format
    # Example: '10.00pm' => ('10', '00', 'pm')
    hours, minutes, period = schedule_time[:-2], schedule_time[-4:-2], schedule_time[-2:]

    # Convert to 24-hour format
    if period.lower() == 'pm' and hours != '12':
        hours = str(int(hours) + 12)

    # Get the current time in struct_time format
    current_time_struct = time.localtime()

    # Create a struct_time for the scheduled time
    scheduled_time_struct = time.struct_time(
        current_time_struct.tm_year,
        current_time_struct.tm_mon,
        current_time_struct.tm_mday,
        int(hours),
        int(minutes),
        0,  # seconds
        current_time_struct.tm_wday,
        current_time_struct.tm_yday,
        current_time_struct.tm_isdst
    )

    # Convert struct_time to seconds since epoch
    scheduled_time_seconds = int(time.mktime(scheduled_time_struct))
    
    return scheduled_time_seconds

def send_reminder(session_id):
    try:
        # Use Africa's Talking SMS API to send reminder
        reminder_message = f"Reminder: {user_data[session_id]['task']}"
        send_ussd_response(session_id, f"END {reminder_message}")
        print(f"Reminder USSD sent: {reminder_message}")
    except Exception as e:
        print(f"Error sending reminder USSD: {e}")

def send_ussd_response(session_id, message):
    try:
        # Use Africa's Talking USSD API to send response
        ussd.send(message, session_id)
        print(f"USSD Response sent: {message}")
    except Exception as e:
        print(f"Error sending USSD response: {e}")

if __name__ == '__main__':
    app.run(port=3000)
