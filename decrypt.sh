#!/bin/bash
# .env 파일 복호화 쉘 스크립트 (env_crypto.py 사용)

set -e

# 함수: 도움말 표시
show_help() {
    echo "사용법: $0 [비밀번호]"
    echo ""
    echo "예제:"
    echo "  $0 안전한비밀번호"
    exit 1
}

# 인자 검사
if [ $# -ne 1 ]; then
    show_help
fi

PASSWORD=$1
INPUT_FILE=".env.encrypted"
OUTPUT_FILE=".env"

# 파일 존재 여부 확인
if [ ! -f "$INPUT_FILE" ]; then
    echo "오류: '$INPUT_FILE' 파일이 존재하지 않습니다."
    echo "먼저 암호화된 파일을 만들거나 현재 디렉토리에 복사한 후 다시 시도하세요."
    exit 1
fi

# env_crypto.py가 실행 가능한지 확인
if [ ! -x "$(command -v python3)" ]; then
    echo "오류: Python 3가 설치되어 있지 않습니다."
    exit 1
fi

# env_crypto.py 파일이 존재하는지 확인
if [ ! -f "env_crypto.py" ]; then
    echo "오류: env_crypto.py 파일을 찾을 수 없습니다."
    exit 1
fi

# 필요한 Python 패키지 확인
python3 -c "import cryptography" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "cryptography 패키지가 설치되어 있지 않습니다. 설치를 시도합니다..."
    uv add cryptography
    # or pip install cryptography
    if [ $? -ne 0 ]; then
        echo "cryptography 패키지 설치에 실패했습니다. 'uv add cryptography' 또는 'pip install cryptography'로 수동 설치가 필요합니다."
        exit 1
    fi
fi

# env_crypto.py를 사용하여 복호화
python3 env_crypto.py decrypt -i "$INPUT_FILE" -o "$OUTPUT_FILE" -p "$PASSWORD"

if [ $? -ne 0 ]; then
    echo "복호화 중 오류가 발생했습니다. 비밀번호가 올바른지 확인하세요."
    exit 1
fi

echo "파일이 성공적으로 복호화되었습니다."

exit 0
