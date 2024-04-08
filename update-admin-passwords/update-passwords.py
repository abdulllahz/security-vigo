import requests
import random
import string
import csv

# Function to generate a random password
def generate_random_password(length=13):
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for _ in range(length))

# Read input CSV file and update passwords
input_csv_file = 'old.csv'
output_csv_file = 'updated.csv'

with open(input_csv_file, 'r') as infile, open(output_csv_file, 'w', newline='') as outfile:
    csv_reader = csv.reader(infile)
    csv_writer = csv.writer(outfile)

    # Write header to output CSV
    csv_writer.writerow(['Phone', 'Password'])

    for row in csv_reader:
        phone = row[0]
        password = generate_random_password()

        headers = {
            'X-BB-client-Token': 'ey',
            'Content-Type': 'application/json'
        }

        data = {
            "phone": phone,
            "password": password,
            "type": "admin"
        }

        try:
            response = requests.put('https://raptor.bykea.net/v1/user/password', headers=headers, json=data)
            response.raise_for_status()  # Raise an exception for HTTP errors

            if response.status_code == 200:
                print(f"Password updated for phone: {phone}")
                csv_writer.writerow([phone, password])
        except requests.exceptions.RequestException as e:
            print(f"Error updating password for phone: {phone} - {e}")

print("Task completed. Check the output CSV for updated passwords.")

