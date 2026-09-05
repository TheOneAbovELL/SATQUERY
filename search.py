
import urllib.request, re, os
req = urllib.request.Request('https://earthobservatory.nasa.gov/world-of-change/Dubai', headers={'User-Agent': 'Mozilla/5.0'})
html = urllib.request.urlopen(req).read().decode('utf-8')
imgs = re.findall(r'/[^\x22\x27\s]+\.jpg', html)
for img in set(imgs):
    print(img)

