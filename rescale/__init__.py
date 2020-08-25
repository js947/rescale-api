import requests
import keyring
import json


class Rescale:
    rescale = requests.Session()

    def __init__(self, platform="platform", key="default"):
        self.s = requests.Session()
        self.s.headers.update(
            {"Authorization": "Token " + keyring.get_password("rescale", key)}
        )
        self.baseurl = "https://%s.rescale.com" % platform

    def url(self, *c):
        return "/".join((self.baseurl, "api", "v3") + c) + "/"

    def get(self, *c, **kwargs):
        return json.loads(self.s.get(self.url(*c), params=kwargs).text)

    def multiget(self, *c, **kwargs):
        nexturl = self.url(*c)
        while nexturl:
            r = json.loads(self.s.get(nexturl, params=kwargs).text)
            for result in r["results"]:
                yield result
            nexturl = r["next"]

    def post(self, *c, **kwargs):
        r = self.s.post(self.url(*c), **kwargs)
        try:
            r = json.loads(r.text)
        except json.JSONDecodeError:
            r = None
        return r

    def jobs(self):
        return self.multiget("jobs")

    def job(self, jobid):
        return self.get("jobs", jobid)

    def job_outputfiles(self, jobid):
        return self.multiget("jobs", jobid, "files")

    def job_statuses(self, jobid):
        return self.multiget("jobs", jobid, "statuses")
