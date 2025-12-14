import re

# arr = ["vineet <vineet.iitg@gmail.co>","vineet <vineet.iitg@gmail.c>","vineet <vineet.iitg@gmail.com>"]
# arr = ["dheeraj <dheeraj-234@gmail.com>","crap <itsallcrap>","harsh <harsh_1234@rediff.in>","kumal <kunal_shin@iop.az>","mattp <matt23@@india.in>","harsh <.harsh_1234@rediff.in>","harsh <-harsh_1234@rediff.in>"]
# arr = ["this <is@valid.com>","this <is_som@radom.stuff>","this <is_it@valid.com>","this <_is@notvalid.com>"]
arr = ["shashank <shashank@9mail.com>","shashank <shashank@gmail.9om>","shashank <shashank@gma_il.com>","shashank <shashank@mail.moc>","shashank <shashank@company-mail.com>","shashank <shashank@companymail.c_o>"]
# Match names.
for element in arr:
     # m = re.match(r"(^[a-zA-Z]+(\s)+(<[^<0-9\.\-\_])+([a-zA-Z0-9_.+-])+(@[^@])+([a-zA-Z0-9-])+(\.[^\.@])+([a-z])+([>])$)", element)
     m = re.match(r"(^[a-zA-Z]+(\s)+(<[^<0-9\.\-\_])+([\w\.\+\-]+\@[a-z]+\.[a-z]{1,3}[>])$)", element)
     if m:
        print(m.group())
     # else: print("NO")
