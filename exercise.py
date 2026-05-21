# Розвивання віртуального асистента з CLI
from collections import UserDict
from datetime import datetime, timedelta # імпортуємо модуль для роботи з датами, оскільки нам потрібно буде обробляти дні народження


class Field:# базовий клас для полів, який буде використовуватися для створення конкретних типів полів, таких як Name, Phone та Birthday
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return str(self.value)

class Name(Field):
# тут нічого  додавав, оскільки всі перевірки вже виконуються в класі Field
    pass

class Phone(Field): # тут ми перевіряємо, що номер телефону складається з 10 цифр
    def __init__(self, value):
        if not (len(value) == 10 and value.isdigit()): 
            raise ValueError("Phone number must be exactly 10 digits")
        super().__init__(value)

class Birthday(Field):# тут ми перевіряємо, що дата народження введена у форматі DD.MM.YYYY, і якщо вона неправильна, то викидаємо помилку
    def __init__ (self, value):
        try:
            self.value = datetime.strptime(value, "%d.%m.%Y").date()
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")
        
    def __str__(self):# реалізуємо метод для виведення дати у потрібному форматі
        return self.value.strftime("%d.%m.%Y")    
 
class Record: # тут ми релізуємо функціонал запису контакту
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None
    
    def add_phone(self, phone_number):# додаємо номер телефону до контакту
        self.phones.append(Phone(phone_number))
    
    def remove_phone(self, phone_number): # тут ми видаляємо номер телефону з контакту
        phone_obj = self.find_phone(phone_number)
        if phone_obj:
            self.phones.remove(phone_obj)
        else:
            raise ValueError("Phone number not found.")
    
    def edit_phone(self, old_number, new_number): #тут ми змінюємо номер телефону в контакті
        phone_obj = self.find_phone(old_number)
        if phone_obj:
            index = self.phones.index(phone_obj)
            self.phones[index] = Phone(new_number)
        else:
            raise ValueError("Phone not found.")
    
    def find_phone(self, phone_number):# тут ми шукаємо номер телефону в контакті і повертаємо його, якщо він існує
        for phone in self.phones:
            if phone.value == phone_number:
                return phone
        return None
    
    def add_birthday(self, birthday_str):# тут ми додаємо день народження до контакту, використовуючи клас Birthday для перевірки формату дати
        self.birthday = Birthday(birthday_str)
    
    def __str__(self):# реалізуємо метод для виведення інформації про контакт
        return f"Contact name: {self.name.value}, phones: {'; '.join(p.value for p in self.phones)}"
    
class AddressBook(UserDict): # тут ми реалізуємо функціонал адресної книги, яка буде зберігати контакти
    def add_record(self, record): #
        self.data[record.name.value] = record
    
    def find(self, name):
        return self.data.get(name, None)
    
    def delete(self, name):
        if name in self.data:
            del self.data[name]

    def get_upcoming_birthdays(self):
        today = datetime.today().date()
        upcoming_birthdays = []
        for record in self.data.values():
            if record.birthday:
                bday = record.birthday.value
                bday_this_year = bday.replace(year=today.year)
                
                if bday_this_year < today:
                    bday_this_year = bday_this_year.replace(year=today.year + 1)
                
                days_until = (bday_this_year - today).days
                
                if 0 <= days_until <= 7:
                    if bday_this_year.weekday() == 5:
                        bday_this_year += timedelta(days=2)
                    elif bday_this_year.weekday() == 6:
                        bday_this_year += timedelta(days=1)
                    
                    upcoming_birthdays.append({
                        "name": record.name.value,
                        "congratulation_date": bday_this_year.strftime("%d.%m.%Y")
                    })
                    
        return upcoming_birthdays


# --- Функції для обробки команд бота ---
def input_error(func):#
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            return str(e)
        except KeyError:
            return "Contact not found."
        except IndexError:
            return "Not enough arguments. Please check your command."
    return inner

def parse_input(user_input):
    cmd, *args = user_input.split()
    cmd = cmd.strip().lower()
    return cmd, *args

@input_error
def add_contact(args, book: AddressBook):
    name, phone, *_ = args
    record = book.find(name)
    message = "Contact updated."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    if phone:
        record.add_phone(phone)
    return message

@input_error
def change_contact(args, book: AddressBook):
    name, old_phone, new_phone, *_ = args
    record = book.find(name)
    if record is None:
        raise KeyError
    record.edit_phone(old_phone, new_phone)
    return "Contact updated."

@input_error
def show_phone(args, book: AddressBook):
    name, *_ = args
    record = book.find(name)
    if record is None:
        raise KeyError
    return f"{name}'s phones: {'; '.join(p.value for p in record.phones)}"

@input_error
def add_birthday(args, book: AddressBook):
    name, birthday, *_ = args
    record = book.find(name)
    if record is None:
        raise KeyError
    record.add_birthday(birthday)
    return "Birthday added."

@input_error
def show_birthday(args, book: AddressBook):
    name, *_ = args
    record = book.find(name)
    if record is None:
        raise KeyError
    if record.birthday:
        return f"{name}'s birthday is {record.birthday}"
    return f"No birthday added for {name}."

@input_error
def birthdays(args, book: AddressBook):
    upcoming = book.get_upcoming_birthdays()
    if not upcoming:
        return "No upcoming birthdays in the next 7 days."
    return "\n".join([f"{item['name']}: {item['congratulation_date']}" for item in upcoming])


#Головний цикл бота 

def main():
    book = AddressBook()
    print("Welcome to the assistant bot!")
    
    while True:
        user_input = input("Enter a command: ")
        if not user_input.strip():
            continue
            
        command, *args = parse_input(user_input)

        if command in ["close", "exit"]:
            print("Good bye!")
            break
        elif command == "hello":
            print("How can I help you?")
        elif command == "add":
            print(add_contact(args, book))
        elif command == "change":
            print(change_contact(args, book))
        elif command == "phone":
            print(show_phone(args, book))
        elif command == "add-birthday":
            print(add_birthday(args, book))
        elif command == "show-birthday":
            print(show_birthday(args, book))
        elif command == "birthdays":
            print(birthdays(args, book))
        elif command == "all":
            if not book.data:
                print("Address book is empty.")
            else:
                for record in book.data.values():
                    print(record)
        else:
            print("Invalid command.")

if __name__ == "__main__":
    main()