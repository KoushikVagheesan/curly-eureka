from tkinter import *
import os
import socket
global resi
def main():
	file = open(fi.get(),"rb")
	content = file.read()
	s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
	s.connect(('127.0.0.1',1337))
	s.send(content) #send file contents to server
	print("file sent")
	data = int(s.recv(512).decode()) #receive info from server regarding the file
	print(data)
	if(data==1):
          resi.insert(END,'NO')
	else:
	  resi.insert(END,'YES')		
#to create GUI
top=Tk()
top.geometry('400x400')
top.title('Malware Detection')
fn=Label(top,text='Filename:')
fn.place(x=15,y=50)
rsu=Label(top,text='Does your file contain malware:')
rsu.place(x=15,y=100)
fi=Entry(top,width=20)
fi.place(x=80,y=50)
resi=Text(top,height=1,width=15)
resi.place(x=80,y=120)
b=Button(top,text='Send',width=8,command= lambda:main())
b.place(x=100,y=200)
top.mainloop()
