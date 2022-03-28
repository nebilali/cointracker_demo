from flask import (
    Blueprint,
    request,
    abort,
    make_response,
    jsonify,
    Response,
)

from app.db import get_db
from absl import logging
from .util import validate_account_id, validate_or_abort
from .transactions import remove_transactions

bp = Blueprint("address", __name__, url_prefix="/address")


@bp.route("/add", methods=["POST"])
def add_accounts():
    account_ids = request.args.get("account_ids").split("|")
    validate_or_abort(account_ids)
    db = get_db()

    alread_existing_accounts = []
    for account_id in account_ids:
        try:
            db.execute("""
                INSERT INTO accounts (account_id)
                VALUES (?)
                """, (account_id,),
            )
            db.commit()
        except db.IntegrityError:
            message = "account_id alredy exists: {}".format(account_id)
            alread_existing_accounts.append(account_id)
            logging.warning(message)
        except:
            message = "Unknown DB error."
            logging.error(message)
            # Internal server error.
            abort(500, message)

    message = None
    if len(alread_existing_accounts) == 0:
        message = 'Ok.'
    else:
        message = "Account ids alredy exists: {}".format(','.join(alread_existing_accounts))
    return make_response(jsonify({"message": message}), 200)


@bp.route("/remove", methods=["DELETE"])
def remove():
    account_ids = request.args.get("account_ids").split("|")
    validate_or_abort(account_ids)
    db = get_db()

    for account_id in account_ids:
        try:
            db.execute("""
                DELETE FROM accounts
                WHERE account_id = ?;
                """, (account_id,),
            )
            db.commit()
        except:
            message = "Unknown DB error."
            logging.error(message)
            # Internal server error.
            abort(500, message)

        remove_transactions(account_id)
    
    return Response(status=200)


@bp.route("/balance", methods=["GET"])
def balance():
    account_ids = request.args.get("account_ids").split("|")
    validate_or_abort(account_ids)
    balance_sum = 0
    balance_map = {}
    
    for account_id in account_ids:
        balance = get_account_balance(account_id)
        balance_map[account_id] = balance
        balance_sum += get_account_balance(account_id)

    balance_map['total'] = balance_sum
    return make_response(jsonify(balance_map), 200)


def get_account_balance(account_id):
    db = get_db()
    row = db.execute("""
        SELECT balance 
        FROM accounts 
        WHERE account_id = ?;
        """, (account_id,)
    ).fetchone()

    if row is None:
        message = "account_id {} doesn't exist".format(account_id)
        logging.error(message)
        # Not found error code.
        abort(404, message)

    return row[0]

