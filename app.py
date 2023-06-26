from flask import Flask, render_template, request, redirect, flash
from requests import get
from flask_sqlalchemy import SQLAlchemy
import sys


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///weather.db'  # for database
app.config['SECRET_KEY'] = 'So-Seckrekt'  # for flash messages
db = SQLAlchemy(app)


class City(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)


@app.route('/')
def index():
    cities = City.query.all()
    weather_info_list = []
    api_key = '3e92ae34eb4da94c70cc1a85fecc58a6'
    for city in cities:
        response = get(f'http://api.openweathermap.org/data/2.5/weather?q={city.name}&appid={api_key}')
        if response.status_code == 200:
            weather_info = response.json()

            dict_with_weather_info = {
                'id': city.id,
                'city': city.name,
                'temp': round(weather_info['main']['temp'] - 273.15),
                'state': weather_info['weather'][0]['main']
            }
            weather_info_list.append(dict_with_weather_info)

    return render_template('index.html', weather=weather_info_list)


@app.route('/add', methods=['POST'])
def add_city():
    if request.method == 'POST':
        city = request.form['city']

        existing_city = City.query.filter_by(name=city).first()
        if existing_city:
            flash('The city has already been added to the list!')
            return redirect('/')
        elif not get(f'http://api.openweathermap.org/data/2.5/weather?q={city}&appid=3e92ae34eb4da94c70cc1a85fecc58a6').status_code == 200:
            flash("The city doesn't exist!")
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