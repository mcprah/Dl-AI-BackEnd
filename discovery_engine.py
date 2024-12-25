import requests
from flask import Blueprint, jsonify, request
from utils import get_access_token
from datetime import datetime
import mysql.connector
import re
import json
import os
from bs4 import BeautifulSoup
from google.cloud import storage  # For uploading to Google Cloud Storage

discovery_bp = Blueprint('discovery', __name__)

# Start a new chat and create a new session
@discovery_bp.route('/start', methods=['POST'])
def query_discovery_engine():
    access_token = get_access_token()
    if not access_token:
        return jsonify({'message': 'Failed to obtain access token'}), 401

    # Extract the userPseudoId from the request body
    data = request.get_json()
    user_pseudo_id = data.get('userPseudoId', '')

    if not user_pseudo_id:
        return jsonify({'message': 'UserPseudoId is required'}), 400

    # Define the payload for the Discovery Engine API request
    payload = {
        "userPseudoId": user_pseudo_id
    }

    url = "https://discoveryengine.googleapis.com/v1alpha/projects/615425956737/locations/global/collections/default_collection/dataStores/dennislaw_1725932647753/sessions"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # Make the POST request to the Discovery Engine API
    response = requests.post(url, headers=headers, json=payload)
    response_data = response.json()

    # Print the response data for debugging
    print(response_data)

    # Return the response data to the frontend
    return jsonify(response_data), response.status_code

#--------------------------------------------------------------------------------------------------------
#Ask a question and add to session 
@discovery_bp.route('/chat', methods=['POST'])
def query_discovery_engine_chat():
    access_token = get_access_token()
    if not access_token:
        return jsonify({'message': 'Failed to obtain access token'}), 401

    # Extract the query from the request body
    data = request.get_json()
    query = data.get('query', '')
    session_id = data.get('session_id', '')

    # Define the payload for the Discovery Engine API request
    payload = {
        "query": { "text": query},
        "session": session_id,
        "searchSpec":{ "searchParams": {"filter": ""} }
    }

    url = "https://discoveryengine.googleapis.com/v1alpha/projects/615425956737/locations/global/collections/default_collection/dataStores/dennislaw_1725932647753/servingConfigs/default_search:answer"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # Make the POST request to the Discovery Engine API
    response = requests.post(url, headers=headers, json=payload, timeout=60)

    # Return the response from the Discovery Engine API to the client
    return jsonify(response.json()), response.status_code
#--------------------------------------------------------------------------------------------------------

# Get all Sessions of a User
@discovery_bp.route('/sessions/', methods=['GET'])
def query_discovery_engine_sessions():
    
    access_token = get_access_token()
    if not access_token:
        return jsonify({'message': 'Failed to obtain access token'}), 401
    
    # Extract the userPseudoId from the request query parameters
    user_pseudo_id = request.args.get('userPseudoId', '')

    if not user_pseudo_id:
        return jsonify({'message': 'UserPseudoId is required'}), 400

    url = f"https://discoveryengine.googleapis.com/v1alpha/projects/615425956737/locations/global/collections/default_collection/dataStores/dennislaw_1725932647753/sessions?filter=userPseudoId={user_pseudo_id}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # Make the GET request to the Discovery Engine API to get the sessions
    response = requests.get(url, headers=headers)
    sessions = response.json().get('sessions', [])

    # Loop through each session and fetch the answer details for each turn
    for session in sessions:
        for turn in session.get('turns', []):
            answer_ref = turn.get('answer', '')
            if answer_ref:
                # Make an API request to fetch the answer details
                answer_url = f"https://discoveryengine.googleapis.com/v1alpha/{answer_ref}"
                answer_response = requests.get(answer_url, headers=headers)
                answer_data = answer_response.json()

                # Add the answer text or relevant fields to the turn
                turn['answerDetails'] = answer_data

    # Return the sessions with detailed answer information
    return jsonify(sessions), response.status_code

