"""Small authenticated API client; token is read from a private file only."""
import json, os, pathlib, urllib.request
import websocket

class HA:
    def __init__(self):
        self.url = os.environ.get('HA_HTTP_URL', 'http://192.168.0.200')
        self.token = pathlib.Path(os.environ['HA_TOKEN_FILE']).read_text().strip()
        self.ws = websocket.create_connection(self.url.replace('http', 'ws', 1) + '/api/websocket', timeout=40)
        self.ws.recv()
        self.ws.send(json.dumps({'type':'auth','access_token':self.token}))
        assert json.loads(self.ws.recv())['type'] == 'auth_ok', 'HA authentication failed'
        self.n = 0
    def call(self, **msg):
        self.n += 1
        self.ws.send(json.dumps(dict(msg, id=self.n)))
        while True:
            r = json.loads(self.ws.recv())
            if r.get('id') == self.n:
                if not r.get('success'): raise RuntimeError(r.get('error'))
                return r.get('result')
    def rest(self, path, data=None):
        req = urllib.request.Request(self.url + '/api/' + path, data=None if data is None else json.dumps(data).encode(), headers={'Authorization':'Bearer '+self.token, 'Content-Type':'application/json'})
        with urllib.request.urlopen(req, timeout=40) as r:
            return json.load(r)

if __name__ == '__main__':
    ha = HA()
    me = ha.call(type='auth/current_user')
    helper = 'input_select.dashboard_theme_' + __import__('re').sub(r'[^a-z0-9]+', '_', me['name'].lower())
    print('Authenticated as', me['name'], '; theme:', ha.rest('states/' + helper)['state'])
    print('Registered themes:', list(ha.call(type='frontend/get_themes')['themes']))
