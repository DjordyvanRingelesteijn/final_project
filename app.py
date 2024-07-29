import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from dateutil.relativedelta import relativedelta
from flask_apscheduler import APScheduler
from dateutil.relativedelta import relativedelta

import datetime
import pathlib
import base64


from helpers import apology, login_required

UPLOAD_FOLDER = 'static/project_pictures'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif'}

# Configure application
app = Flask(__name__)

app.debug = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///database.db")

# declare global variablesss  
types = ["Buyer", "Seller","Admin"]
days = [*range(1,32,1)]
months = [*range(1,13,1)]
years = [*range(2024,1900,-1)]
company_types =["Restaurant","Fast food","Pub"]
minimum_interest_rate = 0.0
maximum_interest_rate = 20.0
amount = [*range(0,10250,250)]
rating = [*range(0,6,1)]



@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response



@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    """Show form to create a new project"""
    id = session["user_id"]
    rows = db.execute(
        "SELECT * FROM users WHERE id = ?", id
    )

    xtype = rows[0]['type']
    
    if xtype:
        return render_template("layout.html",type=xtype)
    else:
        return apology("TODO")


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """buy project"""
    id = session["user_id"]
    project_id = request.form.get("project_id")
    amount_bought = int(request.form.get("amount"))

    publish_date = request.form.get("publishing_date")

    app.logger.info(publish_date)

    if amount_bought not in amount:
        return apology("value chosen is not correct", 400)
    
    current_cash = int(db.execute("SELECT * FROM users WHERE id = ?", id)[0]['cash'])

    if current_cash < amount_bought:
        return apology("Not a sufficient amount of cash to make this transaction", 300)
    
    cash_new = current_cash - amount_bought
    

    db.execute("INSERT INTO transactions (user_id, project_id, amount, payment_type) VALUES (?, ?, ?, ?)", id, project_id, amount_bought, 'buy')
    db.execute("UPDATE users SET cash = ? WHERE id = ?", cash_new, id )
    invested_money = int(db.execute("SELECT * FROM project WHERE id = ?", project_id)[0]['invested_money'])  
    db.execute("UPDATE project SET invested_money = ? WHERE id = ?", invested_money + amount_bought, project_id)

    return redirect("/projects")


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():

    id = session["user_id"]

    xtype = db.execute(
        "SELECT * FROM users WHERE id = ?", id
    )[0]['type']

    person_info = db.execute("SELECT * FROM users WHERE id = ?", id)

    return render_template("profile.html", person_info=person_info, type=xtype)


@app.route("/projects")
@login_required
def projects():
    """Show all projects"""
    project_info = db.execute("SELECT * FROM project WHERE reviewed = 1")

    all_project = db.execute("SELECT * FROM project")

    encoded_images = []

    for x in range(len(all_project)):
        encoded_images.append(convertToBase64Data(all_project[x]['picture']))


    id = session["user_id"]
    xtype = db.execute(
        "SELECT * FROM users WHERE id = ?", id
    )[0]['type']

    return render_template("projects.html", project_info=project_info, type=xtype, encoded_images=encoded_images)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        # Ensure username was submitted
        if not username:
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not password:
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", username
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], password
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")



