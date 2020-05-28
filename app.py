import sqlite3
import flask
import sys
#initialisation
app = flask.Flask(__name__)

#general get db command
def get_db():
    db = sqlite3.connect('Salon.db')
    db.row_factory = sqlite3.Row
    return db

#route to index
@app.route('/')
def home():
    return flask.render_template('index.html')

#add new member
#retrieve fields from html
@app.route('/addnewmember')
def add():
    db = get_db()
    cursor = db.execute("SELECT seq FROM sqlite_sequence WHERE name = 'Member'")
    for line in cursor:
        ID = line['seq']
    ID += 1
    return flask.render_template('addmember.html', ID=ID)

@app.route('/addedmember', methods=['POST'])
def addMember():
    db = get_db()
    cursor = db.execute("SELECT seq FROM sqlite_sequence WHERE name = 'Member'")
    for line in cursor:
        ID = line['seq']
    ID += 1
    
    name = flask.request.form['name'] #string
    gender = flask.request.form['gender'] #radio button
    contact = flask.request.form['contact'] #string
    email = flask.request.form['email'] #string
    address = flask.request.form['address'] #string

    db.execute('INSERT INTO Member VALUES (?, ?, ?, ?, ?, ?)', (ID, name, gender, contact, email, address))
    db.commit()
    db.close()
    return flask.render_template('memberadded.html', name = name)


#update email/mobile no
#get member id, new email, new mobile no
@app.route('/update')
def update():
    db = get_db()
    cursor = db.execute("SELECT seq FROM sqlite_sequence WHERE name = 'Member'")
    for line in cursor:
        ID2 = line['seq']
    if ID2 == 0:
        return flask.render_template('updatedetails.html', ID1=0, ID2=0)
    else:
        return flask.render_template('updatedetails.html', ID1=1, ID2=ID2)

@app.route('/updatedetails', methods=['POST'])
def updatedetails():
    db = get_db()
    ID = flask.request.form['ID']
    if ID == '0':
        statement = 'No such member exists.'
        return flask.render_template('noRecordFound.html', statement=statement)
    email = flask.request.form['email']
    contact = flask.request.form['contact']
    if email == 'NULL':
        db.execute("UPDATE Member SET ContactNo = (?)" +
                   " WHERE MemberID = (?)", (contact, ID))
        db.commit()
    if contact == '10000000':
        db.execute("UPDATE Member SET Email = (?)" +
                   " WHERE MemberID = (?)", (email, ID))
        db.commit()
    if email == 'NULL' and contact == '10000000':
        db.close()
        return flask.render_template('detailsupdated.html', ID=ID)
    db.close()
    return flask.render_template('detailsupdated.html', ID=ID)

    

#add business transaction
#000 is reserved for non-memebers
#get fields
@app.route('/addtransaction')
def addTransaction():
    db = get_db()
    cursor = db.execute("SELECT seq FROM sqlite_sequence WHERE name = 'Member'")
    for line in cursor:
        maxID = line['seq']
    cursor2 = db.execute("SELECT seq FROM sqlite_sequence WHERE name = 'Transactions'")
    for line in cursor2:
        IID = line['seq']
    IID += 1
    return flask.render_template('addTransaction.html', maxID=maxID, IID=IID)

@app.route('/addednewtransaction', methods=['POST'])
def addNewTransaction():
    db = get_db()
    FormData = flask.request.form
    ID = FormData['ID']
    cursor = db.execute("SELECT seq FROM sqlite_sequence WHERE name = 'Transactions'")
    invoice = 0
    for line in cursor:
        invoice = line['seq']
    invoice += 1
    db.execute('INSERT INTO Transactions VALUES(?, ?, NULL, NULL, NULL)', (invoice, ID))
    name = ''

    #calculating total amounts
    servicelist = []
    if 'check1' in FormData:
        servicelist.append(FormData['check1'])
    if 'check2' in FormData:
        servicelist.append(FormData['check2'])
    if 'check3' in FormData:
        servicelist.append(FormData['check3'])
    if 'check4' in FormData:
        servicelist.append(FormData['check4'])
    if 'check5' in FormData:
        servicelist.append(FormData['check5'])
    if 'check6' in FormData:
        servicelist.append(FormData['check6'])
    if 'check7' in FormData:
        servicelist.append(FormData['check7'])
    if 'check8' in FormData:
        servicelist.append(FormData['check8'])
    if 'check9' in FormData:
        servicelist.append(FormData['check9'])
    if servicelist == []:
        return flask.render_template('invalidInput.html')
    total = 0
    for x in range(len(servicelist)):
        price = 0
        cursor3 = db.execute('SELECT Price FROM Service WHERE Type = "'
                             + str(servicelist[x]) + '"')
        for y in cursor3:
            price = y['Price']
        db.execute('INSERT INTO TransactionDetails VALUES (?, ?)', (invoice, (servicelist[x]))) #again placeholder
        total += price
    date = FormData['date']
    if ID == '0':
        name = FormData['fullname']
    else:
        cursor = db.execute("SELECT MemberName FROM Member WHERE MemberID = (?)", (ID,))
        for x in cursor:
            name = x['MemberName']
        cursor2 = db.execute('SELECT Cvalue FROM Constants' + 
                              ' WHERE Constant = "Discount"')
        for z in cursor2:
            discount = z['CValue']
        total = total - (total * discount)
    db.execute('UPDATE Transactions '+
               "SET Date = (?), Name = (?), TotalAmount = (?) " +
               'WHERE InvoiceID = (?)',
               (date, name, total, invoice))
    db.commit()
    
    return flask.render_template('transactionadded.html', ID=invoice)
    

