from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired

class AdminLoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")


from flask_wtf import FlaskForm
from wtforms import FloatField, IntegerField, SubmitField
from wtforms.validators import DataRequired, NumberRange

class EdgeCaseForm(FlaskForm):
    daily_earning_cap = FloatField("Daily Earning Cap", validators=[DataRequired(), NumberRange(min=0)])
    max_rides_per_day = IntegerField("Max Rides Per Day", validators=[DataRequired(), NumberRange(min=0)])
    cancellation_penalty = FloatField("Cancellation Penalty", validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField("Save Settings")