@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        username = request.form.get("username")
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        day = int(request.form.get("day"))
        month = int(request.form.get("month"))
        year = int(request.form.get("year"))
        country = request.form.get("country")
        state = request.form.get("state")
        city = request.form.get("city")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        type = request.form.get("type")

        user = db.execute("SELECT * FROM users where username = ?", username)

        if not username:
            return apology("must provide username", 400)

        elif not first_name:
            return apology("must provide first name", 400)

        elif not last_name:
            return apology("must provide last name", 400)

        elif not day or day < 1 or day > 31:
            return apology("must provide a correct day of birth", 400)

        elif not month or month < 1 or month > 12:
            return apology("must provide a correct month of birth", 400)

        elif not year or year < 1900 or year > 2024:
            return apology("must provide a correct year of birth", 400)

        elif not country:
            return apology("must provide a country", 400)
        
        elif not state:
            return apology("must provide a state", 400)

        elif not city:
            return apology("must provide a city", 400)

        elif not type:
            return apology("must provide a type(buyer/seller)", 400)

        elif not password:
            return apology("must provide password", 400)

        elif not confirmation:
             return apology("must provide confirmation password", 400)

        elif not (password == confirmation):
            return apology("password and confirmation password are not the same", 400)

        elif len(user) == 1:
            return apology("username already exist", 400)

        else:
            date_of_birth = str(day) + '-' + str(month) + '-' + str(year)
            hash = generate_password_hash(password)
            db.execute("INSERT INTO users (username, hash, type, date_of_birth, first_name, last_name, country, state, city) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", username, hash, type, date_of_birth, first_name, last_name, country, state, city)
            return apology("Succes",200)
    else:
        return render_template("register.html", types=types, days=days, months=months, years=years)



@app.route("/password", methods=["GET", "POST"])
@login_required
def password():
    """Change password"""

    id = session["user_id"]
    xtype = db.execute(
        "SELECT * FROM users WHERE id = ?", id
    )[0]['type']
    
    if request.method == "POST":
        old_password = request.form.get("old_password")
        new_password = request.form.get("new_password")
        confirmation = request.form.get("confirmation")


        #check if all fields are filled in and correct

        if not old_password:
            return apology("fill in the old password", 400)

        if not new_password:
            return apology("fill in a new password", 400)
        
        if not confirmation:
            return apology("fill in a confirmation password", 400)

        if new_password != confirmation:
            return apology("new password and confirmation passpword are not the same", 400)

        # compare old password to known password
        hash_old = db.execute("SELECT * FROM users WHERE id = ?", id)[0]['hash']

        if not check_password_hash(hash_old, old_password):
            return apology("old password doesn't match", 400)

        return apology("succes",200)

    else:
        return render_template("password.html", type=xtype)


@app.route("/create", methods=["GET", "POST"])
@login_required
def create():
    id = session["user_id"]
    xtype = db.execute(
        "SELECT * FROM users WHERE id = ?", id
    )[0]['type']

    if request.method == "POST":
        project_name = request.form.get("project_name")
        goal = request.form.get("goal")
        funding_money = request.form.get("funding_money")
        duration = request.form.get("duration")
        interest_rate = float(request.form.get("interest_rate"))
        general_information = request.form.get("general_information")
        detail_information = request.form.get("detail_information")
        company_type = request.form.get("type")



        if not project_name:
            return apology("must provide a project name", 400)
        
        elif not goal:
            return apology("must provide a goal", 400)

        elif not interest_rate or interest_rate < minimum_interest_rate or interest_rate > maximum_interest_rate:
            return apology("must provide correct interest rate", 400)
        
        elif not funding_money:
            return apology("must provide an amount of funding", 400)

        elif not duration:
            return apology("must provide a duration", 400)

        elif not general_information:
            return apology("must provide general information", 400)

        elif not detail_information:
            return apology("must provide detail information", 400)

        elif not company_type:
            return apology("must provide company type ", 400)  


        if 'file' not in request.files:
            return apology("must provide a picture", 400)
                        
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename 
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            path = pathlib.Path().absolute() / "static/project_pictures"
            app.logger.info(path)
            app.logger.info(file.filename)

            with open(path / file.filename, 'rb') as file:
                image = file.read()

        db.execute("INSERT INTO project (name, detail_information, general_information, company_type, goal, interest_rate, user_id, picture, funding_money, duration) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", project_name, detail_information, general_information, company_type, goal, interest_rate, id, image, funding_money, duration) 

        return apology("Succes",200)

    else:
        return render_template("create.html", company_types=company_types, type=xtype)

