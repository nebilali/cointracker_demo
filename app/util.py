from flask import abort
from absl import logging

def validate_account_id(account_id):
    return True


def validate_or_abort(account_ids):
    for account_id in account_ids:
        if not validate_account_id(account_id):
            message = "Invalid account_id: {}, from input: {}".format(account_id, unparsed_account_ids)
            logging.error(error_msg)
            abort(400, message)