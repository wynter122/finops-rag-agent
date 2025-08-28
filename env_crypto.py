#!/usr/bin/env python3
"""
환경 변수(.env) 파일 암호화/복호화 스크립트 - cryptography 라이브러리 사용
"""
import os
import base64
import argparse
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import padding

def derive_key(password, salt=None, iterations=100000):
    """비밀번호로부터 암호화 키와 IV 생성"""
    if salt is None:
        salt = os.urandom(16)  # 새 솔트값 생성
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=48,  # 32바이트 키 + 16바이트 IV
        salt=salt,
        iterations=iterations,
    )
    
    key_material = kdf.derive(password.encode())
    key = key_material[:32]  # AES-256 키
    iv = key_material[32:48]  # 16바이트 IV
    
    return key, iv, salt

def encrypt_file(input_file, output_file, password):
    """파일 암호화"""
    try:
        # 키, IV, 솔트 생성
        key, iv, salt = derive_key(password)
        
        # 파일 내용 읽기
        with open(input_file, 'rb') as f:
            data = f.read()
        
        # 패딩 적용
        padder = padding.PKCS7(algorithms.AES.block_size).padder()
        padded_data = padder.update(data) + padder.finalize()
        
        # 암호화
        encryptor = Cipher(algorithms.AES(key), modes.CBC(iv)).encryptor()
        encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
        
        # 암호화된 내용과 솔트값을 함께 저장
        # 포맷: VERSION(1) + ITERATIONS(4) + SALT(16) + IV(16) + ENCRYPTED_DATA
        with open(output_file, 'wb') as f:
            f.write(b'\x01')  # 버전 1
            f.write(int.to_bytes(100000, 4, byteorder='big'))  # 반복 횟수
            f.write(salt)
            f.write(iv)
            f.write(encrypted_data)
        
        print(f"파일이 성공적으로 암호화되어 {output_file}에 저장되었습니다.")
        return True
    
    except Exception as e:
        print(f"암호화 중 오류 발생: {e}")
        return False

def decrypt_file(input_file, output_file, password):
    """파일 복호화"""
    try:
        # 암호화된 파일 읽기
        with open(input_file, 'rb') as f:
            version = f.read(1)
            if version != b'\x01':
                raise ValueError("지원되지 않는 파일 버전입니다.")
            
            iterations = int.from_bytes(f.read(4), byteorder='big')
            salt = f.read(16)
            iv = f.read(16)
            encrypted_data = f.read()
        
        # 키 유도
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=iterations,
        )
        key = kdf.derive(password.encode())
        
        # 복호화
        decryptor = Cipher(algorithms.AES(key), modes.CBC(iv)).decryptor()
        padded_data = decryptor.update(encrypted_data) + decryptor.finalize()
        
        # 패딩 제거
        unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
        data = unpadder.update(padded_data) + unpadder.finalize()
        
        # 복호화된 내용 저장
        with open(output_file, 'wb') as f:
            f.write(data)
        
        print(f"파일이 성공적으로 복호화되어 {output_file}에 저장되었습니다.")
        return True
    
    except ValueError as e:
        print(f"복호화 오류: {e}")
        print("파일 형식이 올바르지 않거나 비밀번호가 틀렸습니다.")
        return False
    
    except Exception as e:
        print(f"복호화 중 오류 발생: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description=".env 파일 암호화/복호화 도구")
    parser.add_argument('action', choices=['encrypt', 'decrypt'], help='수행할 작업')
    parser.add_argument('-i', '--input', required=True, help='입력 파일 경로')
    parser.add_argument('-o', '--output', required=True, help='출력 파일 경로')
    parser.add_argument('-p', '--password', required=True, help='암호화/복호화 비밀번호')
    
    args = parser.parse_args()
    
    if args.action == 'encrypt':
        encrypt_file(args.input, args.output, args.password)
    else:
        decrypt_file(args.input, args.output, args.password)

if __name__ == "__main__":
    main()
