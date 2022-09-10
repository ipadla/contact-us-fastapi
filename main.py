import os
import uuid

from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, Request
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema
from pydantic import BaseModel, EmailStr
from starlette.responses import JSONResponse

load_dotenv()

ENDPOINT = os.getenv('ENDPOINT', default=uuid.uuid4())
HOST = os.getenv('HOST', default='127.0.0.1')

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
    name: str
    message: str
    phone: str


app = FastAPI()


@app.post(f"/{ENDPOINT}/")
async def send_email(
    bg: BackgroundTasks,
    email: EmailSchema,
    request: Request
) -> JSONResponse:

    if request.headers.get('host') != HOST:
        return JSONResponse(status_code=403, content={'message': 'you are not wellcome here.'})

    message = MessageSchema(
        subject='Заявка с сайта',
        recipients=[EmailStr(os.getenv('RECIPIENT', default='nobody@example.com'))],
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

    return JSONResponse(status_code=200, content={'message': 'email sent.'})
