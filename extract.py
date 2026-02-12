import json
import time
import os
from dotenv import load_dotenv
from groq import Groq

from schemas import ShipmentExtraction
from prompts import system_prompt

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def match_port_item(port_name, port_codes_data, product_line, is_origin):
    if not port_name: return None
    
    abbreviation_map = {
        "MAA": "Chennai", "BLR": "Bangalore", "HYD": "Hyderabad",
        "NSA": "Nhava Sheva", "MUN": "Mundra", "WFD": "Whitefield",
        "JED": "Jeddah", "DAM": "Dammam", "RUH": "Riyadh",
        "HK": "Hong Kong", "HKG": "Hong Kong", "GZG": "Guangzhou",
        "SHA": "Shanghai", "SZX": "Shenzhen", "QIN": "Qingdao",
        "TXG": "Tianjin", "LAX": "Los Angeles", "HOU": "Houston", 
        "LGB": "Long Beach", "BKK": "Bangkok", "LCH": "Laem Chabang",
        "PKG": "Port Klang", "SIN": "Singapore", "SGN": "Ho Chi Minh",
        "MNL": "Manila", "SUB": "Surabaya", "DAC": "Dhaka",
        "HAM": "Hamburg", "GOA": "Genoa", "AMR": "Ambarli",
        "IZM": "Izmir", "OSA": "Osaka", "YOK": "Yokohama",
        "PUS": "Busan", "CPT": "Cape Town",
    }


    input_parts = [p.strip().upper() for p in port_name.split('/')]
    resolved_parts = []
    for part in input_parts:
        words = part.split()
        resolved_words = [abbreviation_map.get(w, w) for w in words]
        resolved_parts.append(" ".join(resolved_words).lower())
    
    normalized_query = " / ".join(resolved_parts)
    best_matches = []
    highest_score = 0

    for item in port_codes_data:
        item_name_lower = item["name"].lower()
        if normalized_query == item_name_lower:
            score = 100
        else:
            score = sum(1 for p in resolved_parts if p in item_name_lower)

        if score > highest_score:
            highest_score = score
            best_matches = [item]
        elif score == highest_score and score > 0:
            best_matches.append(item)

    if not best_matches: return None

    
    is_india_req = (product_line == "pl_sea_import_lcl" and not is_origin) or \
                   (product_line == "pl_sea_export_lcl" and is_origin)
    
    if is_india_req:
        in_items = [m for m in best_matches if m["code"].startswith("IN")]
        if in_items: return in_items[0]

    return sorted(best_matches, key=lambda x: x["code"])[0]


def main():
    with open("emails_input.json") as f: emails = json.load(f)
    with open("port_codes_reference.json") as f: ports = json.load(f)

    results = []
    
    for email in emails:
        user_content = f"id: {email['id']}\nSubject: {email['subject']}\nBody: {email['body']}"
        
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                response_format={"type": "json_object"},
                temperature=0
            )
            
            raw_json = json.loads(response.choices[0].message.content)
            extracted = ShipmentExtraction.model_validate(raw_json)
            
            # Adding port code and name based on extracted port names
            o_item = match_port_item(extracted.origin_port_name, ports, extracted.product_line, True)
            d_item = match_port_item(extracted.destination_port_name, ports, extracted.product_line, False)

            final_output = {
                "id": extracted.id,
                "product_line": extracted.product_line,
                "incoterm": extracted.incoterm,
                "origin_port_code": o_item["code"] if o_item else None,
                "origin_port_name": o_item["name"] if o_item else None,
                "destination_port_code": d_item["code"] if d_item else None,
                "destination_port_name": d_item["name"] if d_item else None,
                "cargo_weight_kg": extracted.cargo_weight_kg,
                "cargo_cbm": extracted.cargo_cbm,
                "is_dangerous": extracted.is_dangerous
            }
            results.append(final_output)
            
        except Exception as e:
            print(f"Error on {email['id']}: {e}")
            results.append({"id": email['id'],
                            "product_line": "pl_sea_import_lcl",
                            "incoterm": "FOB",
                            "origin_port_code": None,
                            "origin_port_name": None,
                            "destination_port_code": None,
                            "destination_port_name": None,
                            "cargo_weight_kg": None,
                            "cargo_cbm": None,
                            "is_dangerous": False})
        
        time.sleep(1) # Rate limiting for API call

    with open("output.json", "w") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    main()