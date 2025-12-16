#This File holds the functions practical lab operations
#the theory is here, but the functions may not work

from file_integrity_monitor import FileIntegrityMonitor

#Registering New Images: Mimicking Daily Use
def register_new_image():
    monitor = FileIntegrityMonitor("lab__image_integrity.db")

    researcher_name = input("Enter Researcher Name: ")
    folder_path = input("Enter Folder Path Containing Images: ")

    print(f"\nRegistering all image files in folder: {folder_path}")
    monitor.register_folder(folder_path, registered_by=researcher_name)
    print("\nRegistration Complete")

#Approving Edits: Run After Making Legal Edits
def approve_edit():
    monitor = FileIntegrityMonitor("lab__image_integrity.db")

    print("\nApprove Image Lab Edit\n")
    filepath = input("Enter File Path of Edited Image: ")
    print("\nCommon edit types:")
    print("1. brightness_adjustment")
    print("2. contrast_adjustment") 
    print("3. gamma_correction")
    print("4. brightness_contrast_combo")
    print("5. cropping")

    choice = input("\nSelect Edit Type (1-5): ")

    edit_type = {
        "1": "brightness_adjustment",
        "2": "contrast_adjustment",
        "3": "gamma_correction",
        "4": "brightness_contrast_combo",
        "5": "cropping"
    }

    edit_description = input("Describe the changes made: ")
    approved_by = input("Your Name: ")

    monitor.approve_edit(
        filepath=filepath,
        edit_type=edit_type.get(choice, "other"),
        edit_description=edit_description,
        approved_by=approved_by,
        software_used="Image Lab"
    )

    print("\nEdit Approved and Logged.")

#Daily Verification for a Whole Folder
def daily_verification():
    monitor = FileIntegrityMonitor("lab__image_integrity.db")

    print("\nDaily Image Verification\n")
    folder_path = input("Enter Folder Path Containing Images for Verification: ")

    results = monitor.verify_folder(folder_path)

    for filepath, result in results.items():
        print(f"{filepath}: {result['message']}")

    print("\nVerification Complete.")
    print("\n1. If legitimate - run approve_single_edit()")
    print("\n2. If tampered - investigate further!")

#Daily Vefification for a Single File
def check_file_status():
    monitor = FileIntegrityMonitor("lab__image_integrity.db")

    print("\nCheck Single Image File Status\n")
    filepath = input("Enter File Path of Image to Verify: ")

    result = monitor.verify_file(filepath)
    print("\nFile Status Result\n")
    print(f"{filepath}: {result['message']}")

    print("\nEdit History")
    monitor.print_edit_history(filepath)

#Generating Weekly Audit Report
def generate_weekly_report():
    monitor = FileIntegrityMonitor("lab_integrity.db")
    
    from datetime import datetime
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"audit_report_{date_str}.txt"
    
    monitor.generate_report(filename)
    print(f"\n Weekly audit report generated: {filename}")
    print("keep for lab records")

#Interactive Menu
def lab_menu():
    monitor = FileIntegrityMonitor("lab__image_integrity.db")

    while True:
        print("\n===============================")
        print("\nChemiDoc Integrity Monitoring System")
        print("\n===============================")
        print("\n1. Register New Images")
        print("2. Approve Image Lab Edit")
        print("3. Run Daily Verification of Image Folder")
        print("4. Check Status of a Single Image File")
        print("5. View Edit History of an Image File")
        print("6. Generate Weekly Audit Report")
        print("7. Exit")

        choice = input("Select an option (1-7): ")

        if choice == "1":
            register_new_image()
        elif choice == "2":
            approve_edit()
        elif choice == "3":
            daily_verification()
        elif choice == "4":
            check_file_status()
        elif choice == "5":
            generate_weekly_report()
        elif choice == "6":
            print("Exiting the system.")
            break
        elif choice == "7":
            print("Exiting the system.")
            break
        else:
            print("Invalid choice. Please select a valid option.")

def typical_daily_workflow():
    monitor = FileIntegrityMonitor("lab_integrity.db")
    
    print("\nNew Images from ChemiDoc")
    # Researcher takes new images
    monitor.register_file("gel_experiment_042.scn", "Dr. Chen")
    monitor.register_file("gel_experiment_043.scn", "Dr. Chen")
    
    print("\nMake adjustments in Image Lab")
    # Researcher improves image quality
    # [Actually edit the file in Image Lab]
    # Then approve the edit:
    monitor.approve_edit(
        "gel_experiment_042.scn",
        "brightness_contrast_combo",
        "Brightness +12%, Contrast +8% to enhance band visibility",
        "Dr. Chen"
    )
    
    print("\n Verification")
    # Verify all files before shutting down
    result = monitor.verify_file("gel_experiment_042.scn")
    print(result["message"])
    
    print("\nGenerate Report")
    # Every Friday, generate audit report
    monitor.generate_report("weekly_report.txt")

if __name__ == "__main__":
    print("ChemiDoc Integrity Monitoring System - Lab Workflow Tools")
    print("\nStarting Interactive Menu")
    lab_menu()