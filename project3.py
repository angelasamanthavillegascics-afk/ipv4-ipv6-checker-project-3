import requests
import json

def get_ip_info():
    try:
        # Get IP details from ipapi.co
        response = requests.get("https://ipapi.co/json/")
        data = response.json()

        # Extract important fields
        ip = data.get("ip")
        version = "IPv6" if ":" in ip else "IPv4"
        city = data.get("city")
        region = data.get("region")
        country = data.get("country_name")
        country_code = data.get("country")
        isp = data.get("org")
        asn = data.get("asn")
        latitude = data.get("latitude")
        longitude = data.get("longitude")
        timezone = data.get("timezone")

        # Print nicely formatted output
        print("\n========== Public IP Address Information ==========")
        print(f"Public IP Address : {ip} ({version})")
        print(f"Location          : {city}, {region}, {country} ({country_code})")
        print(f"Latitude/Longitude: {latitude}, {longitude}")
        print(f"Timezone          : {timezone}")
        print(f"ISP / Provider    : {isp}")
        print(f"ASN               : {asn}")
        print("===================================================\n")

    except Exception as e:
        print("❌ Error fetching IP details:", e)


def save_to_file():
    """Optional: Save the details to a JSON file for logs"""
    try:
        response = requests.get("https://ipapi.co/json/")
        data = response.json()

        with open("ip_info.json", "w") as f:
            json.dump(data, f, indent=4)

        print("✅ IP information saved to ip_info.json\n")
    except Exception as e:
        print("❌ Error saving file:", e)


if __name__ == "__main__":
    get_ip_info()
    save_to_file()
