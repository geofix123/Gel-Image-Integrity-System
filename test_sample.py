from file_integrity_monitor import FileIntegrityMonitor

monitor = FileIntegrityMonitor("file_integrity.db")

print("---Registering File---")
monitor.register_file("Project_Sample.scn")

print("\n---Verifying File---")
result = monitor.verify_file("Project_Sample.scn")
print(result["message"])

print("\n---File Hashed & Stored---")