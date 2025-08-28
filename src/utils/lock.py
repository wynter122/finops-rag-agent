import os
import time
import fcntl
from pathlib import Path
from typing import Optional
from contextlib import contextmanager

class FileLock:
    """파일 기반 락 구현"""
    
    def __init__(self, lock_file: str = 'data/.etl.lock'):
        self.lock_file = Path(lock_file)
        self.lock_file.parent.mkdir(parents=True, exist_ok=True)
        self.fd = None
    
    def acquire(self, timeout: int = 300) -> bool:
        """락 획득 (timeout 초 대기)"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                self.fd = os.open(self.lock_file, os.O_CREAT | os.O_EXCL | os.O_RDWR)
                # 락 파일에 프로세스 정보 기록
                pid_info = f"PID: {os.getpid()}, Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                os.write(self.fd, pid_info.encode())
                os.fsync(self.fd)
                return True
            except FileExistsError:
                # 락 파일이 존재하는 경우, 프로세스가 살아있는지 확인
                if self._is_process_alive():
                    time.sleep(1)
                    continue
                else:
                    # 죽은 프로세스의 락 파일 정리
                    try:
                        os.remove(self.lock_file)
                    except FileNotFoundError:
                        pass
                    continue
            except Exception as e:
                print(f"락 획득 중 오류: {e}")
                return False
        
        return False
    
    def release(self):
        """락 해제"""
        if self.fd is not None:
            try:
                os.close(self.fd)
                os.remove(self.lock_file)
            except (OSError, FileNotFoundError):
                pass
            finally:
                self.fd = None
    
    def _is_process_alive(self) -> bool:
        """락 파일의 프로세스가 살아있는지 확인"""
        try:
            with open(self.lock_file, 'r') as f:
                content = f.read().strip()
                if content.startswith('PID:'):
                    pid = int(content.split(',')[0].split(':')[1].strip())
                    # 프로세스 존재 여부 확인 (Unix/Linux)
                    try:
                        os.kill(pid, 0)  # 시그널 0은 프로세스 존재 여부만 확인
                        return True
                    except OSError:
                        return False
        except (FileNotFoundError, ValueError, IndexError):
            pass
        return False

@contextmanager
def etl_lock(timeout: int = 300):
    """ETL 작업용 락 컨텍스트 매니저"""
    lock = FileLock()
    try:
        if lock.acquire(timeout):
            yield
        else:
            raise TimeoutError(f"ETL 락 획득 실패 (timeout: {timeout}초)")
    finally:
        lock.release()
