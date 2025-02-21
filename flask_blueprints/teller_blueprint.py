from flask import Blueprint, render_template, request, redirect, url_for, session, flash

teller_blueprint = Blueprint("teller_blueprint", __name__, static_folder="static", template_folder="template")

@teller_blueprint.route("/customer", methods=["POST", "GET"])
def teller():
    return "Teller Page"