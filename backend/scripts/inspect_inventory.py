import requests
import pandas as pd
import uuid
import httpx
import asyncio
from pathlib import Path

async def main():
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRBhEEZJicy0bmuNC1EKvalm71ohBS8Q6pTaEJ_yp4bemVGG63Qrf9o2zY7zWaa4Q/pub?output=xlsx"
    dest_path = Path("data/imports/real_inventory.xlsx")
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    
    print("Downloading file...")
    response = requests.get(url)
    response.raise_for_status()
    
    content_type = response.headers.get('Content-Type', '')
    print(f"Content-Type: {content_type}")
    print(f"File Size: {len(response.content)} bytes")
    
    with open(dest_path, "wb") as f:
        f.write(response.content)
        
    print("Loading Excel file...")
    df = pd.read_excel(dest_path)
    
    print("\n--- Excel File Inspection ---")
    print("Shape:", df.shape)
    print("Columns:", df.columns.tolist())
    print("\nFirst 3 rows:")
    print(df.head(3).to_dict(orient="records"))
    
    # Map to schema
    # Looking at likely columns (we'll see them when this runs, but we can assume standard naming based on ProspectOS context)
    # We will just convert the DataFrame to a list of dicts. We have to map missing values (NaN) to None or empty strings.
    df = df.fillna("")
    rows = df.to_dict(orient="records")
    
    # Map columns based on common names if they exist, otherwise we'll just print it and we can adjust the script later.
    columns = df.columns.tolist()
    
    url_col = 'URL'
    name_col = 'Website/Publication Name'
    price_col = 'Price'
    da_col = 'DA'
    dr_col = 'DR'
    traffic_col = None
    industry_col = None
    
    print(f"\nGuessed Mappings:")
    print(f"URL: {url_col}")
    print(f"Name: {name_col}")
    print(f"Price: {price_col}")
    print(f"DA: {da_col}")
    print(f"DR: {dr_col}")
    print(f"Traffic: {traffic_col}")
    print(f"Industry: {industry_col}")

    if not url_col:
        print("Could not find a URL column, aborting preview.")
        return
        
    mapping = {
        "url_column": url_col,
        "publisher_name_column": name_col,
        "price_column": price_col,
        "da_column": da_col,
        "dr_column": dr_col,
        "traffic_column": traffic_col,
        "industry_column": industry_col,
    }
    
    import sys
    import os
    sys.path.append(str(Path(__file__).parent.parent))
    from app.main import app
    from httpx import ASGITransport
    
    print("\nSending COMMIT request to local API via app instance...")
    payload = {
        "batch_id": str(uuid.uuid4()),
        "mapping": {k: v for k, v in mapping.items() if v is not None},
        "rows": rows,
        "dry_run": False
    }
    
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        try:
            resp = await client.post("/publishers/import/commit", json=payload)
            print("Status Code:", resp.status_code)
            if resp.status_code == 200:
                print("Preview Results:")
                print(resp.json())
            else:
                print("Error:", resp.text)
        except Exception as e:
            print("API Error:", e)

if __name__ == "__main__":
    asyncio.run(main())
