import MySQLdb
import os
from flask import request, send_from_directory, render_template, url_for, redirect

from sms_hunt import app, db_config, stripe_config, team_data, app_config

from sms import Sms
from models_tour import follow_tour
from models_goals import add_data_and_send_sms, charge_stripe

key = stripe_config['stripe_publishable_key']
secret_key = stripe_config['stripe_secret_key']

company = app_config['company']
year = app_config['year']
title = app_config['title']
teams_dic = team_data['club_teams']
teams = teams_dic.values()
teams.sort()


# This needs to be here because teams is imported in validation_functions
from functions.validation_functions import convert_entries, validate_entries

# configuration settings
variable_names = ['team', 'phone_number', 'name']
country_codes = app_config['country_codes'].split(',') # all accepted codes
default_country_code = country_codes[0]  # default code, used to complete numbers

payment = {'amount_integer': app_config['amount_integer'],
           'amount': app_config['amount'],
           'currency': app_config['currency'],
           'currency_html': app_config['currency_html']
           }

default_dic = {'valid': True,
               'value': ''
               }


#######################################
# / start page
#######################################
@app.route('/')
def start(team_dic=default_dic,
          phone_number_dic=default_dic,
          name_dic=default_dic):
    return render_template('start.html',
                           title=title,
                           company=company,
                           year=year,
                           payment=payment,
                           key=key,
                           teams=teams,
                           team=team_dic,
                           phone_number=phone_number_dic,
                           name=name_dic
                           )


#######################################
# / start page for each team
#######################################
@app.route('/team/<team_value>/')
def single_team(team_value,
                phone_number_dic=default_dic,
                name_dic=default_dic):
    team_value = team_value.lower()
    if team_value not in teams_dic.keys():
        return redirect(url_for('page_not_found_manual'))

    return render_template('team.html',
                           title=title,
                           company=company,
                           year=year,
                           payment=payment,
                           key=key,
                           team=str(teams_dic[team_value]),
                           team_value=team_value,
                           phone_number=phone_number_dic,
                           name=name_dic
                           )


#######################################
# /verify
#######################################
@app.route('/verify', methods=['GET'])
def verify_get():
    return redirect(url_for('start'))


@app.route('/verify', methods=['POST'])
def verify_post():
    # get the values from the post
    values_dic = {}
    valid_dic = {}

    # fill, convert and validate entries
    for entry in variable_names:
        values_dic[entry] = request.form[entry]
        values_dic[entry] = convert_entries(entry, values_dic[entry], default_country_code)
        valid_dic[entry] = validate_entries(entry, values_dic[entry], country_codes)

    # reload if non-validated entries exist
    if False in valid_dic.values():
        false_values_dic = {}
        for entry in variable_names:
            false_values_dic[entry + '_dic'] = {'valid': valid_dic[entry],
                                                'value': values_dic[entry]}
        return start(**false_values_dic)

    # Take card payment
    stripe_token = request.form['stripeToken']
    email = request.form['stripeEmail']
    phone_number = values_dic['phone_number']

    charge_successful = charge_stripe(payment=payment,
                                      email=email,
                                      secret_key=secret_key,
                                      stripe_token=stripe_token,
                                      phone_number=phone_number)
    if not charge_successful:
        return redirect(url_for('failure'))

    # Establish database connection
    db = MySQLdb.connect(host=db_config['host'],
                         user=db_config['user'],
                         passwd=db_config['password'],
                         db=db_config['database'])

    add_data_and_send_sms(db, values_dic, email, teams_dic)

    # Commit and close database connection
    db.commit()
    db.close()

    # go to success page
    return redirect(url_for('success'))


#######################################
# /success
#######################################
@app.route('/success/')
def success():
    return render_template('success.html',
                           title=title,
                           company=company,
                           year=year
                           )


#######################################
# /failure
#######################################
@app.route('/failure/')
def failure():
    return render_template('failure.html',
                           title=title,
                           company=company,
                           year=year,

                           )


#######################################
# /about
#######################################
@app.route('/about/')
def about():
    return render_template('about.html',
                           title=title,
                           company=company,
                           year=year,
                           payment=payment
                           )


#######################################
# /contact
#######################################
@app.route('/contact/')
def contact():
    return render_template('contact.html',
                           title=title,
                           company=company,
                           year=year
                           )


#######################################
# /sms_tour POST
#######################################
@app.route('/sms_tour', methods=['POST'])
def sms_tour():
    # Get data from POST request, add to sms class and validate
    sms = Sms(request.form['content'], request.form['sender'])
    sms.validate_content()
    sms.validate_sender()

    # Establish database connection
    db = MySQLdb.connect(host=db_config['host'],
                         user=db_config['user'],
                         passwd=db_config['password'],
                         db=db_config['database'])

    sms.validate_sms_and_get_tour(db)
    # Is the message valid?
    if not sms.is_valid:
        return ''

    # Save sms and follow a tour
    sms.save_message_to_db(db, 'messages')
    follow_tour(db, sms)

    # Commit and close database connection
    db.commit()
    db.close()
    return ''


#######################################
# For control purposes
#######################################
@app.route('/show')
def show_sms_entries():
    from backend.db_functions import select_all

    # Establish database connection
    db = MySQLdb.connect(host=db_config['host'],
                         user=db_config['user'],
                         passwd=db_config['password'],
                         db=db_config['database'])
    df = select_all('messages', db)

    # Commit and close database connection
    db.commit()
    db.close()

    return str(df)


#######################################
# Error 404
#######################################
@app.route('/404')
def page_not_found_manual():
    return render_template('404.html',
                           title=title,
                           company=company,
                           year=year)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html',
                           title=title,
                           company=company,
                           year=year), 404


#######################################
# Favicon (also done in layout.html)
#######################################
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'ico/favicon.ico',
                               mimetype='image/vnd.microsoft.icon')
