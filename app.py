from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session, g
import sqlite3
import hashlib
import uuid



app = Flask(__name__)
app.secret_key = "very_much_secure_key"

@app.before_request
def before_request():
    g.user = None
    if 'username' in session:
        g.user = session['username']

@app.context_processor
def inject_user():
    return {'user': g.user}

# Define route for the search page
@app.route("/")
def search():

    return render_template("search.html")


@app.route("/result", methods=["POST"])
def result():
    # Get the search term from the form data
    search_term = request.form["product_name"]

    # Open a connection to the SQLite database
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Execute the search query
    cursor.execute(
        """
        SELECT `Ark nr.`, `Shelf nr.`, `Vertical`, `Horizontal`, `Product name`, `Part Category`, `Total on shelf`, `Bemærkniger:`, `Link:`
        FROM data
        WHERE `Product name`=?
    """,
        (search_term,),
    )
    rows = cursor.fetchall()

    # Execute the query to get loaned products
    cursor.execute(
        """
        SELECT product_loaned, name, SUM(quantity_product_loaned)
        FROM user
        WHERE product_loaned=?
        GROUP BY product_loaned, name
    """,
        (search_term,),
    )
    loaned_products = {}
    for row in cursor.fetchall():
        product, name, quantity = row
        if product in loaned_products:
            loaned_products[product][name] = quantity
        else:
            loaned_products[product] = {name: quantity}

    # Close the database connection
    cursor.close()
    conn.close()

    # Render the search results template with the query results and loaned products
    return render_template(
        "search_results.html", rows=rows, loaned_products=loaned_products
    )


# Define route for handling the pre-search request
@app.route("/presearch", methods=["GET"])
def presearch():
    # Get the search term from the query parameters
    search_term = request.args.get("term")

    # Open a connection to the SQLite database
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Execute the pre-search query
    cursor.execute(
        "SELECT DISTINCT `Product name` FROM data WHERE `Product name` LIKE ? LIMIT 15",
        (f"%{search_term}%",),
    )

    results = [result[0] for result in cursor.fetchall()]

    # Close the database connection
    cursor.close()
    conn.close()

    # Return the results as a JSON object
    return jsonify(results)


# Define route for borrowing a product
@app.route("/borrow", methods=["POST"])
def borrow():
    # Get the form data from the request
    product_name = request.form["product_name"]
    quantity = request.form["quantity"]
    name = request.form["navn"]
    ark_nr = request.form["ark_nr"]

    # Open a connection to the SQLite database
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Get the current total on shelf value for the product
    cursor.execute(
        "SELECT `Total on shelf`, `Shelf nr.`, `Vertical`, `Horizontal` FROM data WHERE `Product name` = ? AND `Ark nr.` = ?",
        (product_name, ark_nr),
    )
    result = cursor.fetchone()
    if result is None:
        return "Error: No matching product found on shelf"
    total_on_shelf, shelf_nr, vertical, horizontal = result

    # Calculate the new total on shelf value
    new_total_on_shelf = int(total_on_shelf) - int(quantity)

    # Execute the query to insert a new row into the users table
    cursor.execute(
        "INSERT INTO user (name, product_loaned, quantity_product_loaned) VALUES (?, ?, ?)",
        (name, product_name, quantity),
    )

    # Execute the query to update the total on shelf value for the product in the data table
    cursor.execute(
        "UPDATE data SET `Total on shelf` = ? WHERE `Product name` = ? AND `Ark nr.` = ?",
        (new_total_on_shelf, product_name, ark_nr),
    )

    # Commit the changes and close the database connection
    conn.commit()
    cursor.close()
    conn.close()

    # Flash a message to indicate success
    flash("Du har nu lånt produktet.")

    # Redirect the user back to the home page
    return redirect(url_for("search"))


@app.route("/return", methods=["POST"])
def return_product():
    # Get the form data from the request
    product_name = request.form["product_name"]
    name = request.form["name"]

    # Open a connection to the SQLite database
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Execute the query to get the current total on shelf value for the product
    cursor.execute(
        "SELECT `Total on shelf`, `Shelf nr.`, `Vertical`, `Horizontal` FROM data WHERE `Product name` = ?",
        (product_name,),
    )
    result = cursor.fetchone()
    if result is None:
        return "Error: No matching product found on shelf"
    total_on_shelf, shelf_nr, vertical, horizontal = result

    # Execute the query to get the loaned product and its quantity
    cursor.execute(
        """
        SELECT quantity_product_loaned
        FROM user
        WHERE name = ? AND product_loaned = ?
    """,
        (name, product_name),
    )
    result = cursor.fetchone()
    if result is None:
        return "Error: User has not loaned this product"
    quantity_loaned = int(result[0])

    # Calculate the new quantity loaned value
    new_quantity_loaned = quantity_loaned - 1

    # Update the quantity loaned for the user and product in the users table
    cursor.execute(
        "UPDATE user SET `quantity_product_loaned` = ? WHERE `name` = ? AND `product_loaned` = ?",
        (new_quantity_loaned, name, product_name),
    )

    # Check if the new quantity loaned is zero and delete the loaned product from the users table if necessary
    if new_quantity_loaned == 0:
        cursor.execute(
            "DELETE FROM user WHERE `name` = ? AND `product_loaned` = ?",
            (name, product_name),
        )

    # Calculate the new total on shelf value
    new_total_on_shelf = total_on_shelf + 1

    # Execute the query to update the total on shelf value for the product in the data table
    cursor.execute(
        "UPDATE data SET `Total on shelf` = ? WHERE `Product name` = ?",
        (new_total_on_shelf, product_name),
    )

    # Commit the changes and close the database connection
    conn.commit()
    cursor.close()
    conn.close()

    # Flash the success message and redirect to the search page
    flash("Du har med succes returneret produktet")
    return redirect(url_for("search"))


