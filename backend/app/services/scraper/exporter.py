import os
import csv
import json
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment

EXPORT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../exports"))
os.makedirs(EXPORT_DIR, exist_ok=True)

STANDARD_COLUMNS = [
    ("company_name", "Company Name"),
    ("website", "Website URL"),
    ("domain", "Domain"),
    ("industry", "Industry"),
    ("category", "Category"),
    ("country", "Country"),
    ("city", "City"),
    ("email", "Email Address"),
    ("phone", "Phone Number"),
    ("address", "Address"),
    ("description", "Description"),
    ("quality_score", "Quality Score"),
    ("quality_status", "Quality Status"),
    ("validation_status", "Validation Status"),
    ("source_url", "Source URL"),
    ("discovery_source", "Source"),
    ("created_at", "Extraction Date"),
]

def prepare_row_dict(record: Dict[str, Any]) -> Dict[str, Any]:
    row = {}
    for col_key, col_label in STANDARD_COLUMNS:
        val = record.get(col_key)
        if val is None:
            # Check inside cleaned_data
            cleaned = record.get("cleaned_data") or {}
            val = cleaned.get(col_key)
            
        if isinstance(val, (datetime,)):
            row[col_label] = val.isoformat()
        elif isinstance(val, (dict, list)):
            row[col_label] = json.dumps(val)
        else:
            row[col_label] = str(val) if val is not None else ""
    return row

def export_to_csv(records: List[Dict[str, Any]], filename_prefix: str = "export") -> Tuple[str, int]:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"{filename_prefix}_{timestamp}.csv"
    filepath = os.path.join(EXPORT_DIR, filename)

    fieldnames = [col_label for _, col_label in STANDARD_COLUMNS]

    with open(filepath, mode="w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in records:
            writer.writerow(prepare_row_dict(r))

    file_size = os.path.getsize(filepath)
    return filepath, file_size

def export_to_xlsx(records: List[Dict[str, Any]], filename_prefix: str = "export") -> Tuple[str, int]:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"{filename_prefix}_{timestamp}.xlsx"
    filepath = os.path.join(EXPORT_DIR, filename)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "ProspectOS Extracted Records"

    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid") # Navy blue
    align_center = Alignment(horizontal="center", vertical="center")

    headers = [col_label for _, col_label in STANDARD_COLUMNS]
    ws.append(headers)

    for cell in ws[1]:
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = align_center

    for r in records:
        row_dict = prepare_row_dict(r)
        ws.append([row_dict.get(h, "") for h in headers])

    # Auto-adjust column widths
    for col in ws.columns:
        max_len = max(len(str(cell.value or "")) for cell in col)
        col_letter = openpyxl.utils.get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = min(max(max_len + 3, 12), 45)

    wb.save(filepath)
    file_size = os.path.getsize(filepath)
    return filepath, file_size

def export_to_json(records: List[Dict[str, Any]], filename_prefix: str = "export") -> Tuple[str, int]:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"{filename_prefix}_{timestamp}.json"
    filepath = os.path.join(EXPORT_DIR, filename)

    serializable = []
    for r in records:
        row = {}
        for k, v in r.items():
            if isinstance(v, datetime):
                row[k] = v.isoformat()
            elif isinstance(v, bytes):
                row[k] = v.decode("utf-8", errors="ignore")
            else:
                row[k] = v
        serializable.append(row)

    with open(filepath, mode="w", encoding="utf-8") as f:
        json.dump(serializable, f, indent=2, ensure_ascii=False)

    file_size = os.path.getsize(filepath)
    return filepath, file_size

def export_to_html(records: List[Dict[str, Any]], filename_prefix: str = "export") -> Tuple[str, int]:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"{filename_prefix}_{timestamp}.html"
    filepath = os.path.join(EXPORT_DIR, filename)

    headers = [col_label for _, col_label in STANDARD_COLUMNS]

    rows_html = []
    for r in records:
        row_dict = prepare_row_dict(r)
        tds = "".join([f"<td>{row_dict.get(h, '')}</td>" for h in headers])
        rows_html.append(f"<tr>{tds}</tr>")

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>ProspectOS Extraction Export</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 24px; color: #1e293b; }}
h1 {{ font-size: 20px; margin-bottom: 8px; color: #0f172a; }}
p {{ font-size: 13px; color: #64748b; margin-bottom: 20px; }}
table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
th {{ background-color: #0f172a; color: #f8fafc; font-weight: 600; text-align: left; padding: 10px 12px; }}
td {{ border-bottom: 1px solid #e2e8f0; padding: 10px 12px; max-width: 280px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
tr:nth-child(even) {{ background-color: #f8fafc; }}
tr:hover {{ background-color: #f1f5f9; }}
</style>
</head>
<body>
<h1>ProspectOS Extraction Dataset</h1>
<p>Generated at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')} • Total Records: {len(records)}</p>
<table>
<thead>
<tr>{"".join([f"<th>{h}</th>" for h in headers])}</tr>
</thead>
<tbody>
{"".join(rows_html)}
</tbody>
</table>
</body>
</html>"""

    with open(filepath, mode="w", encoding="utf-8") as f:
        f.write(html_content)

    file_size = os.path.getsize(filepath)
    return filepath, file_size

def export_to_xml(records: List[Dict[str, Any]], filename_prefix: str = "export") -> Tuple[str, int]:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"{filename_prefix}_{timestamp}.xml"
    filepath = os.path.join(EXPORT_DIR, filename)

    root = ET.Element("ProspectOSDataset")
    root.set("exported_at", datetime.now(timezone.utc).isoformat())
    root.set("record_count", str(len(records)))

    for r in records:
        rec_el = ET.SubElement(root, "Record")
        row_dict = prepare_row_dict(r)
        for col_key, col_label in STANDARD_COLUMNS:
            sub = ET.SubElement(rec_el, col_key)
            sub.text = str(row_dict.get(col_label, ""))

    xml_str = ET.tostring(root, encoding="utf-8")
    pretty_xml = minidom.parseString(xml_str).toprettyxml(indent="  ")

    with open(filepath, mode="w", encoding="utf-8") as f:
        f.write(pretty_xml)

    file_size = os.path.getsize(filepath)
    return filepath, file_size

def create_export(records: List[Dict[str, Any]], export_format: str, filename_prefix: str = "prospectos_records") -> Tuple[str, int, str]:
    fmt = export_format.upper().strip()
    if fmt == "CSV":
        fp, size = export_to_csv(records, filename_prefix)
    elif fmt in ("XLSX", "EXCEL"):
        fp, size = export_to_xlsx(records, filename_prefix)
    elif fmt == "JSON":
        fp, size = export_to_json(records, filename_prefix)
    elif fmt == "HTML":
        fp, size = export_to_html(records, filename_prefix)
    elif fmt == "XML":
        fp, size = export_to_xml(records, filename_prefix)
    else:
        fp, size = export_to_csv(records, filename_prefix)
        fmt = "CSV"

    filename = os.path.basename(fp)
    download_url = f"/api/scraper/export/download/{filename}"
    return fp, size, download_url

