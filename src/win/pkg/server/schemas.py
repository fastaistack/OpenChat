from pydantic import BaseModel
class CommonResponse(BaseModel):
    flag: bool
    errCode: int # 0：success another is error
    errMsg: str

    def success(data, message="success"):
        basic = {"flag": True,
                 "errCode": 0,
                 "errMsg": message,
                 "resData": data}
        return basic

    def fail(error_code: int, error_msg: str):
        basic = {"flag": False,
                 "errCode": error_code,
                 "errMsg": error_msg,
                 "resData": None}
        return basic

