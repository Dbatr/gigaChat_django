import json
import uuid

from django.http import HttpResponse
from django.shortcuts import render
import requests
from requests.auth import HTTPBasicAuth
from gigaChat import secret


def get_access_token():
    url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
        'RqUID': str(uuid.uuid4()),
    }
    payload = {"scope": "GIGACHAT_API_PERS"}
    res = requests.post(
        url=url,
        headers=headers,
        auth=HTTPBasicAuth(secret.CLIENT_ID, secret.SECRET),
        data=payload,
        verify=False,
    )
    access_token = res.json()["access_token"]
    return access_token


def send_prompt(msg, access_token):
    url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"

    payload = json.dumps({
        "model": "GigaChat-Lite",
        "messages": [
            {
                "role": "user",
                "content": msg,
            }
        ],
    })
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }

    response = requests.post(url, headers=headers, data=payload, verify=False)
    print(response)

    if response.status_code == 401:
        return {"error": "Unauthorized"}
    elif response.status_code != 200:
        return {"error": f"HTTP Error {response.status_code}"}
    else:
        return response.json()["choices"][0]["message"]["content"]


def chat_view(request):
    if "access_token" not in request.session:
        try:
            request.session["access_token"] = get_access_token()
        except Exception as e:
            return HttpResponse(f"Не получилось получить токен: {e}")

    if "messages" not in request.session:
        request.session["messages"] = [{"role": "ai", "content": "С чем вам помочь?"}]

    if request.method == 'POST':
        user_prompt = request.POST.get('message')
        if user_prompt:
            request.session["messages"].append({"role": "user", "content": user_prompt})

            access_token = request.session["access_token"]
            response = send_prompt(user_prompt, access_token)

            request.session["messages"].append({"role": "ai", "content": response})

    return render(request, 'chat.html', {"messages": request.session["messages"]})
