from flask import Flask, render_template, request, redirect, flash, url_for
from sqlite3 import connect, Row
import os

database: str = "imageupload.db"

####################################

def postprocess(sql: str) -> bool:
    try:
        db = connect(database)
        cursor = db.cursor()
        cursor.execute(sql)
        db.commit()
        db.close()
        return True
    except Exception as e:
        print("Database error:", e)
        return False
    
def getprocess(sql: str) -> list:
    db = connect(database)
    db.row_factory = Row
    cursor = db.cursor()
    cursor.execute(sql)
    data: list = cursor.fetchall()
    db.close()
    return data
    
def add_student(**kwargs) -> bool:
    try:
        keys: list = list(kwargs.keys())
        values: list = list(kwargs.values())
        flds: str = "`,`".join(keys)
        vals: str = "','".join(str(value).replace("'", "''") for value in values)
        sql: str = f"INSERT INTO `students` (`{flds}`) VALUES ('{vals}')"
        print("Insert SQL:", sql)
        return postprocess(sql)
    except Exception as e:
        print("Add student error:", e)
        return False

def get_students() -> list:
    sql: str = "SELECT * FROM `students`"
    return getprocess(sql)

def get_student(id: int) -> dict:
    sql: str = f"SELECT * FROM `students` WHERE id={id}"
    result = getprocess(sql)
    return result[0] if result else None

def update_student(id: int, **kwargs) -> bool:
    try:
        updates = [f"`{key}`='{str(value).replace('', '')}'" for key, value in kwargs.items()]
        updates_str = ",".join(updates)
        sql: str = f"UPDATE `students` SET {updates_str} WHERE id={id}"
        print("Update SQL:", sql) 
        return postprocess(sql)
    except Exception as e:
        print("Update student error:", e) 
        return False

def delete_student(id: int) -> bool:
    sql: str = f"DELETE FROM `students` WHERE id={id}"
    return postprocess(sql)
    
####################################

app = Flask(__name__)
uploadfolder: str = "static/images/students"
app.config['UPLOAD_FOLDER'] = uploadfolder
app.config['SECRET_KEY'] = "secretkey!@#$##$%%$"

@app.route("/saveinformation", methods=['POST'])
def saveinformation() -> None:
    try:
        student_id = request.form.get('student_id', '')
        
        data = {
            'idno': request.form['idno'],
            'lastname': request.form['lastname'],
            'firstname': request.form['firstname'],
            'course': request.form['course'],
            'level': request.form['level']
        }
       
        file = request.files['imageupload']
        if file and file.filename != '':
            os.makedirs(uploadfolder, exist_ok=True)
            
            filename = uploadfolder+"/"+file.filename
            file.save(filename)
            data['image'] = filename
       
        if student_id:
            student = get_student(int(student_id))
            if not student:
                flash("Student not found")
                return redirect("/")
            
            if 'image' in data and student['image'] and os.path.exists(student['image']):
                try:
                    os.remove(student['image'])
                except Exception as e:
                    print("Error removing old image:", e)
            
            ok = update_student(int(student_id), **data)
            if ok:
                flash("Student Updated Successfully")
            else:
                flash("Failed to update student")
        
        else:
            if 'image' not in data:
                flash("Please select an image")
                return redirect("/")
                
            ok = add_student(**data)
            if ok:
                flash("New Student Added Successfully")
            else:
                flash("Failed to add student")
        
        return redirect("/")
        
    except Exception as e:
        print("Save information error:", e)
        flash("An error occurred while saving the information")
        return redirect("/")

@app.route("/edit/<int:id>")
def edit(id: int) -> None:
    student = get_student(id)
    if student:
        students = get_students()
        return render_template("index.html", 
                             pagetitle="STUDENT REGISTRATION", 
                             students=students,
                             edit_student=student)
    flash("Student not found")
    return redirect("/")

@app.route("/delete/<int:id>")
def delete(id: int) -> None:
    student = get_student(id)
    if student:
        if student['image'] and os.path.exists(student['image']):
            try:
                os.remove(student['image'])
            except Exception as e:
                print("Error removing image:", e)
        
        ok = delete_student(id)
        if ok:
            flash("Student Deleted Successfully")
        else:
            flash("Failed to delete student")
    else:
        flash("Student not found")
    return redirect("/")

@app.route("/")
def index() -> None:
    students = get_students()
    return render_template("index.html", pagetitle="STUDENT REGISTRATION", students=students)

if __name__ == "__main__":
    app.run(debug=True)