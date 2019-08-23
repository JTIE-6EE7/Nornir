#!/usr/local/bin/python3

from pprint import pprint
from nornir import InitNornir
from nornir.plugins.tasks import commands
from nornir.plugins.functions.text import print_result
from nornir.plugins.tasks.networking import napalm_get

nr = InitNornir(core={"num_workers": 1})

routers = nr.filter(platform="ios")

result = routers.run(task=napalm_get, getters=["config"])

print()
for k, v in result.items():
    print("~"*60)
    print(k)
    pprint(v[0].result)

print("~"*60)
print()