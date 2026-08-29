class AppException(Exception):
    def __init__(self, code: int, msg: str, status_code: int = 400):
        self.code = code
        self.msg = msg
        self.status_code = status_code
        super().__init__(msg)


class NotFoundException(AppException):
    def __init__(self, msg: str = "资源不存在"):
        super().__init__(code=404, msg=msg, status_code=404)


class UnauthorizedException(AppException):
    def __init__(self, msg: str = "未授权访问"):
        super().__init__(code=401, msg=msg, status_code=401)


class ForbiddenException(AppException):
    def __init__(self, msg: str = "无权限访问"):
        super().__init__(code=403, msg=msg, status_code=403)


class BadRequestException(AppException):
    def __init__(self, msg: str = "请求参数错误"):
        super().__init__(code=400, msg=msg, status_code=400)


class ProviderException(AppException):
    def __init__(self, msg: str = "AI服务商调用失败"):
        super().__init__(code=5001, msg=msg, status_code=502)


class ProviderTokenExpired(ProviderException):
    def __init__(self, msg: str = "API密钥已失效"):
        super().__init__(msg=msg)


class ProviderQuotaExhausted(ProviderException):
    def __init__(self, msg: str = "API配额已耗尽"):
        super().__init__(msg=msg)


class ProviderTimeout(ProviderException):
    def __init__(self, msg: str = "API调用超时"):
        super().__init__(msg=msg)


class ProviderModelRejected(ProviderException):
    def __init__(self, msg: str = "模型拒绝请求"):
        super().__init__(msg=msg)


class TaskNotFoundException(AppException):
    def __init__(self, msg: str = "任务不存在"):
        super().__init__(code=4041, msg=msg, status_code=404)


class ModelNotFoundException(AppException):
    def __init__(self, msg: str = "模型不存在或未启用"):
        super().__init__(code=4042, msg=msg, status_code=404)