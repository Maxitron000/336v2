
#!/usr/bin/env python3
import os
import signal
import subprocess
import sys

def stop_all_bot_processes():
    """Остановить все процессы бота"""
    try:
        # Находим все процессы python с main.py
        result = subprocess.run(['pgrep', '-f', 'python.*main.py'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            print(f"Найдено {len(pids)} процессов бота")
            
            for pid in pids:
                if pid:
                    try:
                        os.kill(int(pid), signal.SIGTERM)
                        print(f"Остановлен процесс {pid}")
                    except ProcessLookupError:
                        print(f"Процесс {pid} уже завершен")
                    except Exception as e:
                        print(f"Ошибка остановки процесса {pid}: {e}")
        else:
            print("Активных процессов бота не найдено")
            
    except Exception as e:
        print(f"Ошибка поиска процессов: {e}")

if __name__ == "__main__":
    print("🛑 Остановка всех процессов бота...")
    stop_all_bot_processes()
    print("✅ Готово!")
