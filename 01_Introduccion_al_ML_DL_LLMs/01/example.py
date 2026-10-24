school_class: dict[str, tuple[int, ...]] = {}

while True:
    name = input("Enter the student's name: ")
    if name == '':
        break
    
    score = int(input("Enter the student's score (0-10): "))
    if score not in range(0, 11):
        break
    
    if name in school_class:
        school_class[name] += (score,)
    else:
        school_class[name] = (score,)
        
for name in sorted(school_class.keys()):
    adding = 0
    counter = 0
    for score in school_class[name]:
        adding += score
        counter += 1
    print(name, ":", adding / counter)

try:
    with open("school_class.txt", "w") as file:
        for name in sorted(school_class.keys()):
            adding = 0
            counter = 0
            for score in school_class[name]:
                adding += score
                counter += 1
            file.write(f"{name} : {adding / counter}\n")
except ZeroDivisionError:
    print("An error occurred while writing to the file.")


def read_file():
    try:
        with open("school_class.txt", "r") as file:
            for line in file:
                print(line.strip())
    except FileNotFoundError:
        print("The file does not exist.")