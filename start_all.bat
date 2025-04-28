start "" py app\main.py
start "" py -m http.server 8001 --directory .\web
start "" py sonik_notification_bot\main.py