@app.route("/categories")
def get_categories():
    # Open a connection to the SQLite database
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Execute the query to get the distinct part categories
    cursor.execute("SELECT DISTINCT `Part Category` FROM data")
    categories = [result[0] for result in cursor.fetchall()]

    # Close the database connection
    cursor.close()
    conn.close()

    # Return the categories as a JSON object
    return jsonify(categories)


@app.route("/category-search")
def category_search():
    # Get the category from the query parameters
    category = request.args.get("category")

    # Open a connection to the SQLite database
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Execute the search query
    cursor.execute(
        """
        SELECT `Ark nr.`, `Shelf nr.`, `Vertical`, `Horizontal`, `Product name`, `Part Category`, `Total on shelf`, `Bemærkniger:`, `Link:`
        FROM data
        WHERE `Part Category` = ?
    """,
        (category,),
    )
    rows = cursor.fetchall()

    # Close the database connection
    cursor.close()
    conn.close()

    # Return the results as a JSON object
    return jsonify(rows)


# Her kommer login delen... Av

# Define route for the login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get the username and password from the form
        username = request.form.get('username')
        password = request.form.get('password')

        # Open a connection to the SQLite database
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        # Execute the query to get the salt and hashed password for the given username
        cursor.execute(
            'SELECT salt, password FROM students WHERE username = ?',
            (username,),
        )
        result = cursor.fetchone()

        if result:
            salt, hashed_password = result

            # Check if the password is correct
            if hashlib.sha256((password + salt).encode('utf-8')).hexdigest() == hashed_password:
                # Store the username in the session
                session['username'] = username

                # Redirect the user to the search page
                return redirect(url_for('search'))
            else:
                flash('Ugyldigt brugernavn eller kodeord', 'danger')
        else:
            flash('Ugyldigt brugernavn eller kodeord', 'danger')

        # Close the database connection
        cursor.close()
        conn.close()

    return render_template('login.html')


# Logout route for the user.
@app.route("/logout")
def logout():
    # Clear the user's session
    session.pop("username", None)

    # Redirect the user to the login page
    return redirect(url_for("search"))

# Define route for the admin page
@app.route("/lagerbeholdning")
def opret():
    # Check if the user is an admin
    if "username" not in session or not session["is_admin"]:
        flash("You must be an admin to access this page.")
        return redirect(url_for("search"))

    # Render the admin template
    return render_template("lagerbeholdning.html")


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    # Check if the user is authenticated
    if "username" not in session:
        return redirect(url_for("login"))

    # Get the user's username
    username = session["username"]

    # Handle password change form submission
    if request.method == "POST":
        # Get the old password and new password from the form
        old_password = request.form.get("old_password")
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")

        # Open a connection to the SQLite database
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        # Execute the query to get the salt and hashed password for the given username
        cursor.execute(
            "SELECT salt, password FROM students WHERE username = ?",
            (username,),
        )
        result = cursor.fetchone()

        salt, hashed_password = result

        # Check if the old password is correct
        if hashlib.sha256((old_password + salt).encode("utf-8")).hexdigest() != hashed_password:
            flash("Dit gamle kodeord er ikke korrekt.", 'danger')
            return redirect(url_for("profile"))

        # Validate the new password
        if new_password != confirm_password:
            flash("Den nye adgangskode og bekræftelsesadgangskoden stemmer ikke overens.", 'danger')
            return redirect(url_for("profile"))
        elif len(new_password) < 4:
            flash("Den nye adgangskode skal være på mindst 4 tegn.", 'danger')
            return redirect(url_for("profile"))

        # Hash the new password with a new salt and update the database
        new_salt = uuid.uuid4().hex
        new_hashed_password = hashlib.sha256((new_password + new_salt).encode("utf-8")).hexdigest()
        cursor.execute(
            "UPDATE students SET salt = ?, password = ? WHERE username = ?",
            (new_salt, new_hashed_password, username),
        )
        conn.commit()

        # Close the database connection
        cursor.close()
        conn.close()

        # Flash a message to indicate success
        flash("Dit kodeord er skiftet succesfuldt!", "success")

        # Redirect the user back to the profile page
        return redirect(url_for("profile"))

    return render_template("profile.html", username=username)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        # Query the database to see if the user already has a password set
        cursor.execute("SELECT password FROM students WHERE username = ?", (username,))
        result = cursor.fetchone()

        if result is None:
            flash("Brugernavn ikke fundet i databasen.", 'danger')
        elif result[0] != "":
            flash("Denne bruger har allerede indstillet en adgangskode.", 'danger')
        else:
            # Generate a new salt and hash the password with it
            salt = uuid.uuid4().hex
            hashed_password = hashlib.sha256((password + salt).encode('utf-8')).hexdigest()

            # Update the row in the database with the new salt and hashed password
            cursor.execute("UPDATE students SET salt = ?, password = ? WHERE username = ?", (salt, hashed_password, username))
            conn.commit()

            flash("Dit kodeord er nu oprettet!.", "success")
            return redirect(url_for('login'))

        cursor.close()
        conn.close()

    return render_template('signup.html')

@app.route('/brugerstyring')
def brugerstyring():
    # Check if the user is authenticated
    if "username" not in session:
        flash("Du skal logge ind for at få adgang til denne side.")
        return redirect(url_for("login"))

    # Check if the user is an admin
    is_admin = session.get("is_admin", False)
    if not is_admin:
        flash("Du har ikke adgang til denne side.", 'danger')
        return redirect(url_for("search"))

    # Render the brugerstyring template
    return render_template("brugerstyring.html")



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=True)
