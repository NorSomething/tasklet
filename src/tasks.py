from googleapiclient.discovery import build
from pathlib import Path

from auth import get_credentials
from auth import get_service

_service = None #whatdis

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

#def get tasks() how do i even do this

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
    service = get_service(creds=get_credentials)
    print_all_tasklist(service)
    select_tasklist_to_disp(service)
    insert_task_in_tasklist(service)


if __name__ == "__main__":
    main()


