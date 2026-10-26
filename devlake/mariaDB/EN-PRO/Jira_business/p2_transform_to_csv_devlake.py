import json
import csv
from datetime import datetime, timedelta, timezone

# 1. Columnas EXACTAS
COLUMNS = [
    "id", "_raw_data_params", "url", "issue_key", "title",
    "description", "type", "original_status", "original_type",
    "story_point", "resolution_date", "created_date", "updated_date",
    "parent_issue_id", "priority", "original_estimate_minutes",
    "time_spent_minutes", "time_remaining_minutes", "creator_id",
    "creator_name", "assignee_id", "assignee_name", "severity",
    "component", "lead_time_minutes", "original_project", "labels",
    "urgency", "is_subtask", "due_date", "fix_versions",
    "event_report_date", "event_start_date", "event_end_date","end_definitive_correction_mttr"
]

def adf_to_text(node):
    if node is None:
        return ""
    if isinstance(node, str):
        return node
    if isinstance(node, dict):
        if node.get("type") == "text":
            return node.get("text", "")
        parts = []
        for child in node.get("content", []):
            parts.append(adf_to_text(child))
        return " ".join(p for p in parts if p)
    if isinstance(node, list):
        return " ".join(adf_to_text(n) for n in node)
    return ""

def fmt_date(iso_str):
    """
    Para timestamps reales de Jira (created, updated, resolutiondate).
    Convierte a UTC porque DevLake lo requiere para sus cálculos de métricas.
    """
    if not iso_str:
        return None
    try:
        dt = datetime.strptime(iso_str[:19], "%Y-%m-%dT%H:%M:%S")
        if len(iso_str) >= 24 and iso_str[19] == '.':
            tz_str = iso_str[23:]
            sign = 1 if tz_str[0] == '+' else -1
            offset = timezone(timedelta(
                hours=sign*int(tz_str[1:3]), 
                minutes=sign*int(tz_str[3:5])
            ))
            dt = dt.replace(tzinfo=offset).astimezone(timezone.utc)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        print(f"⚠️ Error formateando fecha '{iso_str}': {e}")
        return None

def fmt_local(iso_str):
    """
    Para los campos del evento (customfields de Jira).
    Extrae la fecha y hora EXACTAMENTE como las ves en la interfaz de Jira,
    SIN convertir a UTC (ignora el offset -0500).
    """
    if not iso_str:
        return None
    try:
        # Tomamos los primeros 19 caracteres: YYYY-MM-DDTHH:MM:SS
        # y reemplazamos la 'T' por un espacio.
        return iso_str[:19].replace('T', ' ')
    except Exception as e:
        print(f"⚠️ Error formateando fecha local '{iso_str}': {e}")
        return None

def to_minutes(seconds):
    if seconds is None:
        return None
    return int(seconds // 60)

with open("issues_gdd_full.json", "r", encoding="utf-8") as f:
    data = json.load(f)

rows = []
for issue in data["issues"]:
    fields = issue.get("fields", {})
    assignee = fields.get("assignee") or {}
    creator = fields.get("creator") or {}
    parent = fields.get("parent") or {}
    status_obj = fields.get("status") or {}
    issuetype = fields.get("issuetype") or {}
    priority = fields.get("priority") or {}
    components = fields.get("components") or []
    
    component_names = ",".join([c.get("name", "") for c in components]) if components else None

    row = {
        "id": f"jira:GDD:{issue.get('id')}",
        "_raw_data_params": None,
        "url": issue.get("self", None),
        "issue_key": issue.get("key", None),
        "title": fields.get("summary", None),
        "description": adf_to_text(fields.get("description")) or None,
        "type": issuetype.get("name", None),
        "original_status": status_obj.get("name", None),
        "original_type": issuetype.get("name", None),
        "story_point": fields.get("customfield_10016") or None,
        
        # TIMESTAMPS REALES (Convertidos a UTC)
        "resolution_date": fmt_date(fields.get("resolutiondate")),
        "created_date": fmt_date(fields.get("created")),
        "updated_date": fmt_date(fields.get("updated")),
        
        "parent_issue_id": parent.get("id", None) if parent else None,
        "priority": priority.get("name", None),
        "original_estimate_minutes": to_minutes(fields.get("timeoriginalestimate")),
        "time_spent_minutes": to_minutes(fields.get("timespent")),
        "time_remaining_minutes": to_minutes(fields.get("timeestimate")),
        "creator_id": creator.get("accountId", None),
        "creator_name": creator.get("displayName", None),
        "assignee_id": assignee.get("accountId", None),
        "assignee_name": assignee.get("displayName", None),
        "severity": None, 
        "component": component_names,
        "lead_time_minutes": None,
        "original_project": "GDD",
        "labels": ",".join(fields.get("labels", [])) if fields.get("labels") else None,
        "urgency": None,
        "is_subtask": None,
        "due_date": None,
        "fix_versions": None,
        
        # CAMPOS DEL EVENTO (Fecha y hora local, SIN conversión a UTC)
        "event_report_date":              fmt_local(fields.get("customfield_11204")),
        "event_start_date":               fmt_local(fields.get("customfield_10144")),
        "event_end_date":                 fmt_local(fields.get("customfield_10145")),
        "end_definitive_correction_mttr": fmt_local(fields.get("customfield_13851"))
    }
    rows.append(row)

with open("issues_gdd.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=COLUMNS)
    writer.writeheader()
    for r in rows:
        r_clean = {k: ("NULL" if v is None or v == "" else v) for k, v in r.items()}
        writer.writerow(r_clean)

print(f"✅ CSV generado: issues_gdd.csv con {len(rows)} filas, listo para DevLake.")