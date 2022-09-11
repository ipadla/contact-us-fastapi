import logging
import os
import sys
import uuid

import uvicorn
from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, Request
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema
from pydantic import BaseModel, constr, EmailStr
from starlette import status
from starlette.responses import JSONResponse
from uvicorn.config import LOGGING_CONFIG

load_dotenv()
log = logging.getLogger("uvicorn.info")

ENDPOINT = os.getenv('ENDPOINT', default=uuid.uuid4())
REFERER = os.getenv('REFERER', default='')
HOST = os.getenv('HOST', default='127.0.0.1')

CORN_HOST = os.getenv('CORN_HOST', default='127.0.0.1')
CORN_PORT = os.getenv('CORN_PORT', default='8000')

CONF = ConnectionConfig(
    MAIL_USERNAME=os.getenv('MAIL_USERNAME', default=''),
    MAIL_PASSWORD=os.getenv('MAIL_PASSWORD', default=''),
    MAIL_FROM=EmailStr(os.getenv('MAIL_FROM', default='')),
    MAIL_PORT=int(os.getenv('MAIL_PORT', default=25)),
    MAIL_SERVER=os.getenv('MAIL_SERVER', default=''),
    MAIL_TLS=bool(os.getenv('MAIL_TLS', default=False)),
    MAIL_SSL=bool(os.getenv('MAIL_SSL', default=False)),
)


class EmailSchema(BaseModel):
    name: constr(max_length=128)
    message: str
    phone: constr(max_length=64)


app = FastAPI(
    docs_url=None,
    redoc_url=None
)


@app.post(f"/{ENDPOINT}/")
async def send_email(
    bg: BackgroundTasks,
    email: EmailSchema,
    request: Request
) -> JSONResponse:

    log.info((
        f"to:{request.headers.get('host')} "
        f"from:{request.client} "
        f"ref:{request.headers.get('referer')}"
    ))

    if request.headers.get('content-type', None) != 'application/json':
        return JSONResponse(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            content={'message': 'Unsupported media type.'}
        )

    if request.headers.get('referer') != REFERER:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={'message': 'you are not wellcome here.'}
        )

    if request.headers.get('host') != HOST:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={'message': 'you are not wellcome here.'}
        )

    message = MessageSchema(
        subject='Заявка с сайта',
        recipients=[
            EmailStr(
                os.getenv('RECIPIENT', default='nobody@example.com')
            )
        ],
        body=(
            f"""
            Имя: {email.dict().get('name')}
            Телефон: {email.dict().get('phone')}
            ---

            {email.dict().get('message')}
            """
        ),
    )

    fm = FastMail(CONF)

    bg.add_task(fm.send_message, message)

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={'message': 'email sent.'}
    )


def main() -> None:
    root_path = ''
    if len(sys.argv) >= 2:
        root_path = sys.argv[1]

    LOGGING_CONFIG["formatters"]["access"]["fmt"] = (
        '%(asctime)s %(levelprefix)s %(client_addr)s - '
        '"%(request_line)s" %(status_code)s'
    )
    LOGGING_CONFIG["formatters"]["default"]["fmt"] = (
        "%(asctime)s %(levelprefix)s %(message)s"
    )

    date_fmt = "%Y-%m-%d %H:%M:%S"
    LOGGING_CONFIG["formatters"]["default"]["datefmt"] = date_fmt
    LOGGING_CONFIG["formatters"]["access"]["datefmt"] = date_fmt

    uvicorn.run(
        "main:app",
        host=CORN_HOST,
        port=int(CORN_PORT),
        log_level='info',
        proxy_headers=True,
        root_path=root_path
    )


if __name__ == '__main__':
    main()
