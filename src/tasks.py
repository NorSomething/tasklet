from googleapiclient.discovery import build

from auth import get_credentials
from auth import get_service


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


