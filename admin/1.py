from .model import Admin
for a in Admin.objects:
    print(a.username, a.password)
