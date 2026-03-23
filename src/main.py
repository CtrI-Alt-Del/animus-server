from dotenv import load_dotenv
from uvicorn import run

load_dotenv()

from animus.app import FastAPIApp  # noqa: E402

app = FastAPIApp.register()



def main() -> None:
    from animus.constants import Env

    run('main:app', host=Env.HOST, port=Env.PORT, reload=True)


if __name__ == '__main__':
    main()
