import configparser
from pathlib import Path
import re
import requests
import json
from functools import lru_cache
import pandas as pd
from tqdm import tqdm


class Rescale:
    def __init__(self, platform="global"):
        cfg = configparser.ConfigParser()
        cfg.read(Path.cwd() / "drive" / "My Drive" / "apiconfig")

        self.s = requests.Session()
        self.s.headers.update({"Authorization": "Token " + cfg.get(platform, "apikey")})
        self.baseurl = cfg.get(platform, "apibaseurl")

    # level 1 functionality
    def url(self, *c):
        return "/".join((self.baseurl, "api", "v3") + c) + "/"

    def get(self, *c, **kwargs):
        return json.loads(self.s.get(self.url(*c), params=kwargs).text)

    def multiget(self, *c, key=None, **kwargs):
        nexturl = self.url(*c)
        while nexturl:
            r = json.loads(self.s.get(nexturl, params=kwargs).text)

            if "results" not in r:
                return []

            for result in r["results"]:
                yield result[key] if key else result
            nexturl = r["next"]

    def delete(self, *c, **kwargs):
        return self.s.delete(self.url(*c), params=kwargs).text

    def post(self, *c, **kwargs):
        r = self.s.post(self.url(*c), **kwargs)
        try:
            r = json.loads(r.text)
        except json.JSONDecodeError:
            r = None
        return r

    # level 2 functionality
    def get_jobs(self):
        return self.multiget("jobs", page_size=999)

    @lru_cache(maxsize=2048)
    def get_job(self, jobid):
        return self.get("jobs", jobid)

    def delete_job(self, jobid):
        return self.delete("jobs", jobid)

    def get_job_status(self, jobid):
        return next(self.multiget("jobs", jobid, "statuses"))["status"]

    @lru_cache(maxsize=2048)
    def get_job_hwinfo(self, jobid):
        try:
            hw = self.get_job(jobid)["jobanalyses"][0]["hardware"]
            return dict(
                coretype=hw["coreType"]["code"],
                corecount=int(hw["coresPerSlot"]),
                walltime=int(hw["walltime"]),
            )
        except Exception as e:
            print(jobid, type(e), e)
            return {}

    def get_job_outputfiles(self, jobid, filename=None):
        for f in self.multiget("jobs", jobid, "files", search=filename):
            yield f["id"], f["name"]

    @lru_cache(maxsize=2048)
    def get_file(self, fileid):
        r = self.get("files", fileid, "lines")
        if "lines" in r:
            return r["lines"]
        print("file", fileid, "contents not found", r)
        return []

    def download_file(self, fileid, filename):
        r = self.s.get(self.url("files", fileid, "contents"), stream=True)
        total = int(r.headers.get("content-length", 0))
        chunksize = 1024 * 1024 * 1024
        with open(filename, "wb") as fd, tqdm(
            desc=str(filename),
            total=total,
            unit="iB",
            unit_scale=True,
            unit_divisor=1024,
        ) as bar:
            for chunk in r.iter_content(chunksize):
                bar.update(fd.write(chunk))

    # level 3 functionality = returning dataframes
    def jobs(self, search=lambda name: True):
        return pd.DataFrame(
            dict(
                id=j["id"],
                name=j["name"],
                status=self.get_job_status(j["id"]),
                sla="OD" if self.get_job(j["id"])["isLowPriority"] else "ODP",
                **self.get_job_hwinfo(j["id"]),
            )
            for j in self.get_jobs()
            if search(j["name"])
        ).set_index("id")

    @lru_cache()
    def pricing(self):
        return pd.DataFrame(
            dict(
                coretype=p["coreType"],
                planname=p["planName"],
                plantype=p["planType"],
                currency=p["value"]["currency"],
                amount=float(p["value"]["amount"]),
            )
            for p in self.get("billing", "computeprices")
            if p["isActive"]
        ).pivot_table(
            index="coretype", values="amount", columns=["plantype", "planname"]
        )

    def gather(self, search=lambda name: True, metrics={}):
        def __get_job_metric(jobid, filename, regex, type_fn):
            r = re.compile(regex)
            val = pd.NA
            for fileid in self.get_job_outputfiles(jobid, filename):
                for line in self.get_file(fileid):
                    mat = r.match(line)
                    if mat:
                        try:
                            val = type_fn(mat[1])
                        except ValueError:
                            pass
            return val

        jobs = self.jobs(search)
        jobs = jobs.join(
            pd.DataFrame(
                data={
                    "id": [jobid for jobid in jobs.index],
                    **{
                        key: [
                            __get_job_metric(jobid, filename, regex, type_fn)
                            for jobid in jobs.index
                        ]
                        for key, (filename, regex, type_fn) in metrics.items()
                    },
                }
            ).set_index("id")
        )
        jobs = jobs.join(self.pricing(), on="coretype").rename(
            columns={
                ("2019-on-demand", "pay-as-you-go-on-demand"): "OD cost pch",
                ("2019-on-demand-pro", "pay-as-you-go-instant"): "ODP cost pch",
            }
        )

        jobs["OD cost ph"] = jobs["corecount"] * jobs["OD cost pch"]
        jobs["ODP cost ph"] = jobs["corecount"] * jobs["ODP cost pch"]
        return jobs

    def archive(self, jobid, dir, search=None):
        dir.mkdir(exist_ok=True)

        with (dir / "job.json").open("w") as f:
            json.dump(rescale.get_job(job), f)

        for file, filename in rescale.get_job_outputfiles(job, search):
            rescale.download_file(file, dir / filename)
