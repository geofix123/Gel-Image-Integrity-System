"""
Project: ChemiDoc File Integrity Monitoring System
Purpose: Verifies the integrity of ChemiDoc Imaging Files
Purpose 2: Tracks Legal vs Illegal Edits
Author: Geovany Serrano 
"""

import hashlib
import sqlite3 
import os
import json
from datetime import datetime
from pathlib import Path


class FileIntegrityMonitor:
    def __init__(self, db_path = "lab_image_integrity.db"):
        self.db_path = db_path
        self.init_database()
        
    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        #Main Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS file_hashes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                filepath TEXT UNIQUE NOT NULL,
                original_hash TEXT NOT NULL,
                current_hash TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                created_date TEXT NOT NULL,
                last_verified TEXT,
                last_modified TEXT,
                status TEXT DEFAULT 'Original',
                notes TEXT
            )
        ''')

        #Edit History Table        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS edit_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id INTEGER NOT NULL,
                edit_date TEXT NOT NULL,
                edit_type TEXT NOT NULL,
                edit_description TEXT NOT NULL,
                previous_hash TEXT NOT NULL,
                new_hash TEXT NOT NULL,
                approved_by TEXT NOT NULL,
                software_used TEXT DEFAULT 'Image Lab',
                FOREIGN KEY (file_id) REFERENCES file_hashes(id)
            )
        ''')

        conn.commit()
        conn.close()
        print(f"Database initialized: {self.db_path}")

    def calculate_hash(self, filepath, algorithm = 'sha256'):
        hash_func = hashlib.new(algorithm)

        #this part converts the scn into bytes
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
        
    def register_file(self, filepath, registered_by = "Lab Technician"):
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
                INSERT INTO file_hashes 
                (filename, filepath, original_hash, current_hash, file_size, created_date, status, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (filename, filepath, file_hash, file_hash, file_size, created_date,
                  'Original', f'Registered by {registered_by}'))

            conn.commit()

            print(f" Registered: {filename}")
            print(f" Original Hash: {file_hash[:16]}...")
            print(f" Status: Original \n")
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

        cursor.execute('''
            SELECT id,
            filename, original_hash, current_hash, file_size, status 
            FROM file_hashes WHERE filepath = ? 
            ''', (filepath,))
        result = cursor.fetchone()

        if not result:
            conn.close()
            return {"status": "unregistered", "message": "File not in database"}
         
        file_id, filename, original_hash, stored_current_hash, stored_size, status = result 
        current_size = os.path.getsize(filepath)

        #Update when last verified
        cursor.execute('''
            UPDATE file_hashes 
            SET last_verified = ?
            WHERE filepath = ?
        ''', (datetime.now().isoformat(), filepath))
         
        conn.commit()
        #conn.close()

        #Checking file for modifications
        if current_hash == stored_current_hash:
            conn.close()
            return {
                "status": "verified",
                "filename": filename,
                "message": f"File integrity verified - Status: {status}",
                "file_status":status,
                "original_hash": original_hash[:16] + "...",
                "current_hash": current_hash[:16] + "...",
            }
        
        #If it has been changed check if Legal/Approved
        cursor.execute('''
            SELECT COUNT(*) FROM edit_history
            WHERE file_id = ? AND new_hash = ?
            ''', (file_id, current_hash))

        is_approved_edit = cursor.fetchone()[0] > 0

        if is_approved_edit:
            conn.close()
            return {
                "status": "approved_modifications",
                "filename": filename,
                "message": "File Modified Legally",
                "file_status":"Approved Edit",
            }

        else:
            conn.close()
            return {
                "status": "tampered",
                "filename": filename,
                "message": " Warning: File has been tampered with!!!",
                "details": {
                    "hash_match": original_hash[:16] + "...",
                    "expected_hash": stored_current_hash[:16] + "...",
                    "current_hash": current_hash[:16] + "...",
                    "original_size": stored_size,
                    "current_size": current_size
                },
                "action_required": "Review changes or approve edit if legitimate"
            }
        
    #New Function for approving
    def approve_edit(self, filepath, edit_type, edit_description, approved_by, software_used = "Image Lab"):
        if not os.path.exists(filepath):
            print(f"Error: File not found - {filepath}")
            return False

        new_hash = self.calculate_hash(filepath)
        if not new_hash:
            return False

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                SELECT id, current_hash, status FROM file_hashes WHERE filepath = ?
            ''', (filepath,))
            result = cursor.fetchone()

            if not result:
                print(f"Error: File not registered - {filepath}")
                return False

            file_id, previous_hash, current_hash = result
         
            if new_hash == previous_hash:
                print(f"Note: File hash unchanged - no edit to approve")
                return False 
            
            edit_date = datetime.now().isoformat()
            cursor.execute('''
                INSERT INTO edit_history 
                (file_id, edit_date, edit_type, edit_description, previous_hash, new_hash, approved_by, software_used)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (file_id, edit_date, edit_type, edit_description, previous_hash, new_hash, approved_by, software_used))
                           
            #Updating current hash ans status to the main table
            cursor.execute('''
                UPDATE  file_hashes
                SET current_hash = ?,
                    status = 'Approved_Edit',
                    last_modified = ?,
                    notes = ?
                WHERE id = ?
            ''', (new_hash, edit_date, f'Last edit: {edit_type} approved by {approved_by}', file_id))

            conn.commit()
            print(f"Edit approved for: {os.path.basename(filepath)}\n")
            print(f"Edit tyep: {edit_type}\n") 
            print(f"Description: {edit_description}\n")
            print(f"Approved by: {approved_by}\n")
            print(f"New Hash: {new_hash[:16]}...\n")
            return True

        except Exception as e: 
            print(f"Error: approving edit: {e}")
            return False
        finally:
            conn.close()


    #Another New Function
    def get_edit_history(self, filepath):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id FROM file_hashes WHERE filepath = ?
        ''', (filepath,))
        result = cursor.fetchone()

        if not result:
            print(f"Error: File not registered - {filepath}")
            conn.close()
            return []

        file_id = result[0]
        cursor.execute('''
            SELECT edit_date, edit_type, edit_description, approved_by, software_used
            FROM edit_history 
            WHERE file_id = ? 
            ORDER BY edit_date DESC
        ''', (file_id,))

        history = cursor.fetchall()
        conn.close()

        return history
    
    #Another New Function 
    def print_edit_history(self, filepath):
        history = self.get_edit_history(filepath)

        if not history:
            print(f"\nNo edit history found for: {os.path.basename(filepath)}")
            return

        print("-" * 50)
        print(f"Edit History for {os.path.basename(filepath)}:")

        for i, (edit_date, edit_type, edit_description, approved_by, software_used) in enumerate(history, start=1):
            date_obj = datetime.fromisoformat(edit_date)
            print(f"\nEdit #{i}:")
            print(f"Date: {date_obj.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Type: {edit_type}")
            print(f"Description: {edit_description}")
            print(f"Approved by: {approved_by}")
            print(f"Software Used: {software_used}")
            print("-" * 50)

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
        approved_edit_count = 0
        unauthorized_count = 0

        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith(file_extension):
                    filepath = os.path.join(root, file)
                    result = self.verify_file(filepath)

                    if result["status"] == "verified":
                        print(f" {file}: CLEAN ({result['file_status']})")
                        verified_count += 1
                    elif result["status"] == "approved_modifications":
                        print(f" {file}: Approved Edit")
                        approved_edit_count += 1
                    elif result["status"] == "unauthorized_change":
                        print(f" {file}: Unauthorized Change Detected!")
                        unauthorized_count += 1
                    elif result["status"] == "unregistered":
                        print(f" {file}: Unregistered File")

        print(f"\n ---Verification Summary---")
        print(f"Clean Files: {verified_count}")
        print(f"Approved Edits: {approved_edit_count}")
        print(f"Unauthorized Changes: {unauthorized_count}")

    def generate_report(self, output_file = "integrity_report.txt"):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT f.*,
                    (SELECT COUNT(*) FROM edit_history e WHERE e.file_id = id) AS edit_count
            FROM file_hashes f
            ORDER BY f.created_date DESC
                       ''')
        results = cursor.fetchall()

        with open(output_file, 'w') as f:
            f.write("-" * 70 + "\n")
            f.write("FILE INTEGRITY MONITORING REPORT \n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} \n")
            f.write("-" * 70 + "\n\n")

            for row in results:
                f.write(f"Filename: {row[1]}\n")
                f.write(f"Path: {row[2]}\n")
                f.write(f"Original Hash: {row[3]}\n")
                f.write(f"Current Hash: {row[4]} bytes\n")
                f.write(f"Size: {row[5]} bytes\n")
                f.write(f"Registered: {row[6]}\n")
                f.write(f"Last Verified: {row[7] or 'Never'}\n")
                f.write(f"Last Modified: {row[8] or 'Never'}\n")
                f.write(f"Status: {row[9]}\n")
                f.write(f"Notes: {row[10] or 'None'}\n")
                f.write(f"Total Approved Edits: {row[11]}\n")
                f.write("-" * 70 + "\n\n")

                cursor.execute('''
                    SELECT edit_date, edit_type, edit_description, approved_by
                    FROM edit_history WHERE file_id = ?
                    ORDER BY edit_date ASC
                ''', (row[0],))
                edits = cursor.fetchall()

                if edits:
                    f.write("\nEdit History:\n")
                    for i, (date, etype, desc, approver) in enumerate(edits, start=1):
                        f.write(f"{i}. {date} - {etype}\n")
                        f.write(f"Description: {desc}\n")
                        f.write(f"Approved by: {approver}\n")
                f.write("-" * 70 + "\n\n")

        conn.close()
        print(f"Report Generated: {output_file}")


    #Adding a remove function 
    def remove_file(self, filepath):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM file_hashes WHERE filepath = ?', (filepath,))
        conn.commit()
        conn.close()
        print(f"File removed from monitoring: {filepath}")

#if __name__ == "__main__":
#    print("ChemiDoc File Integrity Monitoring System")
#    print("=========================================\n")
    
#    monitor = FileIntegrityMonitor() 

#    print("\nSystem ready")
#    print("\nQuick Start Guide:")
#    print("1. Register files: monitor.register_file('file.scn)")
#    print("2. Verify files: monitor.verify_file(file.scn')")
#    print("3. Scan Directory: monitor.register_directory('folder_path')")

