from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, DecimalField, SelectField, SubmitField
from wtforms.validators import Regexp, Optional, Length, Email, NumberRange, DataRequired

# -----------------------------------------------------------------------------
# TellerSettingsForm: Tellers can modify their personal information.
# -----------------------------------------------------------------------------
class TellerSettingsForm(FlaskForm):
    first_name = StringField('First Name', validators=[Optional(), Length(max=50)])
    last_name = StringField('Last Name', validators=[Optional(), Length(max=50)])
    phone = StringField('Phone', validators=[Optional(), Regexp(r'^\d{3}-\d{3}-\d{4}$')])
    email = StringField('Email', validators=[Optional(), Email()])
    address = StringField('Address', validators=[Optional(), Length(max=100)])
    username = StringField('Username', validators=[Optional(), Length(min=3, max=25)])
    password = PasswordField('New Password', validators=[Optional(), Length(min=8)])
    current_password = PasswordField('Current Password', validators=[Optional()])

# -----------------------------------------------------------------------------
# AdminSettingsForm: Modify admin password only.
# -----------------------------------------------------------------------------
class AdminSettingsForm(FlaskForm):
    email = StringField('Email')
    password = PasswordField('New Password', validators=[Optional(), Length(min=8)])
    current_password = PasswordField('Current Password', validators=[Optional()])


class AccountTransactionForm(FlaskForm):
    """
    Base form for common account transactions (Deposit/Withdraw).
    Includes account selection and amount field.
    """
    account_id: SelectField = SelectField(
        'Select Account',
        validators=[DataRequired()],
        coerce=str  # Can change to int if account IDs are integers
    )
    amount: DecimalField = DecimalField(
        'Amount',
        places=2,  # Ensures 2 decimal places for currency
        validators=[
            DataRequired(),
            NumberRange(min=0.01, message="Amount must be greater than zero.")
        ]
    )


class DepositForm(AccountTransactionForm):
    """
    Form for making deposits to a selected account.
    """
    submit: SubmitField = SubmitField('Deposit')


class WithdrawForm(AccountTransactionForm):
    """
    Form for withdrawing funds from a selected account.
    """
    submit: SubmitField = SubmitField('Withdraw')