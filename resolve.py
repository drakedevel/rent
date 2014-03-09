import sys
from collections import defaultdict

import rent.main as rent
from rent.model import User
from rent.ui_methods import format_cents

rent.script()
model = rent.model

THRESHOLD = 10000

def debt_message(person, txns):
    bullets = '\n'.join('    - %s to %s' % (format_cents(None, a), d) for d, a in txns)
    msg = '''\
To: %s
Subject: Rent rebalance required

You should pay the following:
%s
''' % (person, bullets)
    return msg

def determine_debts(session):
    #TODO(rpearl) ...actual arg parsing
    dry_run = len(sys.argv) == 2 and sys.argv[1] == '--dry-run'

    if dry_run:
        print "This is a dry run. Not sending messages."

    # Compute aggregate debt
    debts = model.get_unresolved_transactions(session)
    users = [u.username for u in model.get_users(session)]
    rent = {user: 0 for user in users}
    for debt in debts:
        rent[debt.to_user]   -= debt.amount
        rent[debt.from_user] += debt.amount
    assert sum(rent.values()) == 0

    # Find users who have properties of Shakespeare
    need_paid = []
    can_pay = []
    for u, r in rent.iteritems():
        if r <= -THRESHOLD:
            need_paid.append((r, u))
        elif r > 0:
            can_pay.append((-r, u))

    # Begin paying users to zero
    can_pay = [u for _, u in sorted(can_pay)]
    payments = defaultdict(list)
    for _, u in sorted(need_paid):
        print "Finding money for %s (need %s)" % (u, format_cents(None, rent[u]))
        for u2 in can_pay:
            if rent[u2] > 0:
                to_pay = min(rent[u2], -rent[u])
                rent[u2] -= to_pay
                rent[u] += to_pay
                payments[u2].append((u, to_pay))
            if rent[u] >= 0:
                break
        assert rent[u] == 0

    # Inform users of their debts and reconcile ledger
    for f, txns in payments.iteritems():
        fu = session.query(User).get(f)
        for t, amount in txns:
            tu = session.query(User).get(t)
            print "%s pays %s %s" % (f, t, format_cents(None, amount))
            if not dry_run:
                model.create_transaction(session, t, f, amount, '[automatic] resolving debt')

        msg = debt_message(f, txns)
        if not dry_run:
            model.send_mail(from_user='rent', to_user=f, message=msg)
        else:
            print msg

    # FIXME(adrake): Resolve transactions ever

if __name__ == '__main__':
    with model.session() as session:
        determine_debts(session)
