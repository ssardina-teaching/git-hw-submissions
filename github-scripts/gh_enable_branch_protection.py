import requests # https://docs.python-requests.org/en/latest/index.html
import json


r = requests.get('https://api.github.com/repos/django/django')
if(r.ok):
    repoItem = json.loads(r.text or r.content)
    print "Django repository created: " + repoItem['created_at']
    
    
$ curl \
  -u ssardina:$GHTOKEN -X PUT \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/RMIT-COSC1127-1125-AI21/p0-warmup-msardina/branches/master/protection \
  -d '{"required_status_checks": null, "enforce_admins": false, "required_pull_request_reviews": null, "allow_force_pushes" : false, "restrictions" : null }'
