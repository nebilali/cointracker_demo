from flask import (
    Blueprint,
    request,
    url_for,
    abort,
    make_response,
    jsonify,
    Response,
)

from app.db import get_db
from absl import logging
from .util import validate_or_abort
from blockchain import blockexplorer

bp = Blueprint("tx", __name__)


@bp.route("/transactions", methods=["GET"])
def get_transactions():
    db = get_db()
    account_ids = request.args.get("account_ids").split("|")
    validate_or_abort(account_ids)

    # Setting limit = -1 is querying for all rows. (i.e. unlimited)
    limit = int(request.args.get("limit", -1))
    offset = int(request.args.get("offset", 0))

    data = []
    for account_id in account_ids:
        try:
            rows = db.execute("""
                SELECT * 
                FROM transactions 
                WHERE account_id = ?
                LIMIT ?, ?;
                """, (account_id, offset*limit, limit,)
            ).fetchall()
        except Exception as e:
            # Internal server error.
            abort(500, e)

        for tx_id, account_id, value_change in tuple(rows):
            tx_data = {
                "tx_id": tx_id,
                "account_id": account_id,
                "value_change": value_change,
            }
            data.append(tx_data)

    return make_response(jsonify(data), 200)


# Remove all transactions for this account.
def remove_transactions(account_id):
    db = get_db()

    try:
        db.execute(""" 
            DELETE FROM transactions WHERE account_id = ?
            """, (account_id,),
            )
        db.commit()
    except Exception as e:
        abort(500, e)



@bp.route("/sync", methods=["POST"])
def sync_accounts():
    account_ids = request.args.get("account_ids").split("|")
    validate_or_abort(account_ids)

    for account_id in account_ids:
        sync_account(account_id)
        
    return Response(status=200)


def sync_account(account_id):
    db = get_db()
    row = db.execute("""
        SELECT balance, sync_block 
        FROM accounts 
        WHERE account_id=?;
        """, (account_id,),
    ).fetchone()
    balance, sync_block = row
    offset = 0
    total_value_change = 0
    largest_block_height = 0
    call_api = True

    while call_api:

        address = blockexplorer.get_address(
            account_id, 
            limit=100, 
            offset=offset
        )

        if len(address.transactions) == 0:
            break
        
        largest_block_height = max(
            largest_block_height, 
            address.transactions[0].block_height
        )

        for tx in address.transactions:
            # Only sync up to the last sync'd block.
            if tx.block_height <= sync_block:
                call_api = False
                break

            amount_in = 0

            for input in tx.inputs:
                if input.address == account_id:
                    amount_in += input.value

            amount_out = 0

            for output in tx.outputs:
                if output.address == account_id:
                    amount_out += output.value

            value_change = amount_out - amount_in
            total_value_change += value_change

            try:
                db.execute("""
                    INSERT INTO transactions 
                    (tx_id, account_id, value_change, block_num) 
                    VALUES (?, ?, ?, ?);
                    """, (tx.hash, account_id, value_change, tx.block_height)
                )
                db.commit()
            except Exception as e:
                #Internal server error.
                abort(500, e)

            offset += 1


    new_balance = balance + total_value_change
    db.execute("""
        UPDATE accounts 
        SET balance=?, sync_block=? 
        WHERE account_id = ?;
        """, (new_balance, largest_block_height, account_id,)
    )
    db.commit()
