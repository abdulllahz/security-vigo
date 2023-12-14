class MorphingEngine:
    def __init__(self,MorphingEngines):
        pass

    def morph_request(self,obj,target):
        obj.host = target["host"] if "host" in target else obj.host
        obj.port = target["port"] if "port" in target else obj.port
        obj.method = target["method"] if "method" in target else obj.method
        obj.scheme = target["scheme"] if "scheme" in target else obj.scheme
        obj.content = target["body"] if "body" in target else obj.content
        obj.path = target["path"] if "path" in target else obj.path
        if ("query" in target):
            temp="?"
            for params in target["query"]:
                value=target["query"][param]
                temp=temp+f"{param}={value}&"
            obj.path=obj.path+temp[:-1]
        for target_header in target["headers"]:
            for header in obj.headers:
                if header==target_header:
                    obj.headers[header]=target["headers"][target_header]
                else:
                    obj.headers[target_header]=target["headers"][target_header]
        return True

    def morph_response(self,obj,target):
        obj.status_code = target["status_code"] if "status_code" in target else obj.status_code
        obj.content = target["body"] if "body" in target else obj.content
        for target_header in target["headers"]:
            for header in obj.headers:
                if header==target_header:
                    obj.headers[header]=target["headers"][target_header]
                else:
                    obj.headers[target_header]=target["headers"][target_header]
        return True