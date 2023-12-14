class ParsingEngine:
    def __init__(self,ParsingEngines):
        pass

    def parse_request(self,obj):
        parsed_request={
            "method": "",
            "path": "",
            "headers": {},
            "body": "" 
        }
        parsed_request["method"]=obj.method
        parsed_request["path"]=f"{obj.scheme}://{obj.host}:{str(obj.port)}{obj.path}"
        for header in obj.headers:
            parsed_request["headers"][header]=obj.headers[header]
        parsed_request["body"]=obj.content
        return parsed_request

    def parse_response(self,obj):
        parsed_response={
            "status_code": "",
            "headers": {},
            "body": ""
        }
        parsed_response["status_code"]=obj.status_code
        for header in obj.headers:
            parsed_response["headers"][header]=obj.headers[header]
        parsed_response["body"]=obj.content
        return parsed_response
'''
    def try_base_64(obj):
        try:
            return base64.b64decode(s).decode('utf-8')
        except (binascii.Error, UnicodeDecodeError):
            return False
'''