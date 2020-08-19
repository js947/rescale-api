from rescale import Rescale
import pandas as pd

rescale = Rescale('eu', 'eu')
pd.DataFrame(rescale.multiget("jobs"))