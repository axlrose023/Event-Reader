FROM python

COPY requirements.txt ./

WORKDIR /app

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8001

COPY . .

CMD['python', 'manage.py', 'runserver']