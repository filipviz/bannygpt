```bash
# Install dependencies
pipenv install

# Run. Adjust workers as needed.
pipenv run gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker -w 1 main:app
```
