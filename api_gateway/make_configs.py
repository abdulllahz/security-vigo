import copy
import json
import os

# Define the template configuration
template_config = {
    "service": {
        "name": "",
        "host": "",
        "tags": ["Subdomain", "Public"]
    },
    "routes": [{
        "name": "",
        "protocols": ["http", "https"],
        "methods": [["POST", "GET", "PUT", "PATCH", "OPTIONS", "DELETE"]],
        "paths": [""],
        "tags": ["Root_path"],
        "original_path": "/"
    }]
}

# List of subdomains
subdomains = [
    'bss2-be', 'dispatch', 'gateway', 'leaflet-map', 'metabase', 'mis-be-pk',
    'naughty-testt', 'sp', 'track', 'api', 'api-loadboard', 'belaz-bk', 'belaz',
    'betadispatch-backend', 'boleelagao-bk', 'boleelagao', 'geocode-beta-bk',
    'geocode-beta', 'kronos-kn-bk', 'kronos-kn', 'loadboard', 'loadboard-kn',
    'maps', 'nominatim-bk', 'nominatim', 'raptor-bk', 'raptor', 'talos-test1',
    'track-backend'
]

# Output directory
output_dir = './config/'

# Generate configurations for each subdomain
for subdomain in subdomains:
    # Create a deep copy of the template configuration
    config = copy.deepcopy(template_config)

    # Update the configuration with subdomain-specific values
    config["service"]["name"] = subdomain.capitalize()  # Update with appropriate service name
    config["service"]["host"] = f"{subdomain}.bykea.net"
    config["routes"][0]["name"] = "Root"  # Update with appropriate route name
    config["routes"][0]["paths"] = [f"/{subdomain}/"]

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Write configuration to a JSON file
    output_filename = os.path.join(output_dir, f"{subdomain}.json")
    with open(output_filename, 'w') as outfile:
        json.dump(config, outfile, indent=4)

    print(f"Generated configuration for {subdomain} and saved to {output_filename}")

