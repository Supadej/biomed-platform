import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(os.environ.get('BIOMED_ENV_FILE',str(Path(__file__).parent/'.env')),override=False)
from waitress import serve
from wsgi_app import create_app
if __name__=='__main__':serve(create_app(),host=os.environ.get('BIOMED_HOST','127.0.0.1'),port=int(os.environ.get('PORT','8765')),threads=int(os.environ.get('BIOMED_THREADS','8')),max_request_body_size=400*1024*1024,expose_tracebacks=False)
