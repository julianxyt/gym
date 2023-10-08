def collateGymStats(input):
    SlashArray = input.split(",")
    print (SlashArray)
    RepArray = []
    KgArray = []
    SplitArray = []
    intArray = []
    for x in SlashArray:
        y = x.split("/")
        for i in y:
            SplitArray.append(i)
    for x in SplitArray:
        intArray.append(int(x))
    RepArray = intArray[::2]
    KgArray = intArray[1::2]
    print(y)
    print(intArray)
    print(RepArray)
    print(KgArray)

def start():
    collateGymStats(input("Enter array: "))

start()