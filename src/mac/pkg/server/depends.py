from fastapi import Request

def get_headers(r: Request):
    return dict(r.scope["headers"])