from rescale import Rescale
import pandas as pd

rescale = Rescale()
jobs = pd.DataFrame(
    dict(id=j['id'], name=j['name'])
    for j in rescale.multiget("jobs")
)
print(jobs)

jobs = pd.DataFrame(
    dict(id=j['id'], name=j['name'])
    for j in rescale.jobs()
)