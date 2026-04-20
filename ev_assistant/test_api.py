import requests

def test_search():
    url = "https://ev-assistant-143258194645.asia-south1.run.app/search?location=Pune&charger_type=fast&radius=5"
    response = requests.get(url)
    assert response.status_code == 200
