import requests
import json
import base64
import time

JIRA_URL = "https://nuamexchange.atlassian.net"
EMAIL = "administrador_devops@nuamx.com"
API_TOKEN = "ATATT3xFfGF0xuWJIUCxKbzCGDcArpVnc0b6mr4Mt6JcL2GyRdzOl36P5C7XttYGktslq5tJNRKyuyTJLJ7MJsQ0Y_k2OCL5UV7EGhU0-Kjq8K44MXdmFQfIR7jSnqfkpaUp59V7c6Rb7ufJ9yLBnh5EC2h8nHLb1nvcJ62SzvSc3BYTfbB0jW4=073E4CDE"
JQL = "project=GDD"
FIELDS = "summary,description,status,issuetype,priority,assignee,creator,created,updated,resolutiondate,timeoriginalestimate,timespent,timeestimate,labels,parent,components,customfield_10016,customfield_11204,customfield_10144,customfield_10145,customfield_13851"

auth = base64.b64encode(f"{EMAIL}:{API_TOKEN}".encode()).decode()
headers = {
    "Authorization": f"Basic {auth}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

all_issues = []
next_token = None
page = 0

while True:
    page += 1
    payload = {
        "jql": JQL,
        "maxResults": 100,
        "fields": FIELDS.split(",")
    }
    if next_token:
        payload["nextPageToken"] = next_token

    resp = requests.post(f"{JIRA_URL}/rest/api/3/search/jql", headers=headers, json=payload)
    resp.raise_for_status()
    data = resp.json()

    issues = data.get("issues", [])
    all_issues.extend(issues)
    print(f"Página {page}: {len(issues)} issues (total acumulado: {len(all_issues)})")

    next_token = data.get("nextPageToken")
    if not next_token or data.get("isLast", False):
        break
    time.sleep(0.3)

with open("issues_gdd_full.json", "w", encoding="utf-8") as f:
    json.dump({"issues": all_issues}, f, ensure_ascii=False, indent=2)

print(f"\n✅ Total descargado: {len(all_issues)} issues en issues_gdd_full.json")