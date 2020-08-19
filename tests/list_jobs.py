from rescale import Rescale
import pandas as pd

rescale = Rescale()
jobs = pd.DataFrame(rescale.multiget("jobs"))
print(jobs)