#--------------------------------------------------------------------------------------------------------
#Get a Session of a User
@discovery_bp.route('/session/', methods=['GET'])
def query_discovery_engine_session():
    
    access_token = get_access_token()
    if not access_token:
        return jsonify({'message': 'Failed to obtain access token'}), 401

    # Extract the session name from the request query parameters
    name = request.args.get('name', '')

    if not name:
        return jsonify({'message': 'Name is required'}), 400

    # Update the session state before retrieving it
    update_url = f"https://discoveryengine.googleapis.com/v1alpha/projects/615425956737/locations/global/collections/default_collection/dataStores/dennislaw_1725932647753/sessions/{name}?updateMask=state"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # Example of updating the state to "VIEWED" or another relevant state
    patch_data = {
        "state": "IN_PROGRESS"  # Update to the desired state
    }

    # Make the PATCH request to update the session state
    patch_response = requests.patch(update_url, headers=headers, json=patch_data)

    if patch_response.status_code != 200:
        return jsonify({'message': 'Failed to update session state', 'error': patch_response.json()}), patch_response.status_code

    # After updating, retrieve the session data
    session_url = f"https://discoveryengine.googleapis.com/v1alpha/projects/615425956737/locations/global/collections/default_collection/dataStores/dennislaw_1725932647753/sessions/{name}"
    response = requests.get(session_url, headers=headers)
    session = response.json()

    # Fetch the answer details for each turn in the session
    for turn in session.get('turns', []):
        answer_ref = turn.get('answer', '')
        if answer_ref:
            # Make an API request to fetch the answer details
            answer_url = f"https://discoveryengine.googleapis.com/v1alpha/{answer_ref}"
            answer_response = requests.get(answer_url, headers=headers)
            answer_data = answer_response.json()

            # Add the answer text or relevant fields to the turn
            turn['answerDetails'] = answer_data

    # Return the session with detailed answer information
    return jsonify(session), response.status_code




# Delete a Sessions of a User
@discovery_bp.route('/delete/', methods=['DELETE'])
def query_discovery_engine_delete():
    
    access_token = get_access_token()
    if not access_token:
        return jsonify({'message': 'Failed to obtain access token'}), 401
    
    # Extract the session id from the request query parameters
    id = request.args.get('id', '')

    if not id:
        return jsonify({'message': 'Session Id is required'}), 400

    url = f"https://discoveryengine.googleapis.com/v1alpha/{id}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # Make the DELETE request to the Discovery Engine API to delete the session
    response = requests.delete(url, headers=headers)
    
    # Return the response status from the deletion attempt
    if response.status_code == 200:
        return jsonify({'message': 'Session deleted successfully'}), 200
    else:
        return jsonify({'message': 'Failed to delete session'}), response.status_code
    
#---------------------------------------------------------------------------------------------------------------

# Function to upload a file to an existing Google Cloud Storage bucket using access token
def upload_to_bucket(blob_name, file_path, bucket_name, access_token):
    """Uploads a file to the specified bucket using an OAuth 2.0 access token."""

    # Define the upload URL for Google Cloud Storage
    upload_url = f"https://storage.googleapis.com/upload/storage/v1/b/{bucket_name}/o?uploadType=media&name={blob_name}"

    # Set the headers, including the OAuth 2.0 authorization token
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/octet-stream"
    }

    # Open the file and upload its contents
    with open(file_path, 'rb') as file_data:
        response = requests.post(upload_url, headers=headers, data=file_data)

    if response.status_code == 200:
        # Optionally delete the local file after uploading
        os.remove(file_path)
        return response.json().get('mediaLink')  # Return the public URL or media link of the file

    raise Exception(f"Failed to upload file: {response.text}")

