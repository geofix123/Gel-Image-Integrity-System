#This file is to register the files directly
from file_integrity_monitor import FileIntegrityMonitor
monitor = FileIntegrityMonitor("lab_image_integrity.db")


#Registering/Hashing Original Files
print("\nStep 1: Registering Original Image")
#monitor.register_file("Third_Sample.scn", registered_by="Geo")
#monitor.register_file("Project_Sample.scn", registered_by="Geo")
#monitor.register_file("Second_Sample.scn", registered_by="Geo")
monitor.register_file("EECS289 Final Project.pdf", registered_by="Geo")

#Initial Verification
print("\nStep 2: Initial Verification")
#result = monitor.verify_file("Third_Sample.scn")
#print(result["message"])
#result = monitor.verify_file("Project_Sample.scn")
#print(result["message"])
#result = monitor.verify_file("Second_Sample.scn")
#print(result["message"])
result = monitor.verify_file("EECS289 Final Project.pdf")
print(result["message"])

#Simulating Legal File Edits
#print("\nStep 3: Legal File Edits")
#print("Opened file in Image Lab Software")
#rint("Adjustment: Brightness +25%")
#print("File will have a different hash now")

#print("\nStep 4: Verifiction After Legal Edits")
#result = monitor.verify_file("Third_Sample.scn")
#print(result["message"])

#Approving the Legal Edit - Only after Editing
#You would manueally change these
#print("\nStep 5: Approving Legal Edit")
#monitor.approve_edit(
#   filepath="Third_Sample.scn",
#   edit_type="brightness_adjustment",
#    edit_description = "Brightness increased by 25%",
#    approved_by="Geo",
#    software_used="Image Lab"
#)

#Ater Approval: Verifying File
#print("\nStep 6: Verifying After Approval")
#result = monitor.verify_file("Third_Sample.scn")
#print(result)

#Viewing the Complete Editing History
#print("\nStep 7: View Edit History")
#monitor.print_edit_history("Third_Sample.scn")

#Generating a Compliance Report
#print("\nStep 8: Generating Compliance Report")
#monitor.generate_report("compliance_report.txt")




#old commands
#print("---Registering File---")
#monitor.register_file("Project_Sample.scn")
#monitor.register_file("Second_Sample.scn")

#print("\n---Verifying File---")
#result = monitor.verify_file("Project_Sample.scn")
#result = monitor.verify_file("Second_Sample.scn")
#print(result["message"])

#print("\n---File Hashed & Stored---")
