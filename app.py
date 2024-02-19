import os
import sys
from flask import Flask, render_template, request, redirect, flash
from requests import get
from flask_sqlalchemy import SQLAlchemy
#from dotenv import load_dotenv


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///weather.db'  # for database
app.config['SECRET_KEY'] = 'So-Seckrekt'  # for flash messages
db = SQLAlchemy(app)
#load_dotenv()


class City(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

class Stats(db.Model):
    route = db.Column(db.String(100), primary_key=True)
    method = db.Column(db.String(100), primary_key=True)
    day = db.Column(db.Date, primary_key=True)
    count = db.Column(db.Integer, nullable=False)
    
class StatsManager():
    def __init__(self):
        pass

    def inc(self, route, method):
        app.app_context().push()
        print(f"inc {route} {method}")
        from datetime import date
        day = date.today()
        stats = db.session.query(Stats).filter(Stats.route == route, Stats.day == day).first()
        if not stats:
            new_row = Stats(route=route, method=method, day=day, count=1)
            db.session.add(new_row)
        else:
            print(stats)

            db.session.query(Stats).filter(Stats.route == route, Stats.day == day).update({Stats.count: Stats.count + 1})
        db.session.commit()

    def get_stats(self):
        return db.session.query(Stats).all()

statsmgr = StatsManager()

@app.route('/')
def index():
    cities = City.query.all()
    stats = statsmgr.get_stats()
    for stat in stats:
        print(f"Stats are {stat.method} {stat.route} {stat.count}")
    return render_template('index.html', cities=cities)

@app.before_request
def before_request_func():
    print(f"before_request {request.endpoint}")
    if request.endpoint == 'static':
        return

    from threading import Thread
    t = Thread(target=statsmgr.inc, args=(request.path, request.method)) 
    t.start()

@app.route('/add', methods=['POST'])
def add_city():
    print(f"{request.form}")
    if request.method == 'POST':
        city = request.form['city']

        existing_city = City.query.filter_by(name=city).first()
        if existing_city:
            flash('The city has already been added to the list!')
            return redirect('/')

        new_city = City(name=city)
        db.session.add(new_city)
        db.session.commit()

        return redirect('/')

    return render_template('index.html')


@app.route('/delete/<int:city_id>', methods=['POST'])
def delete_city(city_id):
    if request.method == 'POST':
        city = City.query.get(city_id)

        db.session.delete(city)
        db.session.commit()

    return redirect('/')


if __name__ == '__main__':
    with app.app_context():
      db.create_all()

      if len(sys.argv) > 1:
          arg_host, arg_port = sys.argv[1].split(':')
          app.run(host=arg_host, port=arg_port)
      else:
          app.run()
