import rent.main as r
from collections import defaultdict
from rent.model import RentModel
from rent.ui_methods import format_cents

import sys

r.script()

def debt_message(person, amount):
    if amount > 0:
        say = "%s more than" % (format_cents(None, amount))
    elif amount == 0:
        say = 'just'
    else:
        say = "%s less than" % (format_cents(None, -amount))
    msg = '''\
To: %s
Subject: End-of-month rent is due

You should pay %s your regular rent.
''' % (person, say)
    return msg


def determine_debts(session):
    #TODO(rpearl) ...actual arg parsing
    dry_run = len(sys.argv) == 2 and sys.argv[1] == '--dry-run'

    if dry_run:
        print "This is a dry run. Not sending messages."

    debts = r.model.get_unresolved_transactions(session)
    users = [u.username for u in r.model.get_users(session)]

    rent = dict( (user, 0) for user in users )

    for debt in debts:
        rent[debt.to_user]   -= debt.amount
        rent[debt.from_user] += debt.amount

    total_debts = 0

    for person, amount in rent.iteritems():
        total_debts += amount
        msg = debt_message(person, amount)
        if not dry_run:
            r.model.send_mail(from_user='rent', to_user=person, message=msg)
        else:
            print msg

    if not dry_run:
        r.model.resolve_transactions(txns)

    assert total_debts == 0, "Something went wrong resolving debts..."

if __name__ == '__main__':
    with r.model.session() as session:
        determine_debts(session)