@app.route("/cash", methods=["GET", "POST"])
@login_required
def cash():
    id = session["user_id"]
    xtype = db.execute(
        "SELECT * FROM users WHERE id = ?", id
    )[0]['type']
    
    if request.method == "POST":
        cash = request.form.get("cash")

        if not cash.isnumeric() or not cash:
            return apology("fill in a positive integer value")

        cash = int(cash)

        if cash < 0:
            return apology("fill in a positive integer value")

        current_cash = db.execute("SELECT * FROM users WHERE id = ?", id)[0]['cash']

        db.execute("UPDATE users SET cash = ? WHERE id = ?", current_cash + cash, id)

        return apology("success", 200)
    else: 
        return render_template("cash.html", type=xtype)

@app.route("/view_project", methods=["GET", "POST"])
@login_required
def view_project():
    """View project"""
    id = session["user_id"]
    xtype = db.execute(
        "SELECT * FROM users WHERE id = ?", id
    )[0]['type']

    # ADD: functionality to not show payment plan if there has no money been invested in the project!!

    project_id = request.form.get("project_id")
    info = db.execute("SELECT * FROM project WHERE id = ?", project_id )[0]
    payment_plan = []

    try:
        investment = db.execute("SELECT SUM(amount) FROM transactions WHERE user_id = ? AND project_id = ?", id, project_id)[0]['SUM(amount)']

        duration = info['duration']      
        interest_rate = info['interest_rate']
        publish_date = info['publish_date']
        publish_date = datetime.datetime.strptime(publish_date, '%Y-%m-%d').date()

        total_interest = 0
        total_total = 0
        
        for x in range(duration):

            payoff = round(investment / duration * (x + 1), 2)
            interest = round(((investment - payoff) * interest_rate * 0.01 / 12), 2)
            total = round((investment / duration) + interest, 2) 
            payment_plan.insert(x, {"payment_number": x + 1, "date":publish_date + relativedelta(months=x), "interest": interest, "payoff": payoff, "total": total})
            total_interest = total_interest + interest
            total_total = total_total + total

        payment_plan.insert(x + 1, {"payment_number": "total", "date": "", "interest": total_interest, "payoff": investment, "total": total_total})

    except:
        pass      

    app.logger.info(payment_plan)
    image = convertToBase64Data(info['picture'])

    return render_template("view_project.html", amount=amount, info=info, type=xtype, image=image, payment_plan=payment_plan)

@app.route("/delayed_payments", methods=["GET", "POST"])
@login_required
def delayed_payments():
    """Show all delayed projects"""
    id = session["user_id"]

    xtype = db.execute(
        "SELECT * FROM users WHERE id = ?", id
    )[0]['type']

    delayed_projects = db.execute("SELECT * FROM project WHERE delayed = TRUE")

    if request.method == "GET":
        return render_template("delayed_payments.html", type=xtype, delayed_projects=delayed_projects)
    


@app.route("/new_project", methods=["GET", "POST"])
@login_required
def new_projects():
    """Show all new projects"""
    id = session["user_id"]

    xtype = db.execute(
        "SELECT * FROM users WHERE id = ?", id
    )[0]['type']

    new_projects = db.execute("SELECT * FROM project ORDER BY reviewed")

    return render_template("new_project.html", type=xtype, new_projects=new_projects, rating=rating)
    

@app.route("/approve", methods=["GET", "POST"])
@login_required
def approved():
    """approve new project"""
    id = session["user_id"]
    if request.method == "POST":

        rated_value = request.form.get("rated_value")
        publish_date = request.form.get("publishing_date")
  
        if not rated_value:
            return apology("please provide a rating")

        if not publish_date:
            return apology("please provide a publishing date")


        #if publish_date < date.today():           
        #    return apology("please provide a publishing date in the future")
        
        project_id = request.form.get("project_id")

        db.execute("UPDATE project SET approved = 1, reviewed = 1, rating = ?, publish_date = ? WHERE id = ?", rated_value, publish_date, project_id)
    
        return redirect("/new_project")
    else:
        return redirect("/new_project")
    
@app.route("/disapprove", methods=["GET", "POST"])
@login_required
def disapproved():
    """disapprove new project"""
    id = session["user_id"]

    project_id = request.form.get("project_id")

    db.execute("UPDATE project SET approved = 0, reviewed = 1 WHERE id = ?", project_id)
    
    return redirect("/new_project")

