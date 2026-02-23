import sys
import os

# 프로젝트 루트를 path에 추가 (templates, static 접근용)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

# Vercel 서버리스 핸들러
handler = app
