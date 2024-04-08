import os
import random
import string
import logging
import importlib
from mitmproxy import ctx

class Tengu:
    def __init__(self):
        try:
            self.Engines={}
            for filename in os.listdir("Engines"):
                if filename.endswith(".py"):
                    self.Engines[filename[:-3]] = importlib.import_module(f"Engines.{filename[:-3]}")
            self.Engines["parsing"]=self.Engines["parsing"].ParsingEngine([])
            self.Engines["morphing"]=self.Engines["morphing"].MorphingEngine([])
            self.Engines["matching"]=self.Engines["matching"].YaraRuleEngine("Rules")
        except Exception as e:
            logging.error(e)   
        pass

    def Engine(self,engine):
        return self.Engines[engine]

    def request(self, flow):
        request=self.Engines["parsing"].parse_request(flow.request)
        if "X-Ancestor" in request["headers"]:
            morph={"headers":{
                "X-Descendant":''.join(random.choice(string.ascii_letters + string.digits) for _ in range(32))
            }}
        else:
            morph={"headers":{
                "X-Ancestor": "No-Session",
                "X-Current":''.join(random.choice(string.ascii_letters + string.digits) for _ in range(32)),
                "X-Descendant":''.join(random.choice(string.ascii_letters + string.digits) for _ in range(32))
            }}
        self.Engines["morphing"].morph_request(flow.request,morph)
        request=self.Engines["parsing"].parse_request(flow.request)
        match=self.Engines["matching"].match_rules(request)
        logging.error(match)
        #self.db.log_match(flow.request,db)
        #self.db.logs_request(flow.request,db)
        pass

    def response(self, flow):
        morph={"headers":{
            "X-Ancestor": flow.request.headers["X-Current"],
            "X-Current": flow.request.headers["X-Descendant"],
            "X-Descendant": ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(32))
        }}
        self.Engines["morphing"].morph_response(flow.response,morph)
        response=self.Engines["parsing"].parse_response(flow.response)
        match=self.Engines["matching"].match_rules(response)
        logging.error(match)
        #self.db.log_match(flow.request,db)
        #self.db.logs_request(flow.request,db)
        pass

    def done(self):
        pass

# Create an instance of the SimpleMitmProxyPlugin class
addons = [
    Tengu()
]