# Main route to handle reported cases
@discovery_bp.route('/reported', methods=['POST'])
def upload_reported_cases():
    messages = []
    try:
        data = request.get_json()

        # Extract MySQL connection data and row limit from the request body
        host = data.get('host')
        database = data.get('database')
        user = data.get('user')
        password = data.get('password')
        
        # Safely handle 'num_rows_to_convert' and default to all rows if empty or invalid
        num_rows_to_convert = data.get('num_rows_to_convert')
        if not num_rows_to_convert or not num_rows_to_convert.isdigit():
            num_rows_to_convert = None
        else:
            num_rows_to_convert = int(num_rows_to_convert)

        # Connect to the MySQL database
        db_connection = mysql.connector.connect(
            host=host,
            database=database,
            user=user,
            password=password
        )

        messages.append("Connection successful. Database ready.")
        cursor = db_connection.cursor()

        # Run query
        query = "SELECT * FROM reported_cases"
        messages.append(f"Running query: {query}. Please wait...")
        cursor.execute(query)
        rows = cursor.fetchall()
        total_rows = len(rows)

        messages.append(f"Table 'reported_cases' accessed successfully. Total rows: {total_rows}")

        # If num_rows_to_convert is None or greater than the total rows, take all rows
        if num_rows_to_convert is None or num_rows_to_convert > total_rows:
            num_rows_to_convert = total_rows

        # Define a function to clean the data
        def clean_text(text):
            if text is None or text in ["", "-", "----", "------------"]:
                return ""
            
            # Ensure the input is a string
            if not isinstance(text, str):
                return ""
            
            # Ignore URLs
            if re.match(r'^https?://', text):
                return text

            # Remove HTML tags
            text = BeautifulSoup(text, "html.parser").get_text()
            
            # Remove unwanted characters
            text = re.sub(r'\r\n|\r|\n', ' ', text)
            text = re.sub(r'\s+', ' ', text)
            text = text.strip()
            
            return text

        def clean_data(row):
            cleaned_data = {}
            region_mapping = {
                "asr": "Ashanti Region",
                "gar": "Greater Accra Region",
                "er": "Eastern Region",
                "wr": "Western Region",
                "cr": "Central Region",
                "vr": "Volta Region",
                "wnr": "Western North Region",
                "uwr": "Upper West Region",
                "uer": "Upper East Region",
                "or": "Oti Region",
                "ber": "Bono East Region",
                "ar": "Ahafo Region",
                "ner": "North East Region",
                "sr": "Savannah Region",
                "nr": "Northern Region"
            }
            cleaned_data["id"] = row[0]
            cleaned_data["title"] = clean_text(row[1])
            cleaned_data["date"] = row[3]
            
            try:
                cleaned_data["presiding_judge"] = clean_text(json.loads(row[4])[0] if row[4] else "")
            except (json.JSONDecodeError, IndexError, TypeError):
                cleaned_data["presiding_judge"] = clean_text(row[4])

            cleaned_data["statutes_cited"] = clean_text(row[5])
            cleaned_data["cases_cited"] = clean_text(row[6])
            cleaned_data["lawyers"] = clean_text(row[7])
            cleaned_data["town"] = clean_text(row[10])

            # Get the region code from row[11] and map it to the display name
            region_code = clean_text(row[11])
            cleaned_data["region"] = region_mapping.get(region_code)  # Default to region_code if not found
            cleaned_data["dl_citation_no"] = clean_text(row[12])
            cleaned_data["file_url"] = clean_text(row[15])
            cleaned_data["judgement"] = clean_text(row[16])
            cleaned_data["year"] = row[17]
            cleaned_data["type"] = clean_text(row[20])
            cleaned_data["decision"] = clean_text(row[24])
            cleaned_data["citation"] = clean_text(row[27])
            cleaned_data["file_name"] = clean_text(row[30])
            cleaned_data["c_t"] = "Supreme Court" if row[31] == 1 else "Court of Appeal" if row[31] == 2 else "High Court" if row[31] == 3 else ""
            cleaned_data["judgement_by"] = clean_text(row[32])
            cleaned_data["status"] = clean_text(row[33])
            cleaned_data["area_of_law"] = clean_text(row[35])
            cleaned_data["keywords_phrases"] = clean_text(row[36])
            
            return cleaned_data

        messages.append("Vectorizing data is in process...")

        # Process rows in chunks of 100
        chunk_size = 50
        current_datetime = datetime.now().strftime("%Y%m%d-%H%M%S")
        bucket_name = "dennislaw_bucket"  # Use the existing bucket

        # Get access token
        access_token = get_access_token()

        for i in range(0, num_rows_to_convert, chunk_size):
            chunk_rows = rows[i:i+chunk_size]
            cleaned_rows = [clean_data(row) for row in chunk_rows]

            # Write the cleaned data to a file
            file_name = f"ReportedCase_{current_datetime}_part_{i//chunk_size}.txt"
            with open(file_name, "w", encoding="utf-8") as file:
                file.write(f"REPORTED CASES UPLOADED ON {current_datetime}\n\n")
                for row in cleaned_rows:
                    for key, value in row.items():
                        file.write(f"{key}: {value}\n")
                    file.write("\n")

            # Upload each file chunk to Google Cloud Storage
            blob_name = f"ReportedCase_{current_datetime}_part_{i//chunk_size}.txt"
            public_url = upload_to_bucket(blob_name, file_name, bucket_name, access_token)
            messages.append(f"Uploaded chunk {i//chunk_size + 1}")

        # Close the connection
        cursor.close()
        db_connection.close()

        # Return the message log along with the final public URLs
        return jsonify({
            'messages': messages,
        }), 200

    except mysql.connector.Error as e:
        return jsonify({'message': f"Error connecting to MySQL: {e}"}), 500

    except Exception as e:
        return jsonify({'message': f"An error occurred: {e}"}), 500