#view daily transactions
#retrieve fields from sql and send
@app.route('/viewDailyTransactions')
def viewDailyTransactions():
    return flask.render_template('viewTransactions.html')

@app.route('/viewTransactionOnDate', methods = ["POST"])
def viewTransactionOnDate():
    db = get_db()
    ondate = flask.request.form['date']
    cursor1 = db.execute('SELECT EXISTS(SELECT 1 FROM Transactions WHERE date = "' + str(ondate) + '")')
    query = 'EXISTS(SELECT 1 FROM Transactions WHERE date = "' + str(ondate) + '")'
    for row in cursor1:
        existence = row[query]
    if existence == 0:
        statement = 'There are no transactions on ' + str(ondate) + '.'
        return flask.render_template('noRecordFound.html', statement=statement)
    cursor = db.execute('SELECT * FROM Transactions WHERE Date = (?)', (ondate,))
    uniqueInvoice = []
    services = []
    rows = []
    for row in cursor:
        uniqueInvoice.append(row['InvoiceID'])
        rows.append(row)
    for x in range(len(uniqueInvoice)):
        cursor2 = db.execute('SELECT Type FROM TransactionDetails WHERE InvoiceID = (?)',
                             (uniqueInvoice[x],))
        tempstr = ''
        for row in cursor2:
            tempstr = tempstr + str(row['Type']) + ', '
        tempstr = tempstr[0:len(tempstr)-2]
        services.append(tempstr)
    return flask.render_template('viewTransactionOnDate.html', ondate=ondate, rows=rows, services=services)


#view monthly sales revenue
#retrieve fields from sql and send
@app.route('/viewMonthlyRevenue')
def viewMonthlyRevenue():
    return flask.render_template('viewMonthlyRevenue.html')

@app.route('/viewRevenueForMonth', methods=['POST'])
def viewRevenueForMonth():
    month = flask.request.form['month']
    year = flask.request.form['year']
    db = get_db()
    rows = db.execute("SELECT SUM(TotalAmount) FROM Transactions " +
                      "WHERE strftime('%m', Date) = (?) " +
                      "AND strftime('%Y', Date) = (?)", (month, year))
    for line in rows:
        revenue = line['SUM(TotalAmount)']
    return flask.render_template('viewRevenueForMonth.html', year=year, month=month, revenue=revenue)
    

#view member transaction history
#retrieve fields from sql and send
@app.route('/viewMemberHistory')
def viewMemberHistory():
    db = get_db()
    cursor = db.execute("SELECT seq FROM sqlite_sequence WHERE name = 'Member'")
    for line in cursor:
        ID2 = line['seq']
    if ID2 == 0:
        return flask.render_template('viewMemberHistory.html', ID1=0, ID2=0)
    else:
        return flask.render_template('viewMemberHistory.html', ID1=1, ID2=ID2)

@app.route('/viewHistoryOfMember', methods=['POST'])
def viewHistoryOfMember():
    memberID = flask.request.form['ID']
    db = get_db()
    if memberID == '0':
        statement = 'No such member exists.'
        return flask.render_template('noRecordFound.html', statement=statement)
    uniqueInvoice = []
    services = []
    dates = []
    totalamts = []
    #joined query from transaction & transdetails
    cursor = db.execute('SELECT * FROM Transactions ' +
                        'WHERE MemberID = (?)', (memberID,))
    for row in cursor:
        name = row['Name']
        if row['InvoiceID'] not in uniqueInvoice:
            uniqueInvoice.append(row['InvoiceID'])
            dates.append(row['Date'])
            totalamts.append(row['TotalAmount'])
            
    for x in range(len(uniqueInvoice)):
        cursor2 = db.execute('SELECT Type FROM TransactionDetails WHERE InvoiceID = (?)',
                             (uniqueInvoice[x],))
        tempstr = ''
        for row in cursor2:
            tempstr = tempstr + str(row['Type']) + ', '
        tempstr = tempstr[0:len(tempstr)-2]
        services.append(tempstr)

            
    return flask.render_template('viewHistoryOfMember.html', ID=memberID, name=name,
                                 invoices=uniqueInvoice, services=services,
                                 dates=dates, totalamts=totalamts)



if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)
