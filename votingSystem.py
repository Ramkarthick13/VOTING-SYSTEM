from tkinter import *
import tkinter.messagebox as messagebox
import sqlite3

def center_window(root, width, height):
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    
    root.geometry(f"{width}x{height}+{x}+{y}")

def create_db():
    conn = sqlite3.connect('votes.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS votes (
            party TEXT,
            count INTEGER
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            userid INTEGER PRIMARY KEY,
            password TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS votes_cast (
            userid INTEGER PRIMARY KEY
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin (
            adminid INTEGER PRIMARY KEY,
            password TEXT
        )
    ''')

    for i in range(1, 26):
        cursor.execute(f'INSERT OR IGNORE INTO users (userid, password) VALUES ({i}, "password{i}")')
        

    cursor.execute('INSERT OR IGNORE INTO admin (adminid, password) VALUES (777, "adminpass")')
    conn.commit()
    conn.close()

def update_vote(party):
    conn = sqlite3.connect('votes.db')
    cursor = conn.cursor()
    cursor.execute('SELECT count FROM votes WHERE party = ?', (party,))
    result = cursor.fetchone()
    if result:
        cursor.execute('UPDATE votes SET count = count + 1 WHERE party = ?', (party,))
    else:
        cursor.execute('INSERT INTO votes (party, count) VALUES (?, 1)', (party,))
    conn.commit()
    conn.close()

def get_votes():
    conn = sqlite3.connect('votes.db')
    cursor = conn.cursor()
    cursor.execute('SELECT party, count FROM votes')
    votes = cursor.fetchall()
    conn.close()
    return {party: count for party, count in votes}

def authenticate_user(userid, password):
    conn = sqlite3.connect('votes.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE userid = ? AND password = ?', (userid, password))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def authenticate_admin(adminid, password):
    conn = sqlite3.connect('votes.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM admin WHERE adminid = ? AND password = ?', (adminid, password))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def has_voted(userid):
    conn = sqlite3.connect('votes.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM votes_cast WHERE userid = ?', (userid,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def mark_as_voted(userid):
    conn = sqlite3.connect('votes.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO votes_cast (userid) VALUES (?)', (userid,))
    conn.commit()
    conn.close()

def close_voting():
    messagebox.showinfo("Voting Closed", "Voting has been closed by the admin.")
    global voting_open
    voting_open = False

class User:
    def __init__(self):
        self.root = Tk()
        self.root.title("Login")
        center_window(self.root, 300, 200)
        
        self.userid = IntVar()
        self.password = StringVar()
        
        Label(self.root, text="USERID", bg="white", fg="black").place(relx=0.5, rely=0.4, anchor=CENTER)
        Label(self.root, text="PASSWORD", bg="white", fg="black").place(relx=0.5, rely=0.5, anchor=CENTER)
        Entry(self.root, textvariable=self.userid).place(relx=0.6, rely=0.4, anchor=CENTER)
        Entry(self.root, show='*', textvariable=self.password).place(relx=0.6, rely=0.5, anchor=CENTER)
        Button(self.root, text="User Login", command=self.check_credentials).place(relx=0.3, rely=0.6, anchor=CENTER)
        Button(self.root, text="Admin Login", command=self.admin_login).place(relx=0.7, rely=0.6, anchor=CENTER)
        
        self.root.mainloop()
        
    def check_credentials(self):
        userid = self.userid.get()
        password = self.password.get()
        
        if authenticate_user(userid, password):
            if has_voted(userid):
                messagebox.showerror("Error", "You have already voted.")
            else:
                self.root.destroy()
                PartyName(userid)
        else:
            messagebox.showerror("Error", "Invalid credentials. Please try again.")

    def admin_login(self):
        adminid = self.userid.get()
        password = self.password.get()

        if authenticate_admin(adminid, password):
            self.root.destroy()
            AdminDashboard()
        else:
            messagebox.showerror("Error", "Invalid admin credentials. Please try again.")

class PartyName:
    def __init__(self, userid):
        self.userid = userid
        self.root = Tk()
        self.root.title("Select Party")
        center_window(self.root, 400, 200)
        
        self.option=['DMK','ADMK','BJP','TVK','NTK','NOTA']
        self.selected_party = StringVar()
        
        frame = Frame(self.root, padx=20, pady=20)
        frame.pack(expand=True)
        
        Label(frame, text="Select Party", font=("Arial", 16), padx=10, pady=10).grid(row=0, column=0, columnspan=2)
        OptionMenu(frame, self.selected_party, *self.option).grid(row=1, column=0, padx=10, pady=10)
        Button(frame, text="Vote", command=self.cast_vote, padx=10, pady=10).grid(row=1, column=1, padx=10, pady=10)
        
        self.root.mainloop()
        
    def cast_vote(self):
        if voting_open:
            selected_party = self.selected_party.get()
            update_vote(selected_party)
            mark_as_voted(self.userid)
            messagebox.showinfo("Success", "Vote cast successfully!")
            
            votes = get_votes()
            leading_party = max(votes, key=votes.get)
            self.root.destroy()
            ResultWindow(votes, leading_party)
        else:
            messagebox.showerror("Error", "Voting has been closed by the admin.")

class AdminDashboard:
    def __init__(self):
        self.root = Tk()
        self.root.title("Admin Dashboard")
        center_window(self.root, 300, 200)
        
        Button(self.root, text="Close Voting", command=close_voting, padx=20, pady=10).pack(pady=10)
        Button(self.root, text="View Vote Count", command=self.view_vote_count, padx=20, pady=10).pack(pady=10)
        
        self.root.mainloop()
    
    def view_vote_count(self):
        votes = get_votes()
        CountWindow(votes)

class ResultWindow:
    def __init__(self, votes, leading_party):
        self.votes = votes
        self.leading_party = leading_party
        
        self.root = Tk()
        self.root.title("Leading Party")
        center_window(self.root, 300, 150)
        
        Label(self.root, text=f"{self.leading_party} is the leading party!", font=("Arial", 14, "bold"), padx=20, pady=20).pack()
        
        Button(self.root, text="View Count", command=self.show_count, padx=10, pady=5).pack(pady=10)
        
        self.root.mainloop()
    
    def show_count(self):
        self.root.destroy()
        CountWindow(self.votes)

class CountWindow:
    def __init__(self, votes):
        self.votes = votes
        
        self.root = Tk()
        self.root.title("Party Votes Count")
        center_window(self.root, 300, 250)
        
        Label(self.root, text="Party Votes Count", font=("Arial", 16), padx=20, pady=10).pack()
        
        for party, count in self.votes.items():
            Label(self.root, text=f"{party}: {count} votes").pack(pady=5)
        self.root.mainloop()

voting_open = True

create_db()
User()