@app.route("/portfolio", methods=["POST", "GET"])
@login_required
def portfolio():
    """display all bought projects"""
    id = session["user_id"]

    xtype = db.execute(
        "SELECT * FROM users WHERE id = ?", id
    )[0]['type']

    projects = db.execute("SELECT * FROM project WHERE id IN(SELECT project_id FROM transactions WHERE user_id = ?)", id)

    return render_template("portfolio.html", projects=projects, type=xtype)

@app.route("/transactions", methods=["POST", "GET"])
@login_required
def transactions():
    """display all transactions"""
    id = session["user_id"]

    xtype = db.execute(
        "SELECT * FROM users WHERE id = ?", id
    )[0]['type']

    app.logger.info(id)

    transactions = db.execute("SELECT * FROM transactions WHERE user_id = ?", id)

    return render_template("transactions.html", transactions=transactions, type=xtype)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def convertToBinaryData(filename):
    # Convert digital data to binary format
    with open(filename, 'rb') as file:
        blobData = file.read()
    return blobData


def convertToBase64Data(filename):
    encoded_image = (base64.b64encode(filename).decode("utf-8"))
    return encoded_image


scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

#@scheduler.task(trigger='cron', day_of_week='mon-sun', hour=14, minute=34, id='update_DB')
@scheduler.task(trigger='interval', seconds = 10, id='update_DB')

def update_DB():

    projects = db.execute("SELECT id, name, interest_rate, publish_date, user_id, duration, funding_money FROM project")

    for project in projects:
        publish_date = project['publish_date']
        duration = project['duration']
        project_id = project['id']
        interest_rate = project['interest_rate']
        user_id = project['user_id']
        cash_owner = db.execute("SELECT * from users WHERE id = ?", user_id)[0]['cash']
        date_today = datetime.date.today()
        date_today = datetime.date(2024, 11, 24)
        base_date = datetime.datetime.strptime(publish_date, '%Y-%m-%d').date()
        funding_money = project['funding_money']

        date_list = [base_date + relativedelta(months=x) for x in range(duration)]
        #app.logger.info(date_list)
        
        # check if a payment need to be made (every month)
        if date_today in date_list:    
            index = date_list.index(date_today)

            if index > duration:
                app.logger.info('project has been paid off')

            owners = db.execute("SELECT * FROM transactions WHERE project_id = ?", project_id)
            # check if project leader has enough money to pay. if not raise a flag to admins.
            total_payoff = round(funding_money / duration)
            total_interest = round(((funding_money - (total_payoff * index)) * interest_rate * 0.01 / 12), 2)             
            
            cash_needed = total_payoff + total_interest
            if cash_owner < cash_needed:
                db.execute("UPDATE project SET delayed = TRUE WHERE id = ?", project_id)

            app.logger.info(cash_owner)
            
            # pay out all the owners of the project
            
            for owner in owners:
                investment = owner['amount']
                user_id = owner['user_id']
                project_id = owner['project_id']
                payoff = round(investment / duration)
                interest = round(((investment - (payoff * index)) * interest_rate * 0.01 / 12), 2)

                total = round((payoff + interest), 2) 
                
                #update transactions
                db.execute("INSERT INTO transactions (user_id, project_id, amount, payment_type) VALUES (?, ?, ?, ?)", user_id, project_id, total, 'return')
                
                #add total to cash reverse
                cash = db.execute("SELECT * FROM users WHERE id = ?", user_id)[0]['cash']
                new_cash = cash + total
                db.execute("UPDATE users SET cash = ? WHERE id = ?", new_cash, user_id)

                # update the project database (redeemed)
                redeemed_money = db.execute("SELECT * FROM project WHERE id = ?", project_id)[0]['redeemed_money']
                redeemed_money_new = redeemed_money + total
                db.execute("UPDATE project SET redeemed_money = ? WHERE id = ?", redeemed_money_new, project_id)

if __name__ == '__main__':
    app.run(debug=False)