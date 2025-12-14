def count_substring(string, sub_string):
    # return string.find(sub_string
    c = 0
    l = len(sub_string)
    # print (len(string))
    for i in range(0,len(string)):
        s = string[i:l+i]
        # print (i,l,s)
        if(s == sub_string):
            c+=1
    return c

if __name__ == '__main__':
    string = input().strip()
    sub_string = input().strip()

    count = count_substring(string, sub_string)
    print(count)
