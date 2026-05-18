import urllib.request

for path in ['/bao_page_1', '/bao_page_1?lang=en']:
    try:
        with urllib.request.urlopen('http://localhost:8000' + path) as r:
            body = r.read().decode('utf-8', errors='replace')
            print('PATH', path)
            print('tooltip', 'persona-tooltip' in body)
            print('public health researcher', 'Public Health researcher' in body)
            print('economist', 'Economist' in body)
            idx = body.find('<section class="personas-section">')
            print('idx', idx)
            if idx != -1:
                print(body[idx:idx+700])
    except Exception as e:
        print('ERROR', path, repr(e))
