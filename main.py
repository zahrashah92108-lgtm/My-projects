import json
import os
import sys

if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

FILE_NAME = os.path.join(BASE_DIR, "students.json")


def calculate_grade(percentage):
    if percentage >= 90:
        return "A+"
    elif percentage >= 80:
        return "A"
    elif percentage >= 70:
        return "B"
    elif percentage >= 60:
        return "C"
    elif percentage >= 50:
        return "D"
    else:
        return "F"


def load_data():
    if not os.path.exists(FILE_NAME):
        return {}
    with open(FILE_NAME, "r") as f:
        return json.load(f)


def save_data(data):
    with open(FILE_NAME, "w") as f:
        json.dump(data, f, indent=4)


def add_student():
    data = load_data()
    roll = input("Roll number: ").strip()

    if roll in data:
        print("This roll number already exists!")
        return

    name = input("Student name: ").strip()
    subjects = {}

    while True:
        try:
            n = int(input("How many subjects? "))
            if n > 0:
                break
            print("Enter a number greater than 0.")
        except ValueError:
            print("Please enter a valid number.")

    for i in range(n):
        sub = input(f"Subject {i+1} name: ").strip()
        while True:
            try:
                marks = float(input(f"Marks for {sub} (0-100): "))
                if 0 <= marks <= 100:
                    break
                print("Marks must be between 0 and 100.")
            except ValueError:
                print("Please enter a valid number.")
        subjects[sub] = marks

    total = sum(subjects.values())
    percentage = total / (n * 100) * 100

    data[roll] = {
        "name": name,
        "subjects": subjects,
        "total": total,
        "percentage": round(percentage, 2),
        "grade": calculate_grade(percentage),
    }
    save_data(data)
    print("Student added successfully!")


def show_result(roll, s):
    print(f"\nRoll No: {roll} | Name: {s['name']}")
    for sub, m in s["subjects"].items():
        print(f"  {sub}: {m}")
    print(f"  Total: {s['total']} | Percentage: {s['percentage']}% | Grade: {s['grade']}")


def view_all():
    data = load_data()
    if not data:
        print("No students found yet.")
        return
    for roll, s in data.items():
        show_result(roll, s)


def search_student():
    data = load_data()
    roll = input("Enter roll number: ").strip()
    if roll in data:
        show_result(roll, data[roll])
    else:
        print("Student not found.")


def delete_student():
    data = load_data()
    roll = input("Enter roll number to delete: ").strip()
    if roll in data:
        del data[roll]
        save_data(data)
        print("Student deleted successfully.")
    else:
        print("Student not found.")


def update_marks():
    data = load_data()
    roll = input("Enter roll number: ").strip()
    if roll not in data:
        print("Student not found.")
        return

    s = data[roll]
    show_result(roll, s)

    sub = input("\nWhich subject do you want to update? ").strip()
    if sub not in s["subjects"]:
        print("Subject not found. Write the name exactly as shown above.")
        return

    while True:
        try:
            marks = float(input(f"New marks for {sub} (0-100): "))
            if 0 <= marks <= 100:
                break
            print("Marks must be between 0 and 100.")
        except ValueError:
            print("Please enter a valid number.")

    s["subjects"][sub] = marks
    n = len(s["subjects"])
    s["total"] = sum(s["subjects"].values())
    s["percentage"] = round(s["total"] / (n * 100) * 100, 2)
    s["grade"] = calculate_grade(s["percentage"])
    save_data(data)
    print("Marks updated successfully!")


def show_topper():
    data = load_data()
    if not data:
        print("No students found yet.")
        return
    roll, s = max(data.items(), key=lambda item: item[1]["percentage"])
    print("\n*** TOPPER ***")
    show_result(roll, s)


def main():
    while True:
        print("\n===== STUDENT RESULT MANAGER =====")
        print("1. Add student")
        print("2. View all results")
        print("3. Search student")
        print("4. Delete student")
        print("5. Update marks")
        print("6. Show topper")
        print("7. Exit")

        choice = input("Choose an option: ").strip()

        if choice == "1":
            add_student()
        elif choice == "2":
            view_all()
        elif choice == "3":
            search_student()
        elif choice == "4":
            delete_student()
        elif choice == "5":
            update_marks()
        elif choice == "6":
            show_topper()
        elif choice == "7":
            print("Goodbye!")
            break
        else:
            print("Invalid option, please try again.")


if __name__ == "__main__":
    main()