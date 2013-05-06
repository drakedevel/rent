def format_cents(what, cents):
    return "$%d.%02d" % (cents // 100, cents % 100)
