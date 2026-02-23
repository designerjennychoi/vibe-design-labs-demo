import sys
import os

# 프로젝트 루트를 Python path에 추가
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root)

# app.py의 Flask 앱 임포트
from app import app

# Vercel 서버리스 환경에서 template/static 폴더 경로를 절대경로로 재설정
app.template_folder = os.path.join(root, "templates")
app.static_folder = os.path.join(root, "static")

# Vercel 핸들러
handler = app
