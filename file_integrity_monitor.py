"""
Project: ChemiDoc File Integrity Monitoring System
Purpose: Verifies the integrity of ChemiDoc Imaging Files
Author: Geovany Serrano 
"""

import hashlib
import sqlite3 
import os
from datetime import datetime
from pathlib import Path
import json


class FileIntegrityMonitor:
    def __init__(self, db_path = "file_integrity.db"):
        self.db_path = db_path
        self.init_database()
        
    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS file_hashes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                filepath TEXT UNIQUE NOT NULL,
                file_hash TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                created_date TEXT NOT NULL,
                last_verified TEXT,
                status TEXT DEFAULT 'Original'
            )
        ''')
                       
        conn.commit()
        conn.close()
        print(f"Database initialized: {self.db_path}")

    def calculate_hash(self, filepath, algorithm = 'sha256'):
        hash_func = hashlib.new(algorithm)

        try:
            with open(filepath, 'rb') as f:
                #8KB Chunks
                while chunk := f.read(8192):
                    hash_func.update(chunk)
            return hash_func.hexdigest()
        #Incase file is locked/no persmission/corrupted/etc.
        except Exception as e:
            print(f"Error: Calculating hash for {filepath}: {e}")
            return None
        
    def register_file(self, filepath):
        if not os.path.exists(filepath):
            print(f"Error: File not found - {filepath}")
            return False

        file_hash = self.calculate_hash(filepath)
        if not file_hash:
            return False

        file_size = os.path.getsize(filepath)
        filename = os.path.basename(filepath)
        created_date = datetime.now().isoformat()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO file_hashes (filename, filepath, file_hash, file_size, created_date)
                VALUES (?, ?, ?, ?, ?)
            ''', (filename, filepath, file_hash, file_size, created_date))

            conn.commit()
            print(f" Registered: {filename}")
            print(f" Hash: {file_hash[:16]}...")
            return True

        except sqlite3.IntegrityError:
            print(f"File already registered: {filename}")
            return False
        except Exception as e:
            print(f"Error: registering file: {e}")
            return False
        finally:
            conn.close()
    
    def verify_file(self, filepath):
        if not os.path.exists(filepath):
            return {"status": "error", "message": "File not found"}
        
        current_hash = self.calculate_hash(filepath)
        if not current_hash:
            return {"status": "error", "message": "Calculating hash failed"}
        
        #Get stored hash from database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT file_hash, file_size, filename FROM file_hashes WHERE filepath = ?', (filepath,))
        result = cursor.fetchone()

        if not result:
            conn.close()
            return {"status": "unregistered", "message": "File not in database"}
         
        stored_hash, stored_size, filename = result 
        current_size = os.path.getsize(filepath)

        cursor.execute('''
            UPDATE file_hashes 
            SET last_verified = ?, status = ?
            WHERE filepath = ?
        ''', (datetime.now().isoformat(), 
            'Original' if current_hash == stored_hash else 'TAMPERED', 
            filepath))
        
        conn.commit()
        conn.close()

        if current_hash == stored_hash and current_size == stored_size:
            return {
                "status": "verified",
                "filename": filename,
                "message": "File integrity verified - No tampering detected"
            }
        else:
            return {
                "status": "tampered",
                "filename": filename,
                "message": " Warning: File has been tampered with!!!",
                "details": {
                    "hash_match": current_hash == stored_hash,
                    "size_match": current_size == stored_size,
                    "stored_hash": stored_hash[:16] + "...",
                    "current_hash": current_hash[:16] + "...",
                    "stored_size": stored_size,
                    "current_size": current_size, 
                }
            }
        
    def register_directory(self, directory, file_extension = ".scn"):
        if not os.path.isdir(directory):
            print(f"Error: Directory not found - {directory}")
            return 
        
        print(f"\nScanning directory: {directory}")
        print(f"Looking for files with extension: {file_extension}\n")

        registered_count = 0
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith(file_extension):
                    filepath = os.path.join(root, file)
                    if self.register_file(filepath):
                        registered_count += 1

        print(f"\n{registered_count} files(s) registered successfully")
        
        
        
    def verify_directory(self, directory, file_extension = ".scn"):
        if not os.path.isdir(directory):
            print(f"Error: Directory not found - {directory}")
            return
        
        print(f"\nVerifying files in: {directory}")
        
        verified_count = 0
        tampered_count = 0

        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith(file_extension):
                    filepath = os.path.join(root, file)
                    result = self.verify_file(filepath)

                    if result["status"] == "verified":
                        print(f" {file}: CLEAN")
                        verified_count += 1
                    elif result["status"] == "tampered":
                        print(f" {file}: TAMPERED")
                        tampered_count += 1
                    elif result["status"] == "unregistered":
                        print(f" {file}: NOT REGISTERED")

        print(f"\n ---Verification Summary---")
        print(f"Clean Files: {verified_count}")
        print(f"Tampered Files: {tampered_count}")

    def generate_report(self, output_file = "integrity_report.txt"):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM file_hashes ORDER BY created_date DESC')
        results = cursor.fetchall()
        conn.close()

        with open(output_file, 'w') as f:
            f.write("=" * 70 + "\n")
            f.write("FILE INTEGRITY MONITORING REPORT \n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} \n")
            f.write("=" * 70 + "\n\n")

            for row in results:
                f.write(f"Filename: {row[1]}\n")
                f.write(f"Path: {row[2]}\n")
                f.write(f"Hash: {row[3]}\n")
                f.write(f"size: {row[4]} bytes\n")
                f.write(f"Registered: {row[5]}\n")
                f.write(f"Last Verified: {row[6] or 'Never'}\n")
                f.write(f"Status: {row[7]}\n")
                f.write("-" * 70 + "\n\n")

        print(f"Report Generated: {output_file}")

#if __name__ == "__main__":
#    print("ChemiDoc File Integrity Monitoring System")
#    print("=========================================\n")
    
#    monitor = FileIntegrityMonitor() 

#    print("\nSystem ready")
#    print("\nQuick Start Guide:")
#    print("1. Register files: monitor.register_file('file.scn)")
#    print("2. Verify files: monitor.verify_file(file.scn')")
#    print("3. Scan Directory: monitor.register_directory('folder_path')")

