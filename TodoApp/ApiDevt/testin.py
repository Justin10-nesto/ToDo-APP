import requests

data = {"name": "john2GHH", 'description':"user1", 'status':'1234', 'start_date':'17/09/1999', 'start_time':'1000', 'end_date':'12/04/2035', 'end_time':'2300', 'assigned_user':1}

response = requests.post('http://127.0.0.1:8000/addTask/', data=data)
print(response.content)