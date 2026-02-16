เพื่อเก็บรายชื่อไลบรารี (packages)
 pip list --format=freeze > requirements.txt

เมื่อต้องการติดตั้งจากไฟล์นี้ในเครื่องอื่น
pip install -r requirements.txt

https://drive.google.com/drive/folders/1V4RsHf4nDFhCfjrTDBIOz0V3ZRWYxXVA ******form****

https://docs.google.com/spreadsheets/d/1tdKwYhlCbjCwmUgEuRTdGbYSpdimX1xBWiIp3aGQq-I/edit?gid=1037710724#gid=1037710724 *****ชีต****

DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=1234
DB_HOST=localhost
DB_PORT=5432
DB_SCHEMA=tickets

pip install XlsxWriter==3.0.9

>>> from django.conf import settings
>>> settings.TEMPLATES[0]["OPTIONS"]["context_processors"]
['django.template.context_processors.request', 'django.contrib.auth.context_processors.auth', 'ticket.context_processors.user_permissions', 'django.contrib.messages.context_processors.messages']