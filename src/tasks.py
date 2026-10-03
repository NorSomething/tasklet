from googleapiclient.discovery import build
from pathlib import Path
import json 
import threading

from auth import get_credentials
from auth import get_service

CACHE_FILE = Path.home() / ".cache" / "tasklet-waybar" / "cache.json"
_lock = threading.RLock()
_service = None 

def service():
    #so we can reuse the service, less api calsl
    global _service
    if _service is None:
        _service = get_service(creds=get_credentials)

    return _service

def get_tasklists(service):
    resp = service.tasklists().list(maxResults=100).execute()
    return resp.get("items", [])

def add_tasklist(service, title):
    bod = {
        "title": title
    }
    return service.tasklists().insert(body=bod).execute()

def delete_tasklist(service, tasklist_id):
    service.tasklists().delete(tasklist=tasklist_id).execute()

def get_tasks(svc, tasklist_id):
    #getting open tasks from gugle tasks
    items, token = [], None
    while True:
        resp = svc.tasks().list(
            tasklist=tasklist_id,
            maxResults=100,
            showCompleted=False,
            showHidden=False,
            pageToken=token,
        ).execute()
        items.extend(resp.get("items", []))
        token = resp.get("nextPageToken")
        if not token:
            return items

def add_task(service, tasklist_id, title, notes=""):
    bod = {
        "title": title
    }
    if notes:
        bod["notes"] = notes
    return service.tasks().insert(tasklist=tasklist_id, body=bod).execute()

def update_task(service, tasklist_id, task_id, **bod):
    return service.tasks().patch(tasklist=tasklist_id, task=task_id, body=bod).execute()

def complete_task(service, tasklist_id, task_id):
    return update_task(service, tasklist_id, task_id, status="completed") #here we are usign the bod kwargs to change the json response thingy

def delete_task(service, tasklist, tasklist_id):
    service.tasks().delete(tasklist=tasklist_id, task=task_id).execute()

def load_cache():
    try:
        return json.loads(CACHE_FILE.read_text())
    except:
        return {"lists": []}

def save_cache(data):
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = CACHE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(data))
    tmp.replace(CACHE_FILE) #this is atomic?? no way

def _slim(t):
    return {
        "id": t["id"],
        "title": t.get("title", ""), 
        "notes": t.get("notes", "")
    }

def sync():
    #load into cahche
    with _lock:
        svc = service()
        data = {"lists": []}

        for tasklist in get_tasklists(svc):
            tasks = []
            for task in get_tasks(svc, tasklist["id"]):
                if not task.get("title"):  #skip blank tasks
                    continue
                tasks.append(_slim(task))

            data["lists"].append({
                "id": tasklist["id"],
                "title": tasklist["title"],
                "tasks": tasks,
            })

        save_cache(data)
        return data

#gui funcs
def add(tasklist_id, title, notes=""):
    with _lock:
        t = add_task(service(), tasklist_id, title, notes)
        data = load_cache()
        for l in data["lists"]:
            if l["id"] == tasklist_id:
                l["tasks"].append(_slim(t))
        save_cache(data)
 
 
def remove(tasklist_id, task_id, complete=False):
    #here we remove from cache as well
    with _lock:
        if complete:
            complete_task(service(), tasklist_id, task_id)
        else:
            delete_task(service(), tasklist_id, task_id)
        
        data = load_cache()
        for l in data["lists"]:
            if l["id"] == tasklist_id:
                l["tasks"] = [t for t in l["tasks"] if t["id"] != task_id]
        save_cache(data)

def print_all_tasklist(service):
    resp = service.tasklists().list().execute()
    items = resp.get("items", [])
    
    for item in items:
        print(f"{item['title']} : ({item['id']})")


def select_tasklist_to_disp(service):
    tasklist_id = input("Enter a tasklist id to display : ")
    
    resp = service.tasks().list(tasklist=str(tasklist_id)).execute()
    data = resp.get("items", [])

    print("The tasks are:")
    for task in data:
        print(task["title"])

def insert_task_in_tasklist(service):
    tasklist_id = input("Enter a tasklist id to add task : ")
    task_title = input("Enter the task name : ")
    task_data = input("Enter task description : ")

    task_body = {
        'title': task_title,
        'notes': task_data
    }

    resp = service.tasks().insert(tasklist=str(tasklist_id), body=task_body).execute()

def main():
    svc = service()


if __name__ == "__main__":
    main